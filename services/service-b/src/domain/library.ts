// Casos de uso de socios y préstamos (REQ-B-001…012).
import { randomUUID } from "node:crypto";
import {
  addDays,
  DomainError,
  isoDate,
  type Loan,
  type Member,
  type MemberStatus,
  notFound,
} from "./model.js";
import type { Clock, LoanQuery, LoanRepository, MemberQuery, MemberRepository } from "./ports.js";

export interface MemberInput {
  full_name: string;
  email: string;
  phone?: string | null;
  status?: MemberStatus;
}

export interface LoanInput {
  member_id: string;
  book_id: string;
  due_date?: string;
}

export interface Rules {
  maxActiveLoans: number;
  defaultLoanDays: number;
}

export class Library {
  constructor(
    private readonly members: MemberRepository,
    private readonly loans: LoanRepository,
    private readonly clock: Clock,
    private readonly rules: Rules,
  ) {}

  today(): string {
    return isoDate(this.clock.now());
  }

  async createMember(input: MemberInput): Promise<Member> {
    const now = this.clock.now();
    const m: Member = {
      id: randomUUID(),
      full_name: input.full_name,
      email: input.email,
      phone: input.phone ?? null,
      status: "active",
      created_at: now,
      updated_at: now,
    };
    await this.members.insert(m);
    return m;
  }

  async getMember(id: string): Promise<Member> {
    const m = await this.members.get(id);
    if (!m) throw notFound("Member", id);
    return m;
  }

  activeLoans(id: string): Promise<number> {
    return this.loans.countOpen(id);
  }

  listMembers(q: MemberQuery) {
    return this.members.list(q);
  }

  async replaceMember(id: string, input: Required<MemberInput>): Promise<Member> {
    const old = await this.getMember(id);
    const m: Member = { ...old, ...input, updated_at: this.clock.now() };
    await this.members.replace(m);
    return m;
  }

  async deleteMember(id: string): Promise<void> {
    await this.getMember(id);
    if ((await this.loans.countOpen(id)) > 0) {
      throw new DomainError(409, "member-has-active-loans", `Member ${id} has active loans`);
    }
    await this.loans.deleteByMember(id);
    await this.members.delete(id);
  }

  async createLoan(input: LoanInput): Promise<Loan> {
    const member = await this.members.get(input.member_id);
    if (!member) throw new DomainError(422, "member-not-found", `Member ${input.member_id} does not exist`);
    if (member.status !== "active") {
      throw new DomainError(409, "member-not-eligible", `Member ${member.id} is ${member.status}`);
    }
    const today = this.today();
    const due = input.due_date ?? addDays(today, this.rules.defaultLoanDays);
    if (due <= today || due > addDays(today, 90)) {
      throw new DomainError(422, "validation-error", "due_date must be after today and within 90 days");
    }
    if ((await this.loans.countOpen(member.id)) >= this.rules.maxActiveLoans) {
      throw new DomainError(
        409,
        "loan-limit-reached",
        `Member already has ${this.rules.maxActiveLoans} active loans`,
      );
    }
    if (await this.loans.hasOpen(member.id, input.book_id)) {
      throw new DomainError(409, "duplicate-active-loan", "Member already has this book on loan");
    }
    const loan: Loan = {
      id: randomUUID(),
      member_id: member.id,
      book_id: input.book_id,
      loaned_at: this.clock.now(),
      due_date: due,
      returned_at: null,
    };
    await this.loans.insert(loan);
    return loan;
  }

  async getLoan(id: string): Promise<Loan> {
    const l = await this.loans.get(id);
    if (!l) throw notFound("Loan", id);
    return l;
  }

  listLoans(q: Omit<LoanQuery, "today">) {
    return this.loans.list({ ...q, today: this.today() });
  }

  async returnLoan(id: string): Promise<Loan> {
    const loan = await this.getLoan(id);
    if (loan.returned_at) throw new DomainError(409, "loan-already-returned", `Loan ${id} already returned`);
    const at = this.clock.now();
    await this.loans.markReturned(id, at);
    return { ...loan, returned_at: at };
  }
}
