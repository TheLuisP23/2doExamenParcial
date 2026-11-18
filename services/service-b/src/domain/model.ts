// Dominio: entidades, reglas y errores. No importa express ni mongodb.
export type MemberStatus = "active" | "suspended";
export type LoanStatus = "active" | "returned" | "overdue";

export interface Member {
  id: string;
  full_name: string;
  email: string;
  phone: string | null;
  status: MemberStatus;
  created_at: Date;
  updated_at: Date;
}

export interface Loan {
  id: string;
  member_id: string;
  book_id: string;
  loaned_at: Date;
  due_date: string; // YYYY-MM-DD
  returned_at: Date | null;
}

export class DomainError extends Error {
  constructor(
    readonly status: number,
    readonly slug: string,
    message: string,
  ) {
    super(message);
  }
}

export const notFound = (what: string, id: string) =>
  new DomainError(404, "not-found", `${what} ${id} not found`);

export function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function addDays(day: string, days: number): string {
  const d = new Date(`${day}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return isoDate(d);
}

/** REQ-B-012: estado derivado, no persistido. */
export function loanStatus(loan: Loan, today: string): LoanStatus {
  if (loan.returned_at) return "returned";
  return loan.due_date < today ? "overdue" : "active";
}
