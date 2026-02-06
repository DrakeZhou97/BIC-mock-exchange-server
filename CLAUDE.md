# Mock Robot Server — CLAUDE.md

## Project Overview

This repository is a **mock Exchange server** that simulates the RabbitMQ-based communication layer between **LabRun** (the orchestrator) and **Robot workers** (Talos humanoid robots) in a BIC (Bio-Inspired Chemistry) laboratory automation system. It replaces the real robot-side `mars_service` for development and testing of the LabRun side.

### Target Architecture (from `system_architecture.png` and `v0.2 Skill-level Runtime Service.pdf`)

```
LabRun ──publish──> [Exchange (TOPIC)] ──queue_bind──> [robot_id.cmd] ──consume──> Robot
LabRun <──consume── [#.log / #.result / #.hb] <──publish── Robot
LabRun <──read──── [MinIO] <──write── Robot (photos, objects)
```

The architecture runs on an **Edge Box** with:
- **RabbitMQ** — Central TOPIC exchange for all message routing
- **MinIO** — Object storage for photos/captures
- **Local Server** — Optional edge-side offline monitor/logger

---

## Gap Analysis: Current State vs. Target Specification

### Legend
- `[DONE]` — Fully implemented and tested
- `[PARTIAL]` — Implemented but incomplete or diverges from spec
- `[MISSING]` — Not implemented at all

---

### 1. Communication Layer (RabbitMQ Exchange)

| Aspect | Spec Requirement | Current State | Gap |
|--------|-----------------|---------------|-----|
| Exchange type | Single TOPIC exchange for all messages | `[PARTIAL]` — Uses TOPIC exchange but with simplified topology (`robot.commands` / `robot.results`) | Spec uses a **single** Exchange with routing keys like `talos_001.cmd`, `talos_001.log`, `talos_001.result`, `talos_001.hb`, `device_xxx.log`. Current implementation uses **two separate exchanges/queues** (`robot.commands` + `robot.results` direct queue) instead of routing everything through one exchange. |
| Routing keys — Commands | `<robot_id>.cmd` (e.g. `talos_001.cmd`) | `[PARTIAL]` — Uses generic `robot.command` routing key | Should route to individual robot queues via `<robot_id>.cmd` pattern per spec |
| Routing keys — Logs | `<robot_id>.log` and `device_xxx.log` | `[MISSING]` — No log channel publishing | Robot should publish real-time logs during skill execution via `<robot_id>.log` |
| Routing keys — Results | `<robot_id>.result` | `[PARTIAL]` — Publishes to `robot.results` direct queue | Should publish via the exchange with `<robot_id>.result` routing key |
| Routing keys — Heartbeat | `<robot_id>.hb` | `[MISSING]` — No heartbeat mechanism | Robot should send heartbeat every 2 seconds; LabRun detects offline after 5 seconds |
| Queue binding on LabRun side | Binds `#.log`, `#.result`, `#.hb` wildcards | N/A (not LabRun side) | — |
| Queue binding on Robot side | Binds `<robot_id>.cmd` per robot | `[PARTIAL]` — Uses single shared consumer queue | Should support per-robot command queues |
| Multi-robot support | Multiple robots (`talos_001`, `talos_002`, etc.) | `[PARTIAL]` — Single `robot_id` config, no multi-robot | Need configurable robot identity and support for running multiple robot instances |

### 2. Skill API — Command/Response Contract

| Skill | Spec Task Name | Current Task Name | Status | Gap Details |
|-------|---------------|-------------------|--------|-------------|
| Setup Cartridges | `setup_tubes_to_column_machine` | `setup_tubes_to_column_machine` | `[DONE]` | Request/response schemas match |
| Setup Tube Rack | `setup_tube_rack` | `setup_tube_rack` | `[DONE]` | Request/response schemas match |
| Take Photo | `take_photo` | `take_photo` | `[DONE]` | Request/response schemas match |
| Start CC | `start_column_chromatography` | `start_column_chromatography` | `[DONE]` | Long-running with intermediate updates |
| Terminate CC | `terminate_column_chromatography` | `terminate_column_chromatography` | `[DONE]` | Includes screen capture on termination |
| Fraction Consolidation | `fraction_consolidation` | `fraction_consolidation` | `[DONE]` | `collect_config` array handled correctly |
| Start Evaporation | `start_evaporation` | `start_evaporation` | `[DONE]` | Profiles/triggers system implemented |
| Collapse Cartridges | Not in spec (custom addition) | `collapse_cartridges` | `[EXTRA]` | Added for convenience; not in v0.2 spec — document or remove |
| Stop Evaporation | `stop_evaporation` (TODO in spec) | Not implemented | `[MISSING]` | Marked as TODO in spec, low priority |
| Setup CCS Bins | `setup_ccs_bins` (TODO in spec) | Not implemented | `[MISSING]` | Marked as TODO in spec |
| Return CCS Bins | `return_ccs_bins` (TODO in spec) | Not implemented | `[MISSING]` | Marked as TODO in spec |
| Return Cartridges | `return_cartridges` (TODO in spec) | Not implemented | `[MISSING]` | Marked as TODO in spec |
| Return Tube Rack | `return_tube_rack` (TODO in spec) | Not implemented | `[MISSING]` | Marked as TODO in spec |

### 3. Real-time Log Streaming

| Aspect | Spec Requirement | Current State | Gap |
|--------|-----------------|---------------|-----|
| Log channel | Robot publishes state updates via `<robot_id>.log` routing key **as they happen** during skill execution | `[MISSING]` | Spec explicitly states: "state updates are sent in real-time when state changes occur, NOT all at once when the action completes". Currently, intermediate updates exist for CC/Evaporation only, but they go through the result channel, not a dedicated log channel. |
| Device log channel | Device state published via `device_xxx.log` | `[MISSING]` | No device-specific log routing |
| Incremental updates | Each state change emits an individual update message | `[PARTIAL]` | Only CC and Evaporation simulators emit intermediate updates; other skills batch all updates in the final response |

### 4. Heartbeat System

| Aspect | Spec Requirement | Current State | Gap |
|--------|-----------------|---------------|-----|
| Heartbeat publishing | Robot publishes heartbeat every 2 seconds via `<robot_id>.hb` | `[MISSING]` | No heartbeat mechanism exists |
| Heartbeat format | Periodic pulse message | `[MISSING]` | No heartbeat schema defined |
| Online/offline detection | LabRun detects offline if >5 seconds without heartbeat | N/A (LabRun side) | — |

### 5. MinIO / Object Storage Integration

| Aspect | Spec Requirement | Current State | Gap |
|--------|-----------------|---------------|-----|
| Photo upload | Robot saves photos to MinIO, returns accessible URL | `[PARTIAL]` — Generates mock URLs (`http://minio:9000/bic-robot/captures/...`) | URLs are fabricated; no actual MinIO interaction. Acceptable for mock server, but URL format should match real MinIO bucket paths. |
| Object retrieval | LabRun reads images/objects from MinIO by URI | N/A (LabRun side) | — |
| Local Server dump | Local Server dumps logs to MinIO | `[MISSING]` | Not in scope for mock server |

### 6. State Management

| Aspect | Spec Requirement | Current State | Gap |
|--------|-----------------|---------------|-----|
| Robot states | idle, wait_for_screen_manipulation, watch_column_machine_screen, moving_with_round_bottom_flask, observe_evaporation | `[DONE]` | All defined in `RobotState` enum |
| Equipment states | available, mounted, using, used, running, terminated | `[DONE]` | Defined in `EquipmentState` enum |
| Compound states | e.g. `"used,pulled_out,ready_for_recovery"` | `[PARTIAL]` | Handled as raw strings in some cases, no formal state machine |
| Entity types — 10 types | robot, silica_cartridge, sample_cartridge, tube_rack, round_bottom_flask, ccs_ext_module, column_chromatography_system, evaporator, pcc_left_chute, pcc_right_chute | `[DONE]` | All 10 entity types have factory functions and Pydantic models |
| Device state lifecycle | Formal state transitions (spec notes: "needs systematic design") | `[PARTIAL]` | States exist but no validation of legal transitions |

### 7. Error Handling

| Aspect | Spec Requirement | Current State | Gap |
|--------|-----------------|---------------|-----|
| Safety conflict detection | Robot checks preconditions (e.g., cartridge position, existing mounts) | `[PARTIAL]` | Scenario manager can inject failures, but no precondition simulation based on current device state |
| Stateful error responses | Errors based on current world state | `[MISSING]` | No world state tracking; failures are probabilistic, not state-driven |
| Error code ranges | Task-specific error codes | `[DONE]` | Codes 1010-1089 defined per task |

### 8. Configuration & Deployment

| Aspect | Spec Requirement | Current State | Gap |
|--------|-----------------|---------------|-----|
| Docker | Containerized deployment | `[DONE]` | Multi-stage Alpine Dockerfile |
| Docker Compose | Service integration with BIC Lab Service | `[DONE]` | `docker-compose.mock.yml` override |
| Env config | Environment-based configuration | `[DONE]` | Pydantic-settings with `MOCK_` prefix |
| Multi-robot instances | Run multiple robot workers | `[PARTIAL]` | Single robot_id per instance; need ability to spin up N instances |

### 9. Testing

| Aspect | Current State | Gap |
|--------|---------------|-----|
| Unit tests | `[DONE]` — 37 tests covering generators, scenarios, schemas | — |
| Integration tests (MQ) | `[MISSING]` | No tests verifying actual RabbitMQ message flow end-to-end |
| Simulator integration tests | `[MISSING]` | No tests running full simulate → publish flow |
| Heartbeat tests | `[MISSING]` | No heartbeat to test |
| Multi-robot tests | `[MISSING]` | No multi-robot scenarios |

---

## Implementation Plan

### Phase 1: MQ Topology Alignment (Critical)

**Goal:** Align the RabbitMQ exchange and routing key patterns with the spec's single-exchange architecture.

1. **Refactor to single Exchange topology**
   - Rename exchange to a configurable name (e.g., `bic_exchange`)
   - Route commands via `<robot_id>.cmd` routing key pattern
   - Route results via `<robot_id>.result` routing key
   - Route logs via `<robot_id>.log` routing key
   - Route heartbeat via `<robot_id>.hb` routing key
   - Maintain backward compatibility via config flags if needed

2. **Support per-robot identity**
   - `robot_id` config already exists; ensure it's used in all routing keys
   - Command queue name should be `<robot_id>.cmd`
   - Support launching multiple instances with different `robot_id` values

3. **Update consumer queue binding**
   - Bind consumer queue to `<robot_id>.cmd` instead of generic `robot.command`

### Phase 2: Real-time Log Channel (High)

**Goal:** Implement the `<robot_id>.log` channel for real-time state updates during skill execution.

1. **Add LogProducer**
   - New producer class publishing to `<robot_id>.log` routing key via the exchange
   - Message format matches the `updates` array structure from spec responses

2. **Emit incremental state updates in simulators**
   - All simulators should emit state changes as they happen (not just in final result)
   - For long-running tasks (CC, Evaporation), publish intermediate logs on the log channel
   - For quick tasks, emit log entries for each significant state transition (e.g., robot location change, cartridge mounting)

3. **Add device log publishing**
   - Device state changes published via `device_<id>.log` routing key

### Phase 3: Heartbeat System (High)

**Goal:** Implement the periodic heartbeat mechanism per spec.

1. **Add HeartbeatPublisher**
   - Async background task publishing to `<robot_id>.hb` every 2 seconds
   - Configurable interval via settings
   - Start on server boot, stop on shutdown

2. **Define heartbeat message schema**
   - Minimal payload: `{ "robot_id": "talos_001", "timestamp": "...", "state": "idle" }`
   - Or match whatever the real `mars_service` sends

3. **Graceful lifecycle**
   - Heartbeat starts after MQ connection is established
   - Stops cleanly on SIGINT/SIGTERM

### Phase 4: TODO Skills Stubs (Medium)

**Goal:** Add placeholder simulators for the spec's TODO skills to complete the API surface.

1. **`stop_evaporation`** — Stop evaporation, remove flask
2. **`setup_ccs_bins`** — Set up waste bins at CC workstation
3. **`return_ccs_bins`** — Return used bins to waste area
4. **`return_cartridges`** — Remove and return used cartridges
5. **`return_tube_rack`** — Remove and return used tube rack

Each stub:
- Register in `TaskName` enum
- Create params schema
- Create minimal simulator (delay + entity updates)
- Add failure messages
- Add unit tests

### Phase 5: World State Tracking (Medium)

**Goal:** Add in-memory state tracking to enable stateful error simulation.

1. **WorldState class**
   - Track current state of robot, devices, cartridges, tube racks, flasks, bins
   - Update state on each simulated action
   - Query state for precondition validation

2. **Precondition-based failures**
   - Before executing a skill, check preconditions against world state
   - Example: `start_evaporation` fails if robot isn't holding a flask
   - Example: `setup_cartridges` fails if ext_module already has cartridges

3. **State reset endpoint**
   - Management API to reset world state to initial conditions
   - Useful for test automation

### Phase 6: Integration Tests & Quality (Low)

**Goal:** End-to-end confidence in the mock server.

1. **MQ integration tests**
   - Use testcontainers or a local RabbitMQ instance
   - Test: publish command → receive result
   - Test: heartbeat stream
   - Test: log stream during skill execution

2. **Multi-robot scenario tests**
   - Launch 2+ mock robot instances
   - Verify independent command routing

3. **Documentation updates**
   - Update README with new topology diagram
   - Document all routing keys and message formats

---

## Quick Reference

### Tech Stack
- **Python 3.12+**, async-first
- **aio-pika** (RabbitMQ), **pydantic** (schemas), **loguru** (logging)
- **uv** (package manager), **ruff** (lint/format), **pytest** (testing)

### Project Structure
```
src/
  config.py          # Pydantic-settings, MOCK_ env prefix
  main.py            # Entry point, wiring, graceful shutdown
  mq/                # RabbitMQ connection, consumer, producer
  schemas/           # Protocol enums, command/result Pydantic models
  simulators/        # Per-skill simulation logic (base ABC + 5 impls)
  generators/        # Pure factories for entity updates, images, timing
  scenarios/         # Failure/timeout injection
  tests/             # 37 unit tests
```

### Running
```bash
uv run python -m src.main          # Run mock server
uv run pytest src/tests/           # Run tests
```

### Key Config (`.env.mock`)
```env
MOCK_MQ_HOST=localhost
MOCK_ROBOT_ID=talos_001
MOCK_BASE_DELAY_MULTIPLIER=0.1    # 10x speed (0.01 = 100x)
MOCK_FAILURE_RATE=0.0             # 0.0-1.0
MOCK_DEFAULT_SCENARIO=success     # success | failure | timeout
```

### Implemented Skills
1. `setup_tubes_to_column_machine` — Mount cartridges to CCS workstation
2. `setup_tube_rack` — Mount tube rack to CCS workstation
3. `collapse_cartridges` — Disassemble used cartridges (extra, not in spec)
4. `take_photo` — Photograph device components
5. `start_column_chromatography` — Long-running CC with intermediate updates
6. `terminate_column_chromatography` — Stop CC, capture results
7. `fraction_consolidation` — Collect fractions, prepare for evaporation
8. `start_evaporation` — Long-running evaporation with sensor ramp
