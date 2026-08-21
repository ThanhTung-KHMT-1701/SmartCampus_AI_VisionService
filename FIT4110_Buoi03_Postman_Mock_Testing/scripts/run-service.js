#!/usr/bin/env node
// Launch one of the AI Vision Service / side mocks.
// Cross-platform wrapper that sets PYTHONPATH=src and shells out to python -m uvicorn.

const { spawn } = require("node:child_process");
const path = require("node:path");

const services = {
  vision: { app: "ai_vision_service.main:app", port: "8000" },
  "camera-mock": { app: "side_mocks.camera_stream:app", port: "4014" },
  "core-mock": { app: "side_mocks.core_business:app", port: "4012" },
};

const name = process.argv[2] || "vision";
const cfg = services[name];
if (!cfg) {
  console.error(`Unknown service '${name}'. Use: ${Object.keys(services).join(", ")}`);
  process.exit(1);
}

const python = process.env.PYTHON
  || (process.platform === "win32" ? "python" : "python3");
const env = { ...process.env, PYTHONPATH: path.join(__dirname, "..", "src") };

const args = ["-m", "uvicorn", cfg.app, "--host", "127.0.0.1", "--port", cfg.port, "--log-level", "warning"];
const child = spawn(python, args, { stdio: "inherit", env });

child.on("exit", (code) => process.exit(code ?? 1));
child.on("error", (err) => {
  console.error(`Failed to launch ${name}:`, err.message);
  process.exit(1);
});
