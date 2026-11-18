// Contrato: las respuestas reales se validan contra specs/002-servicio-b/contracts/openapi.yaml.
import { randomUUID } from "node:crypto";
import SwaggerParser from "@apidevtools/swagger-parser";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import request from "supertest";
import { beforeAll, describe, expect, it } from "vitest";
import { createApp } from "../../src/api/app.js";
import { Library } from "../../src/domain/library.js";
import { makeLogger } from "../../src/logger.js";
import { FakeClock, FakeLoans, FakeMembers } from "../unit/fakes.js";

/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-require-imports */
const require = createRequire(import.meta.url);
const Ajv = require("ajv").default;
const addFormats = require("ajv-formats").default;
let spec: any;
const ajv = new Ajv({ strict: false, allErrors: true });
addFormats(ajv);
const lib = new Library(new FakeMembers(), new FakeLoans(), new FakeClock(), {
  maxActiveLoans: 3,
  defaultLoanDays: 14,
});
const app = createApp(lib, makeLogger("silent"), async () => true);

beforeAll(async () => {
  spec = await SwaggerParser.dereference(
    fileURLToPath(new URL("../../../../specs/002-servicio-b/contracts/openapi.yaml", import.meta.url)),
  );
});

function check(path: string, method: string, res: request.Response) {
  const op = spec.paths[path][method];
  const r = op.responses[String(res.status)];
  expect(r, `${method.toUpperCase()} ${path} ${res.status} no está en el contrato`).toBeTruthy();
  if (res.status === 204) return;
  const [ct, media] = Object.entries(r.content)[0] as [string, { schema: object }];
  expect(res.headers["content-type"]).toContain(ct);
  const ok = ajv.validate(media.schema, res.body);
  expect(ok, JSON.stringify(ajv.errors)).toBe(true);
}

describe("contrato OpenAPI de B", () => {
  it("[REQ-B-013] [REQ-B-014] health", async () => {
    check("/health/live", "get", await request(app).get("/health/live"));
    check("/health/ready", "get", await request(app).get("/health/ready"));
  });

  it("[REQ-B-001] [REQ-B-002] [REQ-B-003] [REQ-B-004] [REQ-B-005] socios", async () => {
    const c = await request(app).post("/members").send({ full_name: "Ana", email: "ana@x.com" });
    check("/members", "post", c);
    check(
      "/members",
      "post",
      await request(app).post("/members").send({ full_name: "Ana", email: "ana@x.com" }),
    );
    check("/members", "post", await request(app).post("/members").send({ email: "bad" }));
    check("/members", "get", await request(app).get("/members"));
    check("/members/{memberId}", "get", await request(app).get(`/members/${c.body.id}`));
    check("/members/{memberId}", "get", await request(app).get(`/members/${randomUUID()}`));
    check(
      "/members/{memberId}",
      "put",
      await request(app)
        .put(`/members/${c.body.id}`)
        .send({ full_name: "Ana", email: "ana@x.com", phone: null, status: "active" }),
    );
    const m2 = await request(app).post("/members").send({ full_name: "Bea", email: "bea@x.com" });
    check("/members/{memberId}", "delete", await request(app).delete(`/members/${m2.body.id}`));
  });

  it("[REQ-B-008] [REQ-B-009] [REQ-B-010] [REQ-B-011] préstamos", async () => {
    const m = await request(app).post("/members").send({ full_name: "Caro", email: "caro@x.com" });
    const l = await request(app).post("/loans").send({ member_id: m.body.id, book_id: randomUUID() });
    check("/loans", "post", l);
    check("/loans", "get", await request(app).get("/loans"));
    check("/loans/{loanId}", "get", await request(app).get(`/loans/${l.body.id}`));
    check("/loans/{loanId}/return", "post", await request(app).post(`/loans/${l.body.id}/return`));
    check("/loans/{loanId}/return", "post", await request(app).post(`/loans/${l.body.id}/return`));
  });
});
