// Adaptadores MongoDB e índices al arranque (REQ-B-015).
import { type Collection, type Db, MongoClient, MongoServerError } from "mongodb";
import { DomainError, type Loan, type Member } from "../domain/model.js";
import type { LoanQuery, LoanRepository, MemberQuery, MemberRepository, Page } from "../domain/ports.js";

type Doc<T> = Omit<T, "id"> & { _id: string };
const toDoc = <T extends { id: string }>({ id, ...rest }: T) => ({ _id: id, ...rest }) as Doc<T>;
const fromDoc = <T>({ _id, ...rest }: Doc<T & { id: string }>) => ({ id: _id, ...rest }) as unknown as T;
const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export async function connect(uri: string, dbName: string, timeoutMs = 2000) {
  const client = new MongoClient(uri, { serverSelectionTimeoutMS: timeoutMs });
  await client.connect();
  return { client, db: client.db(dbName) };
}

export async function ensureIndexes(db: Db): Promise<void> {
  await db.collection("members").createIndexes([
    { key: { email: 1 }, name: "uq_members_email", unique: true },
    { key: { status: 1, created_at: -1, _id: 1 }, name: "ix_members_status_created" },
  ]);
  await db.collection("loans").createIndexes([
    { key: { member_id: 1, returned_at: 1 }, name: "ix_loans_member_open" },
    {
      key: { member_id: 1, book_id: 1 },
      name: "uq_loans_member_book_open",
      unique: true,
      partialFilterExpression: { returned_at: { $type: "null" } },
    },
    { key: { book_id: 1, loaned_at: -1 }, name: "ix_loans_book" },
    { key: { loaned_at: -1 }, name: "ix_loans_loaned_at" },
  ]);
}

export async function ping(db: Db): Promise<boolean> {
  try {
    return (await db.command({ ping: 1 })).ok === 1;
  } catch {
    return false;
  }
}

const isDup = (e: unknown) => e instanceof MongoServerError && e.code === 11000;

export class MongoMemberRepository implements MemberRepository {
  private readonly c: Collection<Doc<Member>>;
  constructor(db: Db) {
    this.c = db.collection<Doc<Member>>("members");
  }
  async insert(m: Member) {
    try {
      await this.c.insertOne(toDoc(m));
    } catch (e) {
      if (isDup(e))
        throw new DomainError(409, "duplicate-email", `A member with email ${m.email} already exists`);
      throw e;
    }
  }
  async get(id: string) {
    const d = await this.c.findOne({ _id: id });
    return d ? fromDoc<Member>(d) : null;
  }
  async list(q: MemberQuery): Promise<Page<Member>> {
    const f: Record<string, unknown> = {};
    if (q.status) f.status = q.status;
    if (q.q) {
      const re = new RegExp(escape(q.q), "i");
      f.$or = [{ full_name: re }, { email: re }];
    }
    const [docs, total] = await Promise.all([
      this.c.find(f).sort({ created_at: -1, _id: 1 }).skip(q.offset).limit(q.limit).toArray(),
      this.c.countDocuments(f),
    ]);
    return { items: docs.map((d) => fromDoc<Member>(d)), total };
  }
  async replace(m: Member) {
    try {
      await this.c.replaceOne({ _id: m.id }, toDoc(m));
    } catch (e) {
      if (isDup(e))
        throw new DomainError(409, "duplicate-email", `A member with email ${m.email} already exists`);
      throw e;
    }
  }
  async delete(id: string) {
    await this.c.deleteOne({ _id: id });
  }
}

export class MongoLoanRepository implements LoanRepository {
  private readonly c: Collection<Doc<Loan>>;
  constructor(db: Db) {
    this.c = db.collection<Doc<Loan>>("loans");
  }
  async insert(l: Loan) {
    try {
      await this.c.insertOne(toDoc(l));
    } catch (e) {
      if (isDup(e))
        throw new DomainError(409, "duplicate-active-loan", "Member already has this book on loan");
      throw e;
    }
  }
  async get(id: string) {
    const d = await this.c.findOne({ _id: id });
    return d ? fromDoc<Loan>(d) : null;
  }
  async list(q: LoanQuery): Promise<Page<Loan>> {
    const f: Record<string, unknown> = {};
    if (q.member_id) f.member_id = q.member_id;
    if (q.book_id) f.book_id = q.book_id;
    if (q.status === "returned") f.returned_at = { $ne: null };
    if (q.status === "active") Object.assign(f, { returned_at: null, due_date: { $gte: q.today } });
    if (q.status === "overdue") Object.assign(f, { returned_at: null, due_date: { $lt: q.today } });
    const [docs, total] = await Promise.all([
      this.c.find(f).sort({ loaned_at: -1, _id: 1 }).skip(q.offset).limit(q.limit).toArray(),
      this.c.countDocuments(f),
    ]);
    return { items: docs.map((d) => fromDoc<Loan>(d)), total };
  }
  countOpen(memberId: string) {
    return this.c.countDocuments({ member_id: memberId, returned_at: null });
  }
  async hasOpen(memberId: string, bookId: string) {
    return (await this.c.countDocuments({ member_id: memberId, book_id: bookId, returned_at: null })) > 0;
  }
  async markReturned(id: string, at: Date) {
    await this.c.updateOne({ _id: id }, { $set: { returned_at: at } });
  }
  async deleteByMember(memberId: string) {
    await this.c.deleteMany({ member_id: memberId });
  }
}
