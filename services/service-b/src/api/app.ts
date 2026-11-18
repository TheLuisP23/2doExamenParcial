// Capa API: rutas HTTP, validación zod y errores problem+json (REQ-SYS-006).
import express, { type NextFunction, type Request, type Response } from "express";
import type { Logger } from "pino";
import { z, ZodError } from "zod";
import type { Library } from "../domain/library.js";
import { DomainError, type Loan, loanStatus, type Member } from "../domain/model.js";
import { requestLogger } from "../logger.js";

const PHONE = /^\+?[0-9 ()-]{7,20}$/;
const uuid = z.string().uuid();
const name = z.string().trim().min(1).max(120);
const email = z
  .string()
  .trim()
  .max(254)
  .email()
  .transform((s) => s.toLowerCase());
const phone = z.string().regex(PHONE).nullable();
const memberStatus = z.enum(["active", "suspended"]);
const page = {
  limit: z.coerce.number().int().min(1).max(100).default(20),
  offset: z.coerce.number().int().min(0).default(0),
};

const MemberCreate = z.object({ full_name: name, email, phone: phone.optional() }).strict();
const MemberReplace = z.object({ full_name: name, email, phone, status: memberStatus }).strict();
const MemberList = z.object({
  ...page,
  status: memberStatus.optional(),
  q: z.string().min(1).max(100).optional(),
});
const LoanCreate = z
  .object({ member_id: uuid, book_id: uuid, due_date: z.string().date().optional() })
  .strict();
const LoanList = z.object({
  ...page,
  member_id: uuid.optional(),
  book_id: uuid.optional(),
  status: z.enum(["active", "returned", "overdue"]).optional(),
});

class InputError extends Error {
  constructor(
    readonly where: string,
    readonly zod: ZodError,
  ) {
    super("validation");
  }
}

function parse<T extends z.ZodTypeAny>(schema: T, data: unknown, where: string): z.infer<T> {
  const r = schema.safeParse(data);
  if (!r.success) throw new InputError(where, r.error);
  return r.data;
}

function problem(res: Response, status: number, slug: string, detail: string, extra: object = {}) {
  const titles: Record<number, string> = { 404: "Not Found", 409: "Conflict", 422: "Unprocessable Content" };
  res
    .status(status)
    .type("application/problem+json")
    .send(
      JSON.stringify({
        type: `/problems/${slug}`,
        title: titles[status] ?? "Error",
        status,
        detail,
        ...extra,
      }),
    );
}

export function createApp(lib: Library, logger: Logger, ping: () => Promise<boolean>) {
  const app = express();
  app.disable("x-powered-by");
  app.use(requestLogger(logger));
  app.use(express.json());

  const memberOut = async (m: Member) => ({ ...m, active_loans: await lib.activeLoans(m.id) });
  const loanOut = (l: Loan) => ({ ...l, status: loanStatus(l, lib.today()) });
  const id = (req: Request) => parse(uuid, req.params.id, "path.id");

  app.get("/health/live", (_req, res) => {
    res.json({ status: "ok" });
  });
  app.get("/health/ready", async (_req, res) => {
    const ok = await ping().catch(() => false);
    res
      .status(ok ? 200 : 503)
      .json({ status: ok ? "ok" : "unavailable", checks: { database: ok ? "ok" : "error" } });
  });

  app.get("/members", async (req, res) => {
    const q = parse(MemberList, req.query, "query");
    const r = await lib.listMembers(q);
    res.json({
      items: await Promise.all(r.items.map(memberOut)),
      total: r.total,
      limit: q.limit,
      offset: q.offset,
    });
  });
  app.post("/members", async (req, res) => {
    const m = await lib.createMember(parse(MemberCreate, req.body, "body"));
    res
      .status(201)
      .location(`/members/${m.id}`)
      .json(await memberOut(m));
  });
  app.get("/members/:id", async (req, res) => {
    res.json(await memberOut(await lib.getMember(id(req))));
  });
  app.put("/members/:id", async (req, res) => {
    const memberId = id(req);
    res.json(await memberOut(await lib.replaceMember(memberId, parse(MemberReplace, req.body, "body"))));
  });
  app.delete("/members/:id", async (req, res) => {
    await lib.deleteMember(id(req));
    res.status(204).end();
  });

  app.get("/loans", async (req, res) => {
    const q = parse(LoanList, req.query, "query");
    const r = await lib.listLoans(q);
    res.json({ items: r.items.map(loanOut), total: r.total, limit: q.limit, offset: q.offset });
  });
  app.post("/loans", async (req, res) => {
    const l = await lib.createLoan(parse(LoanCreate, req.body, "body"));
    res.status(201).location(`/loans/${l.id}`).json(loanOut(l));
  });
  app.get("/loans/:id", async (req, res) => {
    res.json(loanOut(await lib.getLoan(id(req))));
  });
  app.post("/loans/:id/return", async (req, res) => {
    res.json(loanOut(await lib.returnLoan(id(req))));
  });

  app.use((_req, res) => problem(res, 404, "not-found", "Route not found"));

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  app.use((err: unknown, _req: Request, res: Response, _next: NextFunction) => {
    if (err instanceof InputError) {
      const errors = err.zod.issues.map((i) => ({
        field: [err.where, ...i.path].join("."),
        message: i.message,
      }));
      return problem(res, 422, "validation-error", "Request validation failed", { errors });
    }
    if (err instanceof DomainError) {
      const extra = err.status === 422 ? { errors: [{ field: "body", message: err.message }] } : {};
      return problem(res, err.status, err.slug, err.message, extra);
    }
    if (err instanceof SyntaxError) {
      return problem(res, 422, "validation-error", "Malformed JSON", {
        errors: [{ field: "body", message: "invalid JSON" }],
      });
    }
    logger.error({ err }, "unhandled error");
    return problem(res, 500, "internal", "Unexpected error");
  });
  return app;
}
