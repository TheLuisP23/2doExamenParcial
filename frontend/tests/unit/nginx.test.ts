import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const conf = readFileSync(new URL("../../nginx/templates/default.conf.template", import.meta.url), "utf8");

describe("plantilla Nginx", () => {
  it("[REQ-F-008] [REQ-SYS-001] proxy con strip de prefijo y sin CORS", () => {
    expect(conf).toMatch(/location \/api\/a\/ \{\s*proxy_pass \$\{SERVICE_A_UPSTREAM\}\/;/);
    expect(conf).toMatch(/location \/api\/b\/ \{\s*proxy_pass \$\{SERVICE_B_UPSTREAM\}\/;/);
    expect(conf).not.toMatch(/Access-Control-Allow-Origin/i);
    expect(conf).toContain("X-Request-ID $request_id");
  });

  it("[REQ-F-008] fallback de SPA, salud y cabeceras de seguridad", () => {
    expect(conf).toContain("try_files $uri /index.html");
    expect(conf).toMatch(/location = \/health\/live/);
    expect(conf).toMatch(/location = \/health\/ready/);
    for (const h of ["X-Content-Type-Options nosniff", "Referrer-Policy same-origin", "X-Frame-Options DENY"]) {
      expect(conf).toContain(h);
    }
    expect(conf).toContain("listen 8080");
  });
});
