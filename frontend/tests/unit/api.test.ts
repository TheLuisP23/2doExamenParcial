import { describe, expect, it } from "vitest";
import { api, ApiError, http, isValidIsbn13, problemMessage } from "../../src/api";

const fake = (status: number, body: unknown) => async () => new Response(JSON.stringify(body), { status });

describe("cliente HTTP", () => {
  it("[REQ-F-007] traduce problem+json conocidos y de validación", async () => {
    await expect(http("/x", {}, fake(409, { type: "/problems/loan-limit-reached", status: 409 }))).rejects.toThrow(
      "El socio alcanzó el máximo de préstamos activos",
    );
    expect(problemMessage({ status: 422, errors: [{ field: "body.email", message: "inválido" }] })).toBe("email: inválido");
    expect(problemMessage({ status: 503 })).toBe("Servicio no disponible, reintenta");
  });

  it("[REQ-F-007] errores de red se convierten en ApiError status 0", async () => {
    const err = (await http("/x", {}, async () => Promise.reject(new TypeError("net"))).catch((e: unknown) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.problem.status).toBe(0);
  });

  it("[REQ-F-009] [REQ-SYS-001] solo usa rutas relativas /api/a y /api/b", () => {
    const src = Object.values(api).map((f) => f.toString()).join("\n");
    expect(src).not.toMatch(/https?:\/\//);
  });

  it("[REQ-F-002] valida ISBN-13 en cliente", () => {
    expect(isValidIsbn13("978-0-306-40615-7")).toBe(true);
    expect(isValidIsbn13("9780306406158")).toBe(false);
  });

  it("[REQ-F-001] [REQ-F-003] [REQ-F-004] [REQ-F-005] [REQ-F-006] cubre los endpoints de libros, socios y préstamos", () => {
    expect(Object.keys(api)).toEqual(
      expect.arrayContaining(["books", "createBook", "deleteBook", "members", "createMember", "deleteMember", "loans", "createLoan", "returnLoan", "book"]),
    );
  });
});
