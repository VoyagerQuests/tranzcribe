# Plan to Change to Aspire

## Goal
Adopt .NET Aspire to orchestrate and observe this Python CLI (tranzcribe), with a clear path to logs/telemetry and optional containerization.

## Assumptions
- We want to keep the project as a Python CLI.
- We want to see logs/traces in the Aspire dashboard.
- We’ll run the app locally first, then optionally containerize.

## Step-by-Step Switch Plan

### Phase 1: Add Aspire AppHost (orchestration)
1. Install Aspire tooling on the dev machine (if not already installed).
2. Initialize Aspire in the repo (creates an AppHost project).
3. Decide orchestration mode:
   - Option A: Run the Python CLI directly via Aspire’s Python hosting integration.
   - Option B: Run the CLI from a Dockerfile via Aspire’s container resource.

### Phase 2: Wire the Python CLI into AppHost
**Option A (Python hosting integration)**
1. Add Aspire’s Python hosting package to the AppHost.
2. In `AppHost.cs`, register a Python app resource pointing to this repo and entrypoint (`main.py` or the script that runs `tranzcribe`).
3. If the Python integration is experimental, suppress any related diagnostics warnings in the AppHost project.

**Option B (Docker integration)**
1. Add a `Dockerfile` that installs dependencies and sets the entrypoint to run `tranzcribe`.
2. In `AppHost.cs`, register the container with `AddDockerfile(...)`.

### Phase 3: Add Observability (logs + traces)
1. Add OpenTelemetry SDK + OTLP exporter to the Python project dependencies.
2. Initialize OpenTelemetry at startup (before executing the pipeline).
3. Wrap the OpenAI call in a trace span.
4. Emit structured log fields for request metadata (model, audio size, duration).
5. Add a safe debug option to log or persist the raw OpenAI response (guarded by a flag/environment variable).
6. Configure OTLP endpoint to point to the Aspire dashboard collector.

### Phase 4: Validate End-to-End
1. Run the AppHost.
2. Trigger a `tranzcribe` run.
3. Confirm logs and traces appear in the Aspire dashboard.
4. Confirm OpenAI response metadata is visible.

### Phase 5: Hardening (optional)
1. Add environment configuration for:
   - `OPENAI_API_KEY`
   - OTEL exporter endpoint
   - debug logging toggle
2. Add runbook notes for local and CI usage.

## Deliverables
- Aspire AppHost project in the repo.
- Either Python integration or Docker resource registration.
- OpenTelemetry wiring in the Python CLI.
- Documented run instructions and environment variables.
