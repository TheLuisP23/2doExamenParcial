// Arranque: config → Mongo → índices → servidor.
import { createApp } from "./api/app.js";
import { loadConfig } from "./config.js";
import { Library } from "./domain/library.js";
import { makeLogger } from "./logger.js";
import {
  connect,
  ensureIndexes,
  MongoLoanRepository,
  MongoMemberRepository,
  ping,
} from "./repository/mongo.js";

async function main() {
  const logger = makeLogger(process.env.SERVICE_B_LOG_LEVEL ?? "info");
  let cfg;
  try {
    cfg = loadConfig();
  } catch (e) {
    logger.fatal({ err: e }, "configuration error");
    process.exit(1);
  }
  const { client, db } = await connect(cfg.mongoUri, cfg.mongoDb, cfg.readyTimeoutMs);
  await ensureIndexes(db);
  const lib = new Library(
    new MongoMemberRepository(db),
    new MongoLoanRepository(db),
    { now: () => new Date() },
    cfg,
  );
  const server = createApp(lib, logger, () => ping(db)).listen(cfg.port, () =>
    logger.info({ port: cfg.port }, "service-b listening"),
  );
  const stop = () => server.close(() => void client.close().then(() => process.exit(0)));
  process.on("SIGTERM", stop);
  process.on("SIGINT", stop);
}

void main();
