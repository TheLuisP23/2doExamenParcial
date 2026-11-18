// Logs JSON con request_id (REQ-SYS-004).
import { randomUUID } from "node:crypto";
import type { NextFunction, Request, Response } from "express";
import pino, { type DestinationStream, type Logger } from "pino";

export function makeLogger(level = "info", dest?: DestinationStream): Logger {
  return pino(
    {
      level,
      base: { service: "service-b" },
      messageKey: "message",
      timestamp: () => `,"timestamp":"${new Date().toISOString()}"`,
      formatters: { level: (label) => ({ level: label }) },
    },
    dest,
  );
}

export function requestLogger(logger: Logger) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const rid = req.header("x-request-id") ?? randomUUID();
    const start = process.hrtime.bigint();
    res.setHeader("X-Request-ID", rid);
    res.on("finish", () => {
      logger.info(
        {
          request_id: rid,
          method: req.method,
          path: req.path,
          status: res.statusCode,
          duration_ms: Number(process.hrtime.bigint() - start) / 1e6,
        },
        "request",
      );
    });
    next();
  };
}
