import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  server: {host:"127.0.0.1", proxy:{"/v1":"http://127.0.0.1:8090","/health":"http://127.0.0.1:8090"}},
  test: { environment:"jsdom", include:["src/**/*.test.tsx"], setupFiles:["./src/test-setup.ts"] },
});
