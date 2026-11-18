import { randomUUID } from "node:crypto";
import { Writable } from "node:stream";
import request from "supertest";
import { beforeEach, describe, expect, it } from "vitest";
import { createApp } from "../../src/api/app.js";
import { loadConfig } from "../../src/config.js";
import { Library } from "../../src/domain/library.js";
import { makeLogger } from "../../src/logger.js";
import { FakeClock, FakeLoans, FakeMembers } from "./fakes.js";

const PROBLEM = /application\/problem\+json/;
let lines: string[];
let healthy: boolean;
let clock: FakeClock;
let app: ReturnType<typeof createApp>;

beforeEach(() => {
  lines = [];
  healthy = true;
  clock = new FakeClock();
  const sink = new Writable({
    write(chunk, _e, cb) {
      lines.push(String(chunk));
      cb();
    },
  });
  const lib = new Library(new FakeMembers(), new FakeLoans(), clock, {
    maxActiveLoans: 3,
    defaultLoanDays: 14,
  });
  app = createApp(lib, makeLogger("info", sink), async () => healthy);
});

const member = (over: object = {}) =>
  request(app)
    .post("/members")
    .send({ full_name: "Ana Pérez", email: "Ana@Example.com", ...over });
const loan = (member_id: string, book_id: string = randomUUID(), extra: object = {}) =>
  request(app)
    .post("/loans")
    .send({ member_id, book_id, ...extra });

describe("socios", () => {
  it("[REQ-B-001] crea socio activo con email normalizado y Location", async () => {
    const r = await member();
    expect(r.status).toBe(201);
    expect(r.body).toMatchObject({
      status: "active",
      email: "ana@example.com",
      phone: null,
      active_loans: 0,
    });
    expect(r.headers.location).toBe(`/members/${r.body.id}`);
  });

  it("[REQ-B-002] obtiene socio con active_loans; 404 y 422", async () => {
    const m = (await member()).body;
    await loan(m.id);
    expect((await request(app).get(`/members/${m.id}`)).body.active_loans).toBe(1);
    const nf = await request(app).get(`/members/${randomUUID()}`);
    expect(nf.status).toBe(404);
    expect(nf.headers["content-type"]).toMatch(PROBLEM);
    expect((await request(app).get("/members/xyz")).status).toBe(422);
  });

  it("[REQ-B-003] lista con filtro de estado, búsqueda y paginación", async () => {
    for (const e of ["a@x.com", "b@x.com", "c@x.com"]) await member({ email: e, full_name: e });
    const s = (await member({ email: "s@x.com", full_name: "Suspendido" })).body;
    await request(app)
      .put(`/members/${s.id}`)
      .send({ full_name: "Suspendido", email: "s@x.com", phone: null, status: "suspended" });
    const r = await request(app).get("/members?status=suspended");
    expect(r.body.total).toBe(1);
    expect((await request(app).get("/members?q=B@X")).body.total).toBe(1);
    expect((await request(app).get("/members?limit=2")).body.items).toHaveLength(2);
    expect((await request(app).get("/members?limit=500")).status).toBe(422);
  });

  it("[REQ-B-004] reemplaza y suspende; el suspendido no puede pedir préstamos", async () => {
    const m = (await member()).body;
    const r = await request(app)
      .put(`/members/${m.id}`)
      .send({ full_name: "Ana P.", email: "ana@example.com", phone: "+57 300 1234567", status: "suspended" });
    expect(r.status).toBe(200);
    expect(r.body.status).toBe("suspended");
    const l = await loan(m.id);
    expect(l.status).toBe(409);
    expect(l.body.type).toBe("/problems/member-not-eligible");
    expect(
      (
        await request(app)
          .put(`/members/${randomUUID()}`)
          .send({ full_name: "x", email: "x@x.com", phone: null, status: "active" })
      ).status,
    ).toBe(404);
  });

  it("[REQ-B-005] no borra con préstamos activos; borra si no tiene", async () => {
    const m = (await member()).body;
    const l = (await loan(m.id)).body;
    const r = await request(app).delete(`/members/${m.id}`);
    expect(r.status).toBe(409);
    expect(r.body.type).toBe("/problems/member-has-active-loans");
    await request(app).post(`/loans/${l.id}/return`);
    expect((await request(app).delete(`/members/${m.id}`)).status).toBe(204);
    expect((await request(app).get(`/members/${m.id}`)).status).toBe(404);
    expect((await request(app).get(`/loans/${l.id}`)).status).toBe(404);
  });

  it("[REQ-B-006] email único sin distinguir mayúsculas", async () => {
    await member();
    const r = await member({ email: "ANA@example.com" });
    expect(r.status).toBe(409);
    expect(r.body.type).toBe("/problems/duplicate-email");
  });

  it("[REQ-B-007] [REQ-SYS-006] validación en problem+json con errors[]", async () => {
    const r = await member({ email: "no-es-email" });
    expect(r.status).toBe(422);
    expect(r.headers["content-type"]).toMatch(PROBLEM);
    expect(r.body.errors.map((e: { field: string }) => e.field)).toContain("body.email");
    expect((await member({ foo: 1 })).status).toBe(422);
    expect((await member({ full_name: "  " })).status).toBe(422);
    expect((await member({ phone: "abc" })).status).toBe(422);
    expect(
      (await request(app).post("/members").set("content-type", "application/json").send("{")).status,
    ).toBe(422);
    expect((await request(app).get("/nope")).headers["content-type"]).toMatch(PROBLEM);
  });
});

describe("préstamos", () => {
  it("[REQ-B-008] crea préstamo con due_date por defecto y aplica reglas", async () => {
    const m = (await member()).body;
    const r = await loan(m.id);
    expect(r.status).toBe(201);
    expect(r.body).toMatchObject({ status: "active", due_date: "2026-12-01", returned_at: null });
    expect(r.headers.location).toBe(`/loans/${r.body.id}`);
    const dup = await loan(m.id, r.body.book_id);
    expect(dup.body.type).toBe("/problems/duplicate-active-loan");
    await loan(m.id);
    await loan(m.id);
    const over = await loan(m.id);
    expect(over.status).toBe(409);
    expect(over.body.type).toBe("/problems/loan-limit-reached");
    const ghost = await loan(randomUUID());
    expect(ghost.status).toBe(422);
    expect(ghost.body.type).toBe("/problems/member-not-found");
  });

  it("[REQ-B-008] valida due_date (> hoy y ≤ 90 días)", async () => {
    const m = (await member()).body;
    expect((await loan(m.id, randomUUID(), { due_date: "2026-11-17" })).status).toBe(422);
    expect((await loan(m.id, randomUUID(), { due_date: "2027-06-01" })).status).toBe(422);
    expect((await loan(m.id, randomUUID(), { due_date: "2026-11-20" })).body.due_date).toBe("2026-11-20");
    expect((await loan(m.id, "no-uuid")).status).toBe(422);
  });

  it("[REQ-B-009] [REQ-B-010] lista con filtros y obtiene por id", async () => {
    const a = (await member()).body;
    const b = (await member({ email: "b@x.com" })).body;
    const la = (await loan(a.id)).body;
    await loan(b.id);
    const r = await request(app).get(`/loans?member_id=${a.id}`);
    expect(r.body.total).toBe(1);
    expect((await request(app).get(`/loans?book_id=${la.book_id}`)).body.total).toBe(1);
    expect((await request(app).get(`/loans/${la.id}`)).body.id).toBe(la.id);
    expect((await request(app).get(`/loans/${randomUUID()}`)).status).toBe(404);
  });

  it("[REQ-B-011] devuelve una vez; la segunda da 409", async () => {
    const m = (await member()).body;
    const l = (await loan(m.id)).body;
    const r = await request(app).post(`/loans/${l.id}/return`);
    expect(r.status).toBe(200);
    expect(r.body.returned_at).not.toBeNull();
    expect(r.body.status).toBe("returned");
    expect((await request(app).post(`/loans/${l.id}/return`)).body.type).toBe(
      "/problems/loan-already-returned",
    );
    expect((await request(app).get("/loans?status=returned")).body.total).toBe(1);
  });

  it("[REQ-B-012] estado overdue derivado del reloj", async () => {
    const m = (await member()).body;
    const l = (await loan(m.id, randomUUID(), { due_date: "2026-11-18" })).body;
    clock.current = new Date("2026-11-19T09:00:00Z");
    expect((await request(app).get(`/loans/${l.id}`)).body.status).toBe("overdue");
    expect((await request(app).get("/loans?status=overdue")).body.total).toBe(1);
    expect((await request(app).get("/loans?status=active")).body.total).toBe(0);
  });
});

describe("operación", () => {
  it("[REQ-B-013] liveness no depende de Mongo", async () => {
    healthy = false;
    expect((await request(app).get("/health/live")).body).toEqual({ status: "ok" });
  });

  it("[REQ-B-014] readiness 200/503", async () => {
    expect((await request(app).get("/health/ready")).body).toEqual({
      status: "ok",
      checks: { database: "ok" },
    });
    healthy = false;
    const r = await request(app).get("/health/ready");
    expect(r.status).toBe(503);
    expect(r.body.checks.database).toBe("error");
  });

  it("[REQ-SYS-004] X-Request-ID propagado y log JSON con request_id", async () => {
    const r = await request(app).get("/health/live").set("X-Request-ID", "rid-7");
    expect(r.headers["x-request-id"]).toBe("rid-7");
    const log = JSON.parse(lines.at(-1)!);
    expect(log).toMatchObject({
      request_id: "rid-7",
      service: "service-b",
      level: "info",
      message: "request",
    });
    expect(log.timestamp).toBeTruthy();
  });

  it("[REQ-SYS-005] la configuración falla sin SERVICE_B_MONGO_URI", () => {
    expect(() => loadConfig({})).toThrow(/SERVICE_B_MONGO_URI/);
    expect(loadConfig({ SERVICE_B_MONGO_URI: "mongodb://x" })).toMatchObject({
      port: 3000,
      maxActiveLoans: 3,
    });
  });
});
