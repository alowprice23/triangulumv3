Short answer: **yes—the CLI itself is agentic.** It plans, reasons, and decides *how* to debug (single file vs. whole repo), *what* to read, and *which* agents/tools to invoke. Below is a **complete file map** (≤170 files), rebuilt to explicitly cover: (1) agentic CLI; (2) project discovery; (3) “family-tree” file/dependency graphing; (4) single-file vs. folder-wide debugging; plus the full runtime, proof artifacts, tests, and ops. I include **descriptions + LOC estimates**. Totals at the end.

---

# Repository: `triangulum/`

## 0) Top level

* **README.md** — overview, quickstart, examples; single-file vs. repo modes. *LOC \~300*
* **pyproject.toml** — deps, entry points, lint config. *LOC \~60*
* **requirements.txt** — runtime deps (typer, rich, fastapi, pydantic, networkx, gitpython, pytest). *LOC \~35*
* **.gitignore** — standard ignores + `.triangulum/` workdir. *LOC \~40*
* **LICENSE** — license text. *LOC \~1*

---

## 1) Agentic CLI (core UX “brain”)

* **cli/**init**.py** — package. *LOC \~5*
* **cli/entry.py** — console entry `tri`; loads config, dispatches to subcommands. *LOC \~140*
* **cli/agentic\_router.py** — interprets user intent (file vs. dir; quick vs. deep); composes plans. *LOC \~220*
* **cli/commands/run.py** — `tri run [path]` agentic run (scan → scope → plan → execute). *LOC \~200*
* **cli/commands/plan.py** — `tri plan [path]` produce step-by-step reasoning plan. *LOC \~130*
* **cli/commands/status.py** — live view: agents, backlog, entropy, timers, invariants. *LOC \~120*
* **cli/commands/explain.py** — explain decisions; show “why these files/tests.” *LOC \~120*
* **cli/commands/graph.py** — emit/visualize file “family tree”; export Graphviz/JSON. *LOC \~160*
* **cli/commands/rollback.py** — rollback last patch bundle; audit trail. *LOC \~110*
* **cli/commands/escalate.py** — enqueue human review or widen scope. *LOC \~90*
* **cli/commands/dashboard.py** — launch local FastAPI dashboard. *LOC \~80*
* **cli/commands/simulate.py** — Monte-Carlo/what-if (p\_fail, p\_spawn, timers). *LOC \~140*
* **cli/commands/scan.py** — dry-run scanner + scope preview. *LOC \~120*

**Agentic behavior**: `agentic_router` builds a *plan* per invocation using project signals (language, build files, test locations), constraints (time budget), and the entropy model; it chooses single-file “surgical” mode or repo-wide mode, and determines the file family tree depth to traverse.

---

## 2) Project discovery & “family tree” graph

* **discovery/**init**.py** — package. *LOC \~5*
* **discovery/repo\_scanner.py** — walk filesystem, honor `.gitignore`, language-aware filters. *LOC \~220*
* **discovery/ignore\_rules.py** — merge `.gitignore`, `.triangulumignore`, defaults. *LOC \~140*
* **discovery/language\_probe.py** — detect primary stack (Python/Node/Java/etc.). *LOC \~130*
* **discovery/build\_systems.py** — detect build tools (pip/poetry, npm/yarn/pnpm, maven/gradle). *LOC \~180*
* **discovery/test\_locator.py** — find unit/integration tests, map them to modules. *LOC \~180*
* **discovery/symbol\_index.py** — fast ctags/pyast/ts AST summary: defs, imports, refs. *LOC \~280*
* **discovery/dep\_graph.py** — construct multi-lang dependency graph (networkx). *LOC \~260*
* **discovery/family\_tree.py** — from a *target file or test*, compute closure: upstream/downstream impacted files (the “family tree”). *LOC \~230*
* **discovery/scope\_proposals.py** — propose scopes (minimal set vs. expanded set) with entropy caps. *LOC \~180*
* **discovery/manifest.py** — emit machine-readable manifest: files, tests, graph hash. *LOC \~120*

**Single file vs. folder**:

* *Single file*: `family_tree` seeds from that file, walks imports/refs to find minimal test set; `scope_proposals` caps H₀.
* *Folder/repo*: `repo_scanner` + `dep_graph` seed from root; `scope_proposals` partitions into components and selects the component that owns failing tests.

---

## 3) Entropy logic & planning

* **entropy/**init**.py** — package. *LOC \~5*
* **entropy/estimator.py** — estimate H₀ from candidate set size; g per iteration from constraints/tests. *LOC \~220*
* **entropy/constraint\_bank.py** — learned clauses (e.g., failing stack signatures) → ΔH. *LOC \~180*
* **entropy/plan\_costing.py** — estimate iterations `N* = ceil(H₀/g)` and wall-time. *LOC \~160*
* **entropy/explainer.py** — human summary (bits remaining, risk). *LOC \~120*

---

## 4) Runtime state machine & scheduling

* **runtime/**init**.py** — package. *LOC \~5*
* **runtime/state.py** — states, timers, attempts; dataclasses. *LOC \~160*
* **runtime/transition.py** — deterministic `T(s, τ, attempts, agents)`. *LOC \~180*
* **runtime/invariants.py** — capacity/safety assertions; liveness preconditions. *LOC \~180*
* **runtime/scheduler.py** — severity×age priority + fairness; lexicographic safe-mode. *LOC \~220*
* **runtime/pid.py** — backlog/utilization PI with anti-windup; drain control. *LOC \~200*
* **runtime/supervisor.py** — tick loop; integrates scheduler, PID, spawn/defer. *LOC \~260*
* **runtime/spawn\_policy.py** — p\_spawn with hysteresis; budget accounting. *LOC \~180*
* **runtime/deferred\_queue.py** — deferred spawn FIFO; no leaks; aging. *LOC \~160*
* **runtime/allocator.py** — distributed/atomic 3-agent allocation. *LOC \~180*
* **runtime/parallel\_executor.py** — run ≤3 concurrent bugs; total agents ≤9. *LOC \~170*
* **runtime/rollback\_manager.py** — patch bundle registry & revert. *LOC \~150*

---

## 5) Agents (Observer / Analyst / Verifier) & coordinator

* **agents/**init**.py** — package. *LOC \~5*
* **agents/llm\_config.py** — model routing, temperature/stop tokens. *LOC \~90*
* **agents/prompts.py** — role prompts (Observer/Analyst/Verifier) with goal/manifest context. *LOC \~160*
* **agents/observer.py** — reproduce failures; capture logs; shrink repro. *LOC \~200*
* **agents/analyst.py** — trace/static analysis; propose patch plans. *LOC \~240*
* **agents/verifier.py** — run tests/fuzz; evaluate efficacy/regression. *LOC \~220*
* **agents/coordinator.py** — orchestrate O→A→V rounds; stopping rules. *LOC \~260*
* **agents/memory.py** — cross-case memory (patch motifs, flaky test cache). *LOC \~170*
* **agents/meta\_tuner.py** — small loop that tunes prompts/knobs from outcomes. *LOC \~150*

---

## 6) Tooling (scope, compression, patch, testing, sandbox)

* **tooling/**init**.py** — package. *LOC \~5*
* **tooling/scope\_filter.py** — apply allow/deny globs; clamp H₀. *LOC \~200*
* **tooling/compress.py** — log/test-output compressor, token budgeter. *LOC \~160*
* **tooling/patch\_bundle.py** — create/apply signed patch bundles (git worktree). *LOC \~150*
* **tooling/repair.py** — DAG-aware patch applier (Tarjan SCC, ripple scoring). *LOC \~160*
* **tooling/test\_runner.py** — deterministic unit test harness; JSON report; coverage taps. *LOC \~230*
* **tooling/fuzz\_runner.py** — quick fuzz hooks for supported stacks. *LOC \~120*
* **tooling/canary\_runner.py** — docker-compose canary; health probe. *LOC \~180*
* **tooling/smoke\_runner.py** — execute smoke suite inside canary; JSON. *LOC \~160*
* **tooling/sandbox.py** — jailed subprocess/limits (timeouts, env). *LOC \~150*
* **tooling/context\_window\.py** — prompt trimming/structuring. *LOC \~120*

---

## 7) Language adapters (enable single-file or repo-wide debugging)

* **adapters/**init**.py** — package. *LOC \~5*
* **adapters/python.py** — module→test mapping, venv, pytest args, coverage. *LOC \~220*
* **adapters/node.py** — workspace detection (npm/yarn/pnpm), jest/vitest mapping. *LOC \~220*
* **adapters/java.py** — maven/gradle detection, test mapping (JUnit). *LOC \~220*
* **adapters/go.py** — `go mod` mapping; `go test` integration. *LOC \~180*
* **adapters/ruby.py** — bundler/rspec mapping. *LOC \~160*
* **adapters/shared\_build.py** — common patterns (env vars, CI flags). *LOC \~150*

These adapters are what make the **family-tree** actionable for real builds/tests across ecosystems.

---

## 8) Knowledge & persistence

* **kb/**init**.py** — package. *LOC \~5*
* **kb/constraint\_store.py** — learned constraints; dedup; TTL. *LOC \~200*
* **kb/lineage.py** — parent/child relationships; audit chain. *LOC \~160*
* **kb/manifest\_store.py** — store/retrieve manifests + hashes. *LOC \~140*
* **storage/**init**.py** — package. *LOC \~5*
* **storage/wal.py** — append-only WAL frames; CRC pages; replay cursor. *LOC \~280*
* **storage/snapshot.py** — periodic compaction/export (optional S3). *LOC \~200*
* **storage/recovery.py** — crash recovery to last good CRC. *LOC \~180*
* **storage/crc.py** — CRC helpers. *LOC \~60*

---

## 9) Observability & service surfaces

* **obs/**init**.py** — package. *LOC \~5*
* **obs/metrics.py** — Prometheus metrics exporters. *LOC \~180*
* **obs/heartbeat.py** — supervisor/agent heartbeats; lag alerts. *LOC \~120*
* **obs/logging.py** — structured logs; spans. *LOC \~140*
* **dashboard/**init**.py** — package. *LOC \~5*
* **dashboard/server.py** — FastAPI + SSE/HTMX, live entropy/backlog. *LOC \~200*
* **dashboard/pages.py** — routes/templates. *LOC \~140*
* **human\_hub/**init**.py** — package. *LOC \~5*
* **human\_hub/server.py** — FastAPI review queue; approve/reject endpoints. *LOC \~140*

---

## 10) API surface (LLM + VCS/CI)

* **api/**init**.py** — package. *LOC \~5*
* **api/llm\_router.py** — OpenAI/Anthropic/Gemini router with fallbacks. *LOC \~200*
* **api/vcs.py** — GitHub/GitLab ops (PR comments, status). *LOC \~160*
* **api/ci.py** — GitHub Actions/Jenkins triggers, artifact pulls. *LOC \~150*

---

## 11) Formal proofs & model checking

* **spec/README\_spec.md** — how to run TLC/Apalache; proof checklist. *LOC \~140*
* **spec/tla/Triangulation.tla** — state machine + invariants. *LOC \~320*
* **spec/tla/Triangulation.cfg** — constants, invariants, depth. *LOC \~20*
* **spec/diagrams/state\_diagram.puml** — PlantUML of states. *LOC \~50*
* **spec/diagrams/sequence\_15\_tick.svg** — sequence chart. *LOC \~1*

---

## 12) Config & policy

* **config/defaults.toml** — PID targets, caps, safe-mode toggles. *LOC \~120*
* **config/language\_rules.toml** — per-language test/graph rules. *LOC \~120*
* **config/ignore.defaults** — built-in ignores (logs, build dirs). *LOC \~80*
* **config/security.yaml** — key policy, path sandbox rules. *LOC \~80*

---

## 13) Scripts & ops

* **scripts/dev\_up.sh** — start local stack (dashboard, hub). *LOC \~60*
* **scripts/run\_tlc.sh** — TLC runner (heap, workers). *LOC \~35*
* **scripts/run\_apalache.sh** — Apalache checks. *LOC \~40*
* **scripts/run\_simulation.py** — 60-tick reference trace generator. *LOC \~140*
* **scripts/check\_format.sh** — black/isort/ruff. *LOC \~25*
* **docker/Dockerfile** — runtime image for canary. *LOC \~40*
* **docker/docker-compose.yml** — app+db services; canary network. *LOC \~70*
* **docker/entrypoint.sh** — container entry. *LOC \~35*

---

## 14) Tests (unit, property, concurrency, e2e)

* **tests/unit/test\_state.py** — transitions & timers. *LOC \~220*
* **tests/unit/test\_invariants.py** — capacity, liveness preconditions. *LOC \~220*
* **tests/unit/test\_scheduler.py** — priority & fairness. *LOC \~200*
* **tests/unit/test\_pid.py** — anti-windup & stability. *LOC \~200*
* **tests/unit/test\_family\_tree.py** — dependency closure correctness. *LOC \~220*
* **tests/unit/test\_scope\_filter.py** — H₀ clamp behavior. *LOC \~180*
* **tests/unit/test\_manifest.py** — manifest integrity/hash. *LOC \~160*
* **tests/property/test\_runtime\_props.py** — Hypothesis invariants. *LOC \~260*
* **tests/concurrency/test\_allocator\_race.py** — stress triplet allocation. *LOC \~220*
* **tests/concurrency/test\_deferred\_queue.py** — leak-free draining. *LOC \~200*
* **tests/e2e/test\_single\_file\_quick.py** — single-file surgical run. *LOC \~200*
* **tests/e2e/test\_repo\_wide\_deep.py** — repo-wide deep run with canary/smoke. *LOC \~220*
* **tests/e2e/test\_cli\_explain\_graph.py** — CLI graph & explain outputs. *LOC \~180*

---

## 15) Workdir (runtime artifacts; generated)

* **.triangulum/** *(created at runtime)*

  * `manifests/*.json` — scan/scope manifests.
  * `patches/*.tar.gz` — patch bundles.
  * `wal/*.log` — WAL segments.
  * `snapshots/*.bin` — compacted state.
  * `review.db` — human hub sqlite.
  * `graphs/*.json` — family tree exports.

*(No LOC; listed to show the CLI’s operating footprint.)*

---

# How the agentic CLI decides single-file vs. repo-wide

1. **Intent parse** (`agentic_router`):

   * If target is a *file*, seed `family_tree` from that file, select tests touching it, and propose **surgical scope** (fewest files, minimal H₀).
   * If target is a *directory* or repo root, run `repo_scanner` → `dep_graph`, find failing tests/components, propose **component scope** first; if signals are diffuse, fall back to **repo scope**.

2. **Scope Decision** (`scope_proposals` + `entropy/plan_costing`):

   * Compare estimated **N\*** and wall-time for *surgical* vs. *component* vs. *repo* scopes.
   * Select the *lowest-cost* scope that satisfies confidence thresholds; safe-mode always picks the smallest.

3. **Execution Plan** (`cli/commands/run.py`):

   * Apply `scope_filter` (cap H₀), then run **O→A→V** cycles under **supervisor** with **PID** control.
   * On partial success or persistent failures, the CLI can **escalate** or **widen scope** automatically.

---

# Totals

* **File count (source & configs & scripts & tests):** 132 (well under the 170 cap).
* **Estimated total LOC:** \~**12,600–13,300**

  * Agentic CLI & router: \~1,400
  * Discovery & family tree: \~1,610
  * Entropy & planning: \~685
  * Runtime (state machine, PID, spawn, alloc, parallel): \~1,960
  * Agents & coordinator: \~1,445
  * Tooling (scope, patch, test/canary/smoke, sandbox): \~1,520
  * Adapters (multi-lang): \~1,130
  * Knowledge & persistence: \~1,020
  * Observability & surfaces: \~790
  * API (LLM, VCS/CI): \~515
  * Formal spec & diagrams: \~531
  * Config & policy: \~400
  * Scripts & ops: \~370
  * Tests (unit/property/concurrency/e2e): \~2,000

---

## Why this version is “complete”

* The **CLI is agentic**: it *reasons* about scope, builds a plan, and chooses tools/agents accordingly.
* It contains the **family-tree machinery** (symbol index, dep graph, closures) that earlier made your bulky map necessary—but now it’s modular and explicit.
* It supports **single-file surgical** and **repo-wide deep** modes with measurable entropy bounds, plus **proofs** (TLA+, invariants tests), **observability**, **canary/smoke**, **rollback**, and **human-in-the-loop**.

If you want, I can export this as a **printable tree** or a **CSV** (`path, description, LOC`) for planning/sprints.
