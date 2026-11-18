import { DomainError, type Loan, type Member } from "../../src/domain/model.js";
import type { LoanQuery, LoanRepository, MemberQuery, MemberRepository } from "../../src/domain/ports.js";

export class FakeMembers implements MemberRepository {
  rows = new Map<string, Member>();
  async insert(m: Member) {
    if ([...this.rows.values()].some((x) => x.email === m.email))
      throw new DomainError(409, "duplicate-email", "dup");
    this.rows.set(m.id, { ...m });
  }
  async get(id: string) {
    return this.rows.get(id) ?? null;
  }
  async list(q: MemberQuery) {
    let items = [...this.rows.values()];
    if (q.status) items = items.filter((m) => m.status === q.status);
    if (q.q)
      items = items.filter((m) => `${m.full_name} ${m.email}`.toLowerCase().includes(q.q!.toLowerCase()));
    return { items: items.slice(q.offset, q.offset + q.limit), total: items.length };
  }
  async replace(m: Member) {
    if ([...this.rows.values()].some((x) => x.email === m.email && x.id !== m.id))
      throw new DomainError(409, "duplicate-email", "dup");
    this.rows.set(m.id, { ...m });
  }
  async delete(id: string) {
    this.rows.delete(id);
  }
}

export class FakeLoans implements LoanRepository {
  rows = new Map<string, Loan>();
  async insert(l: Loan) {
    this.rows.set(l.id, { ...l });
  }
  async get(id: string) {
    return this.rows.get(id) ?? null;
  }
  async list(q: LoanQuery) {
    let items = [...this.rows.values()];
    if (q.member_id) items = items.filter((l) => l.member_id === q.member_id);
    if (q.book_id) items = items.filter((l) => l.book_id === q.book_id);
    if (q.status === "returned") items = items.filter((l) => l.returned_at);
    if (q.status === "active") items = items.filter((l) => !l.returned_at && l.due_date >= q.today);
    if (q.status === "overdue") items = items.filter((l) => !l.returned_at && l.due_date < q.today);
    return { items: items.slice(q.offset, q.offset + q.limit), total: items.length };
  }
  async countOpen(memberId: string) {
    return [...this.rows.values()].filter((l) => l.member_id === memberId && !l.returned_at).length;
  }
  async hasOpen(memberId: string, bookId: string) {
    return [...this.rows.values()].some(
      (l) => l.member_id === memberId && l.book_id === bookId && !l.returned_at,
    );
  }
  async markReturned(id: string, at: Date) {
    this.rows.get(id)!.returned_at = at;
  }
  async deleteByMember(memberId: string) {
    for (const [k, l] of this.rows) if (l.member_id === memberId) this.rows.delete(k);
  }
}

export class FakeClock {
  constructor(public current = new Date("2026-11-17T10:00:00Z")) {}
  now() {
    return new Date(this.current);
  }
}
