import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    testTimeout: 120_000,
    hookTimeout: 180_000,
    coverage: {
      provider: "v8",
      include: ["src/**"],
      exclude: ["src/main.ts", "src/repository/**", "src/domain/ports.ts"],
      thresholds: { lines: 80 },
    },
  },
});
