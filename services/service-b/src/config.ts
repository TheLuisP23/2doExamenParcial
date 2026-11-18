// Configuración solo por entorno, con fallo rápido (REQ-SYS-005).
import { z } from "zod";

const schema = z.object({
  SERVICE_B_MONGO_URI: z.string().min(1),
  SERVICE_B_MONGO_DB: z.string().default("members"),
  SERVICE_B_PORT: z.coerce.number().int().default(3000),
  SERVICE_B_LOG_LEVEL: z.string().default("info"),
  SERVICE_B_MAX_ACTIVE_LOANS: z.coerce.number().int().min(1).default(3),
  SERVICE_B_DEFAULT_LOAN_DAYS: z.coerce.number().int().min(1).default(14),
  SERVICE_B_READY_TIMEOUT_MS: z.coerce.number().int().default(2000),
});

export interface Config {
  mongoUri: string;
  mongoDb: string;
  port: number;
  logLevel: string;
  maxActiveLoans: number;
  defaultLoanDays: number;
  readyTimeoutMs: number;
}

export function loadConfig(env: NodeJS.ProcessEnv = process.env): Config {
  const r = schema.safeParse(env);
  if (!r.success) {
    const missing = r.error.issues.map((i) => i.path.join(".")).join(", ");
    throw new Error(`invalid configuration: ${missing}`);
  }
  const e = r.data;
  return {
    mongoUri: e.SERVICE_B_MONGO_URI,
    mongoDb: e.SERVICE_B_MONGO_DB,
    port: e.SERVICE_B_PORT,
    logLevel: e.SERVICE_B_LOG_LEVEL,
    maxActiveLoans: e.SERVICE_B_MAX_ACTIVE_LOANS,
    defaultLoanDays: e.SERVICE_B_DEFAULT_LOAN_DAYS,
    readyTimeoutMs: e.SERVICE_B_READY_TIMEOUT_MS,
  };
}
