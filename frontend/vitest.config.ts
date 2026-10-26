import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Characterization tests of the shared UI and of the screens: they pin what the code does today before it is restructured.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    include: ["packages/*/src/**/*.test.{ts,tsx}", "web/src/**/*.test.{ts,tsx}", "console/src/**/*.test.{ts,tsx}"],
  },
});
