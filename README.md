# Mock Robot Server

A standalone microservice that simulates the Robot Exchange MQ Server for local development and testing of the BIC Lab Service. Consumes robot command messages from RabbitMQ, simulates task execution with configurable timing and failure modes, and publishes realistic result messages with entity state updates.

## Architecture

```
┌──────────────────┐         RabbitMQ           ┌──────────────────────┐
│  BIC Lab Service │   robot.exchange (TOPIC)   │  Mock Robot Server   │
│                  │                            │                      │
│  MQ Producer ────┼── {robot_id}.cmd ────────▶ │  Command Consumer    │
│                  │                            │        │             │
│                  │   {robot_id}.result        │   Task Simulator     │
│  Result Consumer◀┼── {robot_id}.log     ◀──── │        │             │
│  Log Consumer   ◀┼── {robot_id}.hb      ◀──── │  Result Publisher    │
│  HB Consumer    ◀┼───────────────────────     │  Log Producer        │
│                  │                            │  Heartbeat Publisher  │
└──────────────────┘                            └──────────────────────┘
```

All messages flow through a single **TOPIC exchange** (`robot.exchange`) with per-robot routing keys:
- `{robot_id}.cmd` — Commands from BIC Lab Service → Robot
- `{robot_id}.result` — Final task results from Robot → BIC Lab Service
- `{robot_id}.log` — Real-time intermediate state updates during execution
- `{robot_id}.hb` — Periodic heartbeat messages (every 2s)

**Dependencies:** RabbitMQ only. No PostgreSQL, Redis, or S3 required.

## Quick Start

### Docker (recommended)

```bash
# Build and run
docker build -t mock-robot-server .
docker run --rm \
  -e MOCK_MQ_HOST=rabbitmq \
  --network bic-lab-service_app-network \
  mock-robot-server
```

### Docker Compose (with BIC Lab Service)

Add to the BIC Lab Service project-level `docker-compose.override.yml`:

```yaml
services:
  mock-robot:
    build:
      context: ../mock-robot-server
      dockerfile: Dockerfile
    environment:
      MOCK_MQ_HOST: rabbitmq
      MOCK_BASE_DELAY_MULTIPLIER: "0.01"   # 100x speed for fast iteration
      MOCK_FAILURE_RATE: "0.1"             # 10% random failures
    depends_on:
      rabbitmq:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
```

Then run everything together:

```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

### Local Development

```bash
# Install dependencies
uv sync

# Run directly
uv run python -m src.main
```

## Configuration Reference

All settings are loaded from environment variables with `MOCK_` prefix via pydantic-settings.

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_MQ_HOST` | `localhost` | RabbitMQ host |
| `MOCK_MQ_PORT` | `5672` | RabbitMQ port |
| `MOCK_MQ_USER` | `guest` | RabbitMQ username |
| `MOCK_MQ_PASSWORD` | `guest` | RabbitMQ password |
| `MOCK_MQ_VHOST` | `/` | RabbitMQ virtual host |
| `MOCK_MQ_EXCHANGE` | `robot.exchange` | Shared TOPIC exchange for all message routing |
| `MOCK_MQ_CONNECTION_TIMEOUT` | `30` | RabbitMQ connection timeout (seconds) |
| `MOCK_MQ_HEARTBEAT` | `60` | AMQP heartbeat interval (seconds) |
| `MOCK_MQ_PREFETCH_COUNT` | `5` | Consumer prefetch count |
| `MOCK_ROBOT_ID` | `00000000-0000-4000-a000-000000000001` | Simulated robot identifier (UUID) |
| `MOCK_DEFAULT_SCENARIO` | `success` | Default scenario: `success`, `failure`, or `timeout` |
| `MOCK_FAILURE_RATE` | `0.0` | Probability of injecting a failure (0.0 - 1.0) |
| `MOCK_TIMEOUT_RATE` | `0.0` | Probability of injecting a timeout / no response (0.0 - 1.0) |
| `MOCK_BASE_DELAY_MULTIPLIER` | `0.1` | Speed multiplier for task durations (0.01 = 100x fast, 1.0 = realistic) |
| `MOCK_MIN_DELAY_SECONDS` | `0.5` | Minimum delay floor (seconds) |
| `MOCK_IMAGE_BASE_URL` | `http://minio:9000/bic-robot/captures` | Base URL returned in mock captured image URLs |
| `MOCK_SERVER_NAME` | `mock-robot-server` | Server instance name for logging |
| `MOCK_LOG_LEVEL` | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `MOCK_HEARTBEAT_INTERVAL` | `2.0` | Seconds between heartbeat messages |
| `MOCK_CC_INTERMEDIATE_INTERVAL` | `300.0` | CC progress update interval at 1.0x (seconds) |
| `MOCK_RE_INTERMEDIATE_INTERVAL` | `300.0` | RE progress update interval at 1.0x (seconds) |

## Supported Task Types (All 13 Tasks)

| Task Name | Realistic Duration | At 0.1x Multiplier | Notes |
|-----------|-------------------|-------------------|-------|
| `setup_tubes_to_column_machine` | 15 - 30 s | 1.5 - 3 s | Retrieves and mounts silica + sample cartridges |
| `setup_tube_rack` | 10 - 20 s | 1 - 2 s | Retrieves and mounts tube rack at work station |
| `take_photo` | 2 - 5 s per component | 0.2 - 0.5 s | Navigates to station, captures device screen |
| `start_column_chromatography` | 30 - 60 min | 3 - 6 min | Long-running; intermediate updates via `.log` channel |
| `terminate_column_chromatography` | 5 - 10 s | 0.5 - 1 s | Stops CC operation, captures result images |
| `fraction_consolidation` | ~1 min (tube count) | ~6 s | Collects fractions from tubes into flask |
| `start_evaporation` | 30 - 90 min | 3 - 9 min | Long-running; sensor ramp via `.log` channel |
| `stop_evaporation` | 5 - 10 s | 0.5 - 1 s | Stops evaporator and returns flask |
| `collapse_cartridges` | 10 - 15 s | 1 - 1.5 s | Cleans up cartridges after process completion |
| `setup_ccs_bins` | 10 - 15 s | 1 - 1.5 s | Sets up waste bins at CC workstation |
| `return_ccs_bins` | 10 - 15 s | 1 - 1.5 s | Returns used bins to waste area |
| `return_cartridges` | 10 - 15 s | 1 - 1.5 s | Removes and returns used cartridges |
| `return_tube_rack` | 10 - 15 s | 1 - 1.5 s | Removes and returns used tube rack |

## World State Tracking & Preconditions

The mock server maintains an in-memory `WorldState` that tracks all entities (robots, devices, materials) and validates preconditions before executing tasks. This enables realistic error simulation based on current system state.

**Error Code Ranges:**
- `1000-1009`: General errors (unknown task, validation failure)
- `1010-1139`: Task-specific failures (per-task 10-code ranges)
- `2000-2099`: Precondition violations (state-driven errors)

**Special Commands:**
- `reset_state`: Clears WorldState back to initial conditions (useful for testing)

**Precondition Examples:**
- `setup_cartridges` fails if ext_module already has cartridges (code 2001)
- `terminate_cc` fails if CC system not running (code 2030-2031)
- `collapse_cartridges` fails if cartridges not in 'used' state (code 2010-2013)

## Scenarios

The mock server supports three execution scenarios, controlled globally by `MOCK_DEFAULT_SCENARIO` or injected randomly via `MOCK_FAILURE_RATE` / `MOCK_TIMEOUT_RATE`.

### Success

The default mode. The server simulates the full task lifecycle:
1. Acknowledges command receipt
2. Publishes intermediate entity state updates via `{robot_id}.log` during execution
3. Waits for the simulated duration
4. Publishes a final `RobotResult` via `{robot_id}.result` with `code: 200`, updated entity states, and any captured images

### Failure

Simulates a robot error mid-task:
1. Begins execution normally with intermediate updates
2. Aborts partway through
3. Publishes a `RobotResult` with task-specific error code (1010-1139), an error message, and partially updated entity states

### Timeout

Simulates a non-responsive robot:
1. Acknowledges the command
2. Never publishes a result message
3. Useful for testing the main service's timeout detection and recovery logic

**Injection priority:** Per-message random injection (`MOCK_FAILURE_RATE`, `MOCK_TIMEOUT_RATE`) takes precedence over `MOCK_DEFAULT_SCENARIO`. If both rates are `0.0`, the default scenario is used.

## Message Flow

```
1. BIC Lab Service publishes a RobotCommand to `robot.exchange` (TOPIC)
   with routing key `{robot_id}.cmd` (e.g., `talos_001.cmd`)

2. Mock Robot Server consumes from its `{robot_id}.cmd` queue:
   - Deserializes the command using Pydantic models
   - Validates preconditions against WorldState
   - Selects scenario (success / failure / timeout)
   - Logs the received command

3. During simulated execution:
   - Publishes intermediate entity updates to `{robot_id}.log`
     (e.g., cartridge state: available -> mounted)
   - Publishes heartbeats to `{robot_id}.hb` every 2 seconds
   - Sleeps for the computed duration (base delay × multiplier)

4. On completion:
   - Builds a RobotResult with:
     - task_id matching the command
     - code: 200 (success) or 1010-2099 (failure)
     - entity_updates: list of state changes
     - captured_images: mock image URLs (for take_photo, terminate_cc)
   - Publishes the result to `{robot_id}.result` routing key
   - Updates WorldState with final entity states
```

## Development

### Tech Stack

- **Python 3.12+**, async-first
- **aio-pika** — async RabbitMQ client
- **pydantic + pydantic-settings** — configuration and message schemas
- **loguru** — structured logging
- **uv** — package manager
- **ruff** — lint/format
- **pytest** — testing

### Project Structure

```
mock-robot-server/
├── src/
│   ├── __main__.py                    # Entry point: python -m src.main
│   ├── main.py                        # Server lifecycle (startup/shutdown)
│   ├── config.py                      # pydantic-settings with MOCK_ prefix
│   ├── schemas/                       # Protocol contract definitions
│   ├── simulators/                    # Per-skill task simulation logic
│   ├── generators/                    # Pure factory functions for outputs
│   ├── scenarios/                     # Failure and timeout injection
│   ├── state/                         # In-memory world state tracking
│   ├── mq/                            # RabbitMQ communication layer
│   └── tests/                         # Unit and integration tests
├── docs/
│   ├── note.md                        # Protocol spec (ground truth)
│   └── ROBOT_ID_DESIGN.md            # Robot ID design decisions
├── Dockerfile
├── docker-compose.mock.yml
├── pyproject.toml
├── .env
└── CLAUDE.md
```

### Module Guide

#### `mq/` — RabbitMQ Communication Layer

The message queue module handles all AMQP communication with RabbitMQ. It implements the robot-side of the protocol: consuming commands and publishing results, logs, and heartbeats through a single TOPIC exchange.

| File | Role |
|------|------|
| `connection.py` | Manages a robust AMQP connection with auto-reconnect. Provides lazy channel creation with QoS (prefetch count) and graceful disconnect. All MQ components share this singleton connection. |
| `consumer.py` | The core dispatcher. Declares the `<robot_id>.cmd` queue, binds it to the TOPIC exchange, and processes incoming `RobotCommand` messages. For each message it: parses and validates parameters via Pydantic, checks preconditions against WorldState, applies scenario overrides (timeout/failure/success), and dispatches to the appropriate simulator. Long-running tasks (`start_cc`, `start_evaporation`) are launched as background `asyncio.Task`s so the consumer remains non-blocking. |
| `producer.py` | Publishes final `RobotResult` messages to `<robot_id>.result` with persistent delivery mode. Called once per task upon completion (or failure). |
| `log_producer.py` | Publishes real-time `LogMessage` entries to `<robot_id>.log` during task execution. Simulators call this to stream intermediate entity state changes (e.g., cartridge `available` → `mounted`) before the final result is ready. Uses non-persistent delivery for low overhead. |
| `heartbeat.py` | Runs a background asyncio loop that publishes `HeartbeatMessage` to `<robot_id>.hb` at a configurable interval (default 2s). Reads the robot's current state from WorldState so the heartbeat accurately reflects operational status (e.g., `watch_column_machine_screen` during CC). |

**How it simulates the robot service:** The real robot's `mars_service` consumes commands from the same exchange/routing-key pattern and publishes results back. This module replicates that exact AMQP topology — same exchange name, same routing keys, same message schemas — so the BIC Lab Service cannot distinguish mock from real.

#### `schemas/` — Protocol Contract Definitions

Defines the Pydantic models and enums that constitute the wire protocol between LabRun and the robot. These types are a self-contained copy of the BIC Lab Service's canonical protocol definitions.

| File | Role |
|------|------|
| `protocol.py` | All shared protocol types: `TaskName` (13 tasks), `RobotState` (9 states including intermediates like `moving`, `terminating_cc`), `EquipmentState`, `BinState` enums, plus all `*Params` models (one per task) defining the expected command parameters. |
| `commands.py` | The `RobotCommand` envelope model (`task_id`, `task_name`, `params`) and convenient re-exports of parameter models for import ergonomics. |
| `results.py` | `RobotResult` (final task outcome with code, message, entity updates, images), `LogMessage` (intermediate state update), `HeartbeatMessage`, and 10 entity update models (`RobotUpdate`, `SilicaCartridgeUpdate`, `CCSystemUpdate`, `EvaporatorUpdate`, etc.) combined into a discriminated union `EntityUpdate` type for type-safe deserialization. |

**How it simulates the robot service:** By using identical Pydantic models with the same field names, types, and validation rules as the production protocol, the mock server produces messages that are schema-identical to real robot output. Any LabRun consumer that can parse real robot messages can parse mock messages without modification.

#### `simulators/` — Per-Skill Task Simulation Logic

Each simulator encapsulates the behavior of one or more robot skills. Simulators receive parsed command parameters, simulate realistic execution timing, emit intermediate log updates, and return a `RobotResult` with entity state changes.

| File | Role |
|------|------|
| `base.py` | Abstract base class (`BaseSimulator`) providing shared infrastructure: `_apply_delay()` for randomized timing with multiplier, `_publish_log()` for streaming intermediate updates, `_resolve_entity_id()` for looking up material UUIDs from WorldState by location, and access to settings (robot_id, multiplier, image_base_url). |
| `setup_simulator.py` | Handles `setup_tubes_to_column_machine`, `setup_tube_rack`, and `collapse_cartridges`. Simulates the robot physically moving to a workstation, picking up materials, and mounting/dismounting them. Emits intermediate states (robot moving → materials mounted → robot idle). |
| `cc_simulator.py` | Handles `start_column_chromatography` (long-running) and `terminate_column_chromatography` (quick). `start_cc` runs as a background task: publishes an initial update with CC system `running` and experiment parameters, then emits periodic progress updates at calculated intervals, and finally publishes the completion result. `terminate_cc` captures a screen image and transitions materials to `used` state. |
| `photo_simulator.py` | Handles `take_photo`. Scales delay by component count, generates mock image URLs per component (`{base_url}/{ws_id}/{device_id}/{component}/{timestamp}.jpg`), and maps `device_type` strings to entity types for WorldState updates. Supports all device types: combiflash, CC system, evaporator. |
| `consolidation_simulator.py` | Handles `fraction_consolidation`. Counts collected tubes from the `collect_config` bitmask, scales delay proportionally (3s per tube + 10s base), and produces updates for tube rack, round-bottom flask, and PCC left/right chutes with positioning data. |
| `evaporation_simulator.py` | Handles `start_evaporation` (long-running). Publishes initial ambient sensor readings (25°C, 1013 mbar), then linearly interpolates temperature and pressure toward target values across periodic updates, simulating a realistic sensor ramp. Duration is extracted from the stop-trigger profile. |
| `cleanup_simulator.py` | Handles 5 cleanup tasks: `stop_evaporation`, `setup_ccs_bins`, `return_ccs_bins`, `return_cartridges`, `return_tube_rack`. These are quick operations that transition entities to their post-use states (e.g., evaporator → stopped, bins → closed, cartridges → stored in waste). |

**How it simulates the robot service:** Real robot skills involve physical motion, sensor feedback, and hardware interaction. Simulators replicate the *observable behavior* — the same sequence of state transitions, the same entity updates, the same timing profile (scaled by a configurable multiplier) — without any physical hardware. This lets LabRun exercise its full workflow logic against realistic robot responses.

#### `generators/` — Pure Factory Functions

Stateless factory functions that build the data structures simulators need. Separated from simulators to keep simulation logic clean and factories independently testable.

| File | Role |
|------|------|
| `entity_updates.py` | 10 factory functions (one per entity type) that construct typed Pydantic update models: `create_robot_update()`, `create_silica_cartridge_update()`, `create_cc_system_update()`, `create_evaporator_update()`, etc. Also provides `generate_robot_timestamp()` for spec-compliant timestamps (`YYYY-MM-DD_HH-MM-SS.mmm`). |
| `timing.py` | Delay calculation utilities: `calculate_delay(base_min, base_max, multiplier)` applies a random uniform distribution scaled by the speed multiplier with a floor. `calculate_cc_duration()` and `calculate_evaporation_duration()` compute long-running task durations from experiment parameters. `calculate_intermediate_interval()` divides total duration into evenly-spaced update windows. |
| `images.py` | Mock image URL generation: `generate_image_url()` builds MinIO-style paths (`{base_url}/{ws_id}/{device_id}/{component}/{timestamp}.jpg`), and `generate_captured_images()` creates a list of `CapturedImage` objects for multi-component photo tasks. |

**How it simulates the robot service:** The real robot captures images to MinIO and reports sensor data with hardware-derived timestamps. These generators produce structurally identical outputs — same URL patterns, same timestamp formats, same entity update shapes — using randomized but realistic values instead of actual hardware readings.

#### `scenarios/` — Failure and Timeout Injection

Controls whether a given task succeeds, fails with a realistic error, or silently times out. Enables chaos testing of LabRun's error-handling and retry logic.

| File | Role |
|------|------|
| `manager.py` | `ScenarioManager` decides the outcome for each incoming command. Checks `timeout_rate` first (random roll → no response published), then `failure_rate` (random roll or `default_scenario=failure` → error result), otherwise success. Priority: timeout > failure > success. |
| `failures.py` | Maps each `TaskName` to 4-5 realistic failure messages (e.g., `"Silica cartridge gripper malfunction"`, `"Pressure sensor reading abnormal"`). Each task has a 10-code error range (1010-1019 for setup_cartridges, 1020-1029 for setup_tube_rack, etc.). `get_random_failure()` returns a random (code, message) tuple. |

**How it simulates the robot service:** Real robots fail in unpredictable ways — gripper malfunctions, sensor errors, communication timeouts. The scenario system injects these failure modes probabilistically, producing the same error codes and message patterns that real robot failures would generate, allowing LabRun to test its recovery paths without physical hardware breakdowns.

#### `state/` — In-Memory World State Tracking

Maintains a consistent view of all entities (robot, devices, materials) so the mock server can validate preconditions and produce contextually accurate responses across a multi-step workflow.

| File | Role |
|------|------|
| `world_state.py` | Thread-safe in-memory store keyed by `(entity_type, entity_id)`. `apply_updates()` merges entity updates from completed tasks. `get_entity()` and `get_entities_by_type()` enable lookups. `reset()` clears all state (triggered by the `reset_state` special command). Used by simulators (entity ID resolution), heartbeat (current robot state), and precondition checker (validation). |
| `preconditions.py` | `PreconditionChecker` validates task-specific prerequisites against WorldState before execution. Examples: `setup_cartridges` fails if the ext module already has cartridges (code 2001), `terminate_cc` fails if CC isn't running (code 2030), `start_evaporation` fails if the flask isn't ready (code 2050). Returns structured `PreconditionResult(ok, error_code, error_msg)`. |

**How it simulates the robot service:** A real robot maintains physical state — cartridges are either mounted or not, the CC system is either running or idle. WorldState replicates this statefulness in memory, ensuring that command sequences produce the same precondition errors and state-dependent behaviors as a real robot. This catches workflow bugs (e.g., starting CC twice) without requiring physical equipment.

### Protocol Schema Management

The protocol types (enums, command parameters, result types) are defined in `src/schemas/protocol.py`. This is a self-contained copy of the types from the BIC Lab Service's `app/data/schemas/messages.py` and related enum modules.

**When the production protocol changes**, update `protocol.py` to match the new contract. The types that need to stay in sync:
- `TaskName`, `RobotState`, `EquipmentState`, `BinState` (enums)
- All `*Params` models (command parameters)
- `CapturedImage` (result metadata)

### Extending

**Add a new task type:**
1. Add the task name to `TaskName` enum in `schemas/protocol.py`
2. Define parameter model in `schemas/protocol.py`
3. Re-export from `schemas/commands.py`
4. Create a new simulator in `simulators/` (extend `BaseSimulator`)
5. Add entity update factory functions in `generators/entity_updates.py`
6. Add failure messages in `scenarios/failures.py`
7. Register the simulator in `main.py` and add param model mapping in `mq/consumer.py`

**Adjust timing:**
Modify base duration ranges in `generators/timing.py`. Each task has a `(min, max)` range; the `MOCK_BASE_DELAY_MULTIPLIER` scales all durations uniformly.

**Add new entity update types:**
1. Add the update model in `schemas/results.py` following the discriminated union pattern
2. Add it to the `EntityUpdate` union type
3. Add a factory function in `generators/entity_updates.py`

### Running Tests

```bash
uv run pytest src/tests/ -v
```

134 tests cover generators, scenarios, schemas, consumer integration, simulator integration, cleanup tasks, heartbeat, log producer, photo handling, preconditions, world state tracking, and full CC workflow.

## Case Study: Column Chromatography Workflow

This case study demonstrates a complete column chromatography workflow using the mock server, exercising all major task types and both quick and long-running simulation patterns.

### Scenario

An AI agent orchestrates a column chromatography experiment. The workflow consists of 8 sequential steps:

```
setup_cartridges -> setup_tube_rack -> take_photo -> start_cc
    -> terminate_cc -> fraction_consolidation -> start_evaporation
    -> collapse_cartridges
```

### Step 1: Setup Cartridges

The agent publishes a command to mount silica and sample cartridges at the work station:

```json
{
  "task_id": "task-001",
  "task_name": "setup_tubes_to_column_machine",
  "params": {
    "silica_cartridge_location_id": "shelf-A3",
    "silica_cartridge_type": "40g",
    "silica_cartridge_id": "sc-001",
    "sample_cartridge_location_id": "shelf-B1",
    "sample_cartridge_type": "standard",
    "sample_cartridge_id": "sac-001",
    "work_station_id": "ws-01"
  }
}
```

**Mock behavior:** 1.5-3s delay (at 0.1x multiplier). Returns `code: 200` with entity updates:
- Robot -> `idle` at `ws-01`
- Silica cartridge `sc-001` -> `mounted` at `ws-01`
- Sample cartridge `sac-001` -> `mounted` at `ws-01`
- CCS ext module -> `using`

### Step 2: Setup Tube Rack

```json
{
  "task_id": "task-002",
  "task_name": "setup_tube_rack",
  "params": {
    "tube_rack_location_id": "shelf-C2",
    "work_station_id": "ws-01",
    "end_state": "idle"
  }
}
```

**Mock behavior:** 1-2s delay. Returns tube rack -> `mounted`, robot -> `idle`.

### Step 3: Take Pre-Run Photo

```json
{
  "task_id": "task-003",
  "task_name": "take_photo",
  "params": {
    "work_station_id": "ws-01",
    "device_id": "cc-system-01",
    "device_type": "column_chromatography_system",
    "components": ["screen", "column"],
    "end_state": "idle"
  }
}
```

**Mock behavior:** 0.4-1.0s delay (2 components). Returns 2 `CapturedImage` entries with mock URLs and robot -> `idle`.

### Step 4: Start Column Chromatography (Long-Running)

```json
{
  "task_id": "task-004",
  "task_name": "start_column_chromatography",
  "params": {
    "work_station_id": "ws-01",
    "device_id": "cc-system-01",
    "device_type": "column_chromatography_system",
    "experiment_params": {
      "silicone_column": "40g",
      "peak_gathering_mode": "peak",
      "air_clean_minutes": 5,
      "run_minutes": 45,
      "need_equilibration": true,
      "left_rack": "10x75mm",
      "right_rack": "10x75mm"
    },
    "end_state": "wait_for_screen_manipulation"
  }
}
```

**Mock behavior (long-running pattern):**
1. Message is acknowledged immediately; simulation runs in a background asyncio task
2. **Initial intermediate update** (via `{robot_id}.log`): robot -> `watch_column_machine_screen`, CC system -> `running` with experiment params and ISO timestamp, cartridges -> `using`, tube rack -> `using`
3. **Periodic progress updates** (via `{robot_id}.log`): CC system -> `running` published every N seconds
4. **Final result** (via `{robot_id}.result`, `code: 200`): robot -> `wait_for_screen_manipulation`, CC system -> `running`

### Step 5: Terminate CC

```json
{
  "task_id": "task-005",
  "task_name": "terminate_column_chromatography",
  "params": {
    "work_station_id": "ws-01",
    "device_id": "cc-system-01",
    "device_type": "column_chromatography_system",
    "end_state": "idle"
  }
}
```

**Mock behavior:** 0.5-1s delay. Returns CC system -> `terminated`, cartridges -> `used`, tube rack -> `used`, plus a captured `screen` image.

### Step 6: Fraction Consolidation

```json
{
  "task_id": "task-006",
  "task_name": "fraction_consolidation",
  "params": {
    "work_station_id": "ws-01",
    "device_id": "cc-system-01",
    "device_type": "column_chromatography_system",
    "collect_config": [1, 1, 0, 1, 1, 0, 0, 1],
    "end_state": "moving_with_round_bottom_flask"
  }
}
```

**Mock behavior:** Delay scales with tube count (5 collected × 3s + 10s base = 25s × 0.1 ≈ 2.5s). Returns:
- Robot -> `moving_with_round_bottom_flask`
- Tube rack -> `used,pulled_out,ready_for_recovery`
- Round bottom flask -> `used,ready_for_evaporate`
- Left/right PCC chutes with positioning data

### Step 7: Start Evaporation (Long-Running)

```json
{
  "task_id": "task-007",
  "task_name": "start_evaporation",
  "params": {
    "work_station_id": "ws-01",
    "device_id": "evaporator-01",
    "device_type": "evaporator",
    "profiles": {
      "start": {
        "lower_height": 150.0,
        "rpm": 120,
        "target_temperature": 45.0,
        "target_pressure": 200.0
      },
      "stop": {
        "trigger": { "type": "time_from_start", "time_in_sec": 3600 }
      }
    },
    "post_run_state": "idle"
  }
}
```

**Mock behavior (long-running pattern):**
1. **Initial intermediate update** (via `{robot_id}.log`): robot -> `observe_evaporation`, evaporator -> `running=True` with ambient values (`current_temperature=25.0C`, `current_pressure=1013.0 mbar`)
2. **Periodic ramp updates** (via `{robot_id}.log`): evaporator readings linearly interpolate toward targets (temperature: 25C -> 45C, pressure: 1013 -> 200 mbar)
3. **Final result** (via `{robot_id}.result`, `code: 200`): evaporator -> `running=False`, `current_temperature=45.0`, `current_pressure=200.0`, robot -> `idle`

### Step 8: Collapse Cartridges

```json
{
  "task_id": "task-008",
  "task_name": "collapse_cartridges",
  "params": {
    "work_station_id": "ws-01",
    "silica_cartridge_id": "sc-001",
    "sample_cartridge_id": "sac-001",
    "end_state": "idle"
  }
}
```

**Mock behavior:** 1-1.5s delay. Returns cartridges -> `used` (ready for disposal), CCS ext module -> `used`, robot -> `idle`.

**Prerequisite:** Robot must be `idle`. If step 7 used `post_run_state: "observe_evaporation"`, run `stop_evaporation` first.

### Testing Error Handling

Inject failures to test the main service's error recovery:

```bash
# 20% of tasks fail with realistic robot errors
MOCK_FAILURE_RATE=0.2 uv run python -m src.main

# All tasks timeout (no response published)
MOCK_DEFAULT_SCENARIO=timeout uv run python -m src.main

# Fast iteration: 100x speed + 10% failure rate
MOCK_BASE_DELAY_MULTIPLIER=0.01 MOCK_FAILURE_RATE=0.1 uv run python -m src.main
```

Example failure result for `setup_cartridges`:
```json
{
  "code": 1012,
  "msg": "Silica cartridge gripper malfunction: unable to secure cartridge",
  "task_id": "task-001",
  "updates": []
}
```

### Key Observations

1. **Quick vs. long-running**: Tasks like `setup_cartridges` (15-30s) block the consumer until complete, while `start_cc` and `start_evaporation` run in background asyncio tasks — the consumer immediately acknowledges the message and can process other commands concurrently.

2. **Intermediate updates via log channel**: Long-running tasks publish entity state changes in real-time via `{robot_id}.log`, allowing the main service to update its database incrementally. Final results go via `{robot_id}.result`.

3. **Timing fidelity**: At `MOCK_BASE_DELAY_MULTIPLIER=0.01`, a 45-minute CC run completes in ~27 seconds. At `1.0`, it takes the full 45 minutes. This enables both fast CI testing and realistic integration testing.

4. **Scenario injection**: `MOCK_FAILURE_RATE` and `MOCK_TIMEOUT_RATE` apply per-message random injection, while `MOCK_DEFAULT_SCENARIO` sets a global default. This allows testing specific error paths or general resilience.

5. **WorldState preconditions**: The server validates entity states before execution, returning 2000-series error codes for precondition violations. This catches workflow errors (e.g., starting CC when already running) without needing the real BIC Lab Service validation.
