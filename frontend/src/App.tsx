// SPA del bibliotecario: libros (A), socios y préstamos (B). La composición A+B ocurre solo aquí.
import type React from "react";
import { type FormEvent, useCallback, useEffect, useState } from "react";
import { api, ApiError, type Book, isValidIsbn13, type Loan, type Member, type Page } from "./api";

type Tab = "libros" | "socios" | "prestamos";
const css = `
body{font-family:system-ui,sans-serif;margin:0;background:#f6f7f9;color:#1d2330}
header{background:#1f3a5f;color:#fff;padding:12px 24px;display:flex;gap:16px;align-items:center}
header button{background:none;border:0;color:#cfe0ff;font-size:16px;cursor:pointer;padding:6px 10px}
header button[aria-current=page]{color:#fff;border-bottom:2px solid #fff}
main{max-width:1000px;margin:24px auto;padding:0 16px}
form{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0;background:#fff;padding:12px;border-radius:8px}
input,select{padding:6px 8px;border:1px solid #c9ced8;border-radius:4px}
button.p{background:#1f3a5f;color:#fff;border:0;border-radius:4px;padding:6px 12px;cursor:pointer}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:8px}
th,td{padding:8px;border-bottom:1px solid #eceef2;text-align:left}
.err{background:#fde8e8;color:#8a1c1c;padding:8px 12px;border-radius:6px;margin:8px 0}
.ok{background:#e6f6ea;color:#1c6b33;padding:8px 12px;border-radius:6px;margin:8px 0}
.overdue{color:#b42318;font-weight:600}`;

function useAsync<T>(load: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const reload = useCallback(() => {
    setError(null);
    load().then(setData, (e: unknown) => setError(e instanceof Error ? e.message : String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(reload, [reload]);
  return { data, error, reload };
}

function Banner({ error, onRetry }: { error: string | null; onRetry?: () => void }) {
  if (!error) return null;
  return (
    <div className="err" role="alert">
      {error} {onRetry && <button onClick={onRetry}>Reintentar</button>}
    </div>
  );
}

function Books() {
  const [q, setQ] = useState("");
  const [offset, setOffset] = useState(0);
  const [term, setTerm] = useState("");
  useEffect(() => {
    const t = setTimeout(() => {
      setTerm(q);
      setOffset(0);
    }, 300);
    return () => clearTimeout(t);
  }, [q]);
  const { data, error, reload } = useAsync(() => api.books(term, offset), [term, offset]);
  const [msg, setMsg] = useState<string | null>(null);
  const [formErr, setFormErr] = useState<string | null>(null);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const isbn = String(f.get("isbn"));
    if (!isValidIsbn13(isbn)) return setFormErr("ISBN-13 inválido (revisa el dígito de control)");
    const year = String(f.get("published_year") || "");
    try {
      await api.createBook({
        isbn,
        title: f.get("title"),
        author: f.get("author"),
        published_year: year ? Number(year) : null,
        genre: f.get("genre") || null,
      });
      setFormErr(null);
      setMsg("Libro guardado");
      e.currentTarget?.reset();
      reload();
    } catch (err) {
      setFormErr((err as ApiError).message);
    }
  }
  async function remove(b: Book) {
    if (!confirm(`¿Eliminar "${b.title}"?`)) return;
    await api.deleteBook(b.id).catch((err: ApiError) => setFormErr(err.message));
    reload();
  }
  return (
    <section>
      <h2>Catálogo</h2>
      <form onSubmit={submit} aria-label="Nuevo libro">
        <input name="isbn" placeholder="ISBN-13" aria-label="ISBN" required />
        <input name="title" placeholder="Título" aria-label="Título" required maxLength={255} />
        <input name="author" placeholder="Autor" aria-label="Autor" required maxLength={255} />
        <input name="published_year" type="number" min={1450} max={new Date().getFullYear()} placeholder="Año" aria-label="Año" />
        <input name="genre" placeholder="Género" aria-label="Género" maxLength={64} />
        <button className="p">Guardar</button>
      </form>
      {msg && <div className="ok">{msg}</div>}
      <Banner error={formErr} />
      <input placeholder="Buscar por título o autor" aria-label="Buscar" value={q} onChange={(e) => setQ(e.target.value)} />
      <Banner error={error} onRetry={reload} />
      <List page={data} empty="No hay libros" offset={offset} setOffset={setOffset}>
        {(b: Book) => (
          <tr key={b.id}>
            <td>{b.title}</td>
            <td>{b.author}</td>
            <td>{b.published_year ?? "—"}</td>
            <td>{b.isbn}</td>
            <td>
              <button onClick={() => remove(b)}>Eliminar</button>
            </td>
          </tr>
        )}
      </List>
    </section>
  );
}

function List<T>(props: {
  page: Page<T> | null;
  empty: string;
  children: (x: T) => React.ReactElement;
  offset?: number;
  setOffset?: (n: number) => void;
}) {
  const { page, empty, children, offset = 0, setOffset } = props;
  if (!page) return <p>Cargando…</p>;
  if (!page.items.length) return <p>{empty}</p>;
  return (
    <>
      <table>
        <tbody>{page.items.map(children)}</tbody>
      </table>
      {setOffset && (
        <p>
          <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 20))}>
            Anterior
          </button>{" "}
          {offset + 1}–{offset + page.items.length} de {page.total}{" "}
          <button disabled={offset + page.items.length >= page.total} onClick={() => setOffset(offset + 20)}>
            Siguiente
          </button>
        </p>
      )}
    </>
  );
}

function Members() {
  const [status, setStatus] = useState("");
  const { data, error, reload } = useAsync(() => api.members("", status), [status]);
  const [err, setErr] = useState<string | null>(null);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    try {
      await api.createMember({ full_name: f.get("full_name"), email: f.get("email"), phone: f.get("phone") || null });
      setErr(null);
      e.currentTarget?.reset();
      reload();
    } catch (x) {
      setErr((x as ApiError).message);
    }
  }
  const act = (p: Promise<unknown>) => p.then(() => (setErr(null), reload()), (x: ApiError) => setErr(x.message));
  return (
    <section>
      <h2>Socios</h2>
      <form onSubmit={submit} aria-label="Nuevo socio">
        <input name="full_name" placeholder="Nombre completo" aria-label="Nombre" required maxLength={120} />
        <input name="email" type="email" placeholder="Email" aria-label="Email" required />
        <input name="phone" placeholder="Teléfono" aria-label="Teléfono" />
        <button className="p">Inscribir</button>
      </form>
      <Banner error={err} />
      <select aria-label="Estado" value={status} onChange={(e) => setStatus(e.target.value)}>
        <option value="">Todos</option>
        <option value="active">Activos</option>
        <option value="suspended">Suspendidos</option>
      </select>
      <Banner error={error} onRetry={reload} />
      <List page={data} empty="No hay socios">
        {(m: Member) => (
          <tr key={m.id}>
            <td>{m.full_name}</td>
            <td>{m.email}</td>
            <td>{m.status === "active" ? "Activo" : "Suspendido"}</td>
            <td>{m.active_loans} préstamo(s)</td>
            <td>
              <button
                onClick={() =>
                  act(
                    api.replaceMember(m.id, {
                      full_name: m.full_name,
                      email: m.email,
                      phone: null,
                      status: m.status === "active" ? "suspended" : "active",
                    }),
                  )
                }
              >
                {m.status === "active" ? "Suspender" : "Reactivar"}
              </button>{" "}
              <button onClick={() => confirm(`¿Eliminar a ${m.full_name}?`) && act(api.deleteMember(m.id))}>Eliminar</button>
            </td>
          </tr>
        )}
      </List>
    </section>
  );
}

function Loans() {
  const [status, setStatus] = useState("");
  const { data, error, reload } = useAsync(() => api.loans(status), [status]);
  const members = useAsync(() => api.members("", "active"), []);
  const books = useAsync(() => api.books(), []);
  const [titles, setTitles] = useState<Record<string, string>>({});
  const [err, setErr] = useState<string | null>(null);
  const names = Object.fromEntries((members.data?.items ?? []).map((m) => [m.id, m.full_name]));

  // REQ-F-006: título resuelto desde A (con degradación si A falla o el libro no existe)
  useEffect(() => {
    for (const l of data?.items ?? []) {
      if (titles[l.book_id]) continue;
      api.book(l.book_id).then(
        (b) => setTitles((t) => ({ ...t, [l.book_id]: b.title })),
        (e: ApiError) => setTitles((t) => ({ ...t, [l.book_id]: e.problem.status === 404 ? "Libro no disponible" : "—" })),
      );
    }
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    try {
      await api.createLoan({ member_id: f.get("member_id"), book_id: f.get("book_id"), ...(f.get("due_date") ? { due_date: f.get("due_date") } : {}) });
      setErr(null);
      reload();
      members.reload();
    } catch (x) {
      setErr((x as ApiError).message);
    }
  }
  return (
    <section>
      <h2>Préstamos</h2>
      <form onSubmit={submit} aria-label="Nuevo préstamo">
        <select name="member_id" aria-label="Socio" required>
          <option value="">Socio…</option>
          {members.data?.items.map((m) => (
            <option key={m.id} value={m.id}>
              {m.full_name}
            </option>
          ))}
        </select>
        <select name="book_id" aria-label="Libro" required>
          <option value="">Libro…</option>
          {books.data?.items.map((b) => (
            <option key={b.id} value={b.id}>
              {b.title}
            </option>
          ))}
        </select>
        <input name="due_date" type="date" aria-label="Fecha de devolución" />
        <button className="p">Prestar</button>
      </form>
      <Banner error={err} />
      <select aria-label="Estado del préstamo" value={status} onChange={(e) => setStatus(e.target.value)}>
        <option value="">Todos</option>
        <option value="active">Activos</option>
        <option value="overdue">Vencidos</option>
        <option value="returned">Devueltos</option>
      </select>
      <Banner error={error} onRetry={reload} />
      <List page={data} empty="No hay préstamos">
        {(l: Loan) => (
          <tr key={l.id}>
            <td>{titles[l.book_id] ?? "…"}</td>
            <td>{names[l.member_id] ?? l.member_id.slice(0, 8)}</td>
            <td className={l.status === "overdue" ? "overdue" : ""}>
              {l.status === "returned" ? "Devuelto" : l.status === "overdue" ? "Vencido" : "Activo"}
            </td>
            <td>vence {l.due_date}</td>
            <td>
              {l.status !== "returned" && (
                <button onClick={() => api.returnLoan(l.id).then(reload, (x: ApiError) => setErr(x.message))}>
                  Registrar devolución
                </button>
              )}
            </td>
          </tr>
        )}
      </List>
    </section>
  );
}

export function App() {
  const [tab, setTab] = useState<Tab>((location.hash.slice(1) as Tab) || "libros");
  useEffect(() => {
    location.hash = tab;
  }, [tab]);
  return (
    <>
      <style>{css}</style>
      <header>
        <strong>📚 Biblioteca</strong>
        {(["libros", "socios", "prestamos"] as Tab[]).map((t) => (
          <button key={t} aria-current={tab === t ? "page" : undefined} onClick={() => setTab(t)}>
            {t === "prestamos" ? "Préstamos" : t[0].toUpperCase() + t.slice(1)}
          </button>
        ))}
      </header>
      <main>{tab === "libros" ? <Books /> : tab === "socios" ? <Members /> : <Loans />}</main>
    </>
  );
}
