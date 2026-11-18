// Cliente HTTP: rutas relativas (REQ-F-009) y errores problem+json (REQ-F-007).
export interface Problem {
  type?: string;
  title?: string;
  status: number;
  detail?: string;
  errors?: { field: string; message: string }[];
}

export class ApiError extends Error {
  constructor(readonly problem: Problem) {
    super(problemMessage(problem));
  }
}

const MESSAGES: Record<string, string> = {
  "/problems/duplicate-isbn": "Ya existe un libro con ese ISBN",
  "/problems/duplicate-email": "Ya existe un socio con ese email",
  "/problems/loan-limit-reached": "El socio alcanzó el máximo de préstamos activos",
  "/problems/member-not-eligible": "El socio está suspendido",
  "/problems/member-has-active-loans": "El socio tiene préstamos activos",
  "/problems/duplicate-active-loan": "El socio ya tiene ese libro prestado",
  "/problems/loan-already-returned": "El préstamo ya fue devuelto",
};

export function problemMessage(p: Problem): string {
  if (p.type && MESSAGES[p.type]) return MESSAGES[p.type];
  if (p.errors?.length) return p.errors.map((e) => `${e.field.replace(/^body\./, "")}: ${e.message}`).join("; ");
  if (p.status >= 500) return "Servicio no disponible, reintenta";
  return p.detail ?? p.title ?? `Error ${p.status}`;
}

export async function http<T>(path: string, init: RequestInit = {}, fetcher: typeof fetch = fetch): Promise<T> {
  let res: Response;
  try {
    res = await fetcher(path, { ...init, headers: { "Content-Type": "application/json", ...init.headers } });
  } catch {
    throw new ApiError({ status: 0, detail: "Servicio no disponible, reintenta" });
  }
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError({ status: res.status, ...body });
  return body as T;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
export interface Book {
  id: string;
  isbn: string;
  title: string;
  author: string;
  published_year: number | null;
  genre: string | null;
}
export interface Member {
  id: string;
  full_name: string;
  email: string;
  status: "active" | "suspended";
  active_loans: number;
}
export interface Loan {
  id: string;
  member_id: string;
  book_id: string;
  due_date: string;
  returned_at: string | null;
  status: "active" | "returned" | "overdue";
}

const json = (b: unknown) => JSON.stringify(b);
export const A = "/api/a";
export const B = "/api/b";
export const api = {
  books: (q = "", offset = 0) => http<Page<Book>>(`${A}/books?limit=20&offset=${offset}${q ? `&q=${encodeURIComponent(q)}` : ""}`),
  book: (id: string) => http<Book>(`${A}/books/${id}`),
  createBook: (b: object) => http<Book>(`${A}/books`, { method: "POST", body: json(b) }),
  deleteBook: (id: string) => http<void>(`${A}/books/${id}`, { method: "DELETE" }),
  members: (q = "", status = "") =>
    http<Page<Member>>(`${B}/members?limit=100${q ? `&q=${encodeURIComponent(q)}` : ""}${status ? `&status=${status}` : ""}`),
  createMember: (m: object) => http<Member>(`${B}/members`, { method: "POST", body: json(m) }),
  replaceMember: (id: string, m: object) => http<Member>(`${B}/members/${id}`, { method: "PUT", body: json(m) }),
  deleteMember: (id: string) => http<void>(`${B}/members/${id}`, { method: "DELETE" }),
  loans: (status = "") => http<Page<Loan>>(`${B}/loans?limit=100${status ? `&status=${status}` : ""}`),
  createLoan: (l: object) => http<Loan>(`${B}/loans`, { method: "POST", body: json(l) }),
  returnLoan: (id: string) => http<Loan>(`${B}/loans/${id}/return`, { method: "POST" }),
};

/** REQ-F-002: validación de ISBN-13 en cliente, espejo del contrato. */
export function isValidIsbn13(raw: string): boolean {
  const s = raw.replace(/[\s-]/g, "");
  if (!/^97[89]\d{10}$/.test(s)) return false;
  const sum = [...s.slice(0, 12)].reduce((acc, d, i) => acc + Number(d) * (i % 2 ? 3 : 1), 0);
  return (10 - (sum % 10)) % 10 === Number(s[12]);
}
