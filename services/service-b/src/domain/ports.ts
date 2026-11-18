import type { Loan, LoanStatus, Member, MemberStatus } from "./model.js";

export interface Page<T> {
  items: T[];
  total: number;
}

export interface MemberQuery {
  status?: MemberStatus;
  q?: string;
  limit: number;
  offset: number;
}

export interface LoanQuery {
  member_id?: string;
  book_id?: string;
  status?: LoanStatus;
  today: string;
  limit: number;
  offset: number;
}

export interface MemberRepository {
  /** Lanza DomainError duplicate-email si el email ya existe. */
  insert(m: Member): Promise<void>;
  get(id: string): Promise<Member | null>;
  list(q: MemberQuery): Promise<Page<Member>>;
  replace(m: Member): Promise<void>;
  delete(id: string): Promise<void>;
}

export interface LoanRepository {
  insert(l: Loan): Promise<void>;
  get(id: string): Promise<Loan | null>;
  list(q: LoanQuery): Promise<Page<Loan>>;
  countOpen(memberId: string): Promise<number>;
  hasOpen(memberId: string, bookId: string): Promise<boolean>;
  markReturned(id: string, at: Date): Promise<void>;
  deleteByMember(memberId: string): Promise<void>;
}

export interface Clock {
  now(): Date;
}
