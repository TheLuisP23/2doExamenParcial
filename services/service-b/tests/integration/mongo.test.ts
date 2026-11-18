import { randomUUID } from "node:crypto";
import { GenericContainer, type StartedTestContainer, Wait } from "testcontainers";
import type { Db, MongoClient } from "mongodb";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import {
  connect,
  ensureIndexes,
  MongoLoanRepository,
  MongoMemberRepository,
  ping,
} from "../../src/repository/mongo.js";

let container: StartedTestContainer;
let client: MongoClient;
let db: Db;

beforeAll(async () => {
  container = await new GenericContainer("mongo:7.0")
    .withExposedPorts(27017)
    .withWaitStrategy(Wait.forLogMessage(/Waiting for connections/))
    .start();
  ({ client, db } = await connect(
    `mongodb://${container.getHost()}:${container.getMappedPort(27017)}/?directConnection=true`,
    "members",
  ));
  await ensureIndexes(db);
});
afterAll(async () => {
  await client?.close();
  await container?.stop();
});

const member = (email = `${randomUUID()}@x.com`) => ({
  id: randomUUID(),
  full_name: "Ana",
  email,
  phone: null,
  status: "active" as const,
  created_at: new Date(),
  updated_at: new Date(),
});

describe("MongoDB real", () => {
  it("[REQ-B-015] crea índices idempotentes", async () => {
    await ensureIndexes(db);
    const names = (await db.collection("members").indexes()).map((i) => i.name);
    expect(names).toContain("uq_members_email");
    expect((await db.collection("loans").indexes()).map((i) => i.name)).toContain(
      "uq_loans_member_book_open",
    );
  });

  it("[REQ-B-014] ping a Mongo", async () => {
    expect(await ping(db)).toBe(true);
  });

  it("[REQ-B-001] [REQ-B-002] [REQ-B-003] [REQ-B-004] [REQ-B-006] repositorio de socios", async () => {
    const repo = new MongoMemberRepository(db);
    const m = member("unique@x.com");
    await repo.insert(m);
    expect((await repo.get(m.id))?.email).toBe("unique@x.com");
    await expect(repo.insert(member("unique@x.com"))).rejects.toMatchObject({ slug: "duplicate-email" });
    await repo.replace({ ...m, status: "suspended" });
    expect((await repo.list({ status: "suspended", limit: 10, offset: 0 })).total).toBe(1);
    expect((await repo.list({ q: "UNIQUE", limit: 10, offset: 0 })).total).toBe(1);
  });

  it("[REQ-B-005] [REQ-B-008] [REQ-B-009] [REQ-B-010] [REQ-B-011] repositorio de préstamos", async () => {
    const repo = new MongoLoanRepository(db);
    const memberId = randomUUID();
    const bookId = randomUUID();
    const l = {
      id: randomUUID(),
      member_id: memberId,
      book_id: bookId,
      loaned_at: new Date(),
      due_date: "2026-12-01",
      returned_at: null,
    };
    await repo.insert(l);
    await expect(repo.insert({ ...l, id: randomUUID() })).rejects.toMatchObject({
      slug: "duplicate-active-loan",
    });
    expect(await repo.countOpen(memberId)).toBe(1);
    expect(await repo.hasOpen(memberId, bookId)).toBe(true);
    expect(
      (await repo.list({ member_id: memberId, status: "active", today: "2026-11-17", limit: 10, offset: 0 }))
        .total,
    ).toBe(1);
    expect(
      (await repo.list({ status: "overdue", member_id: memberId, today: "2026-12-05", limit: 10, offset: 0 }))
        .total,
    ).toBe(1);
    await repo.markReturned(l.id, new Date());
    expect((await repo.get(l.id))?.returned_at).not.toBeNull();
    expect(
      (
        await repo.list({
          member_id: memberId,
          status: "returned",
          today: "2026-11-17",
          limit: 10,
          offset: 0,
        })
      ).total,
    ).toBe(1);
    await repo.deleteByMember(memberId);
    expect(await repo.get(l.id)).toBeNull();
  });
});
