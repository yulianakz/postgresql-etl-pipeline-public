# Baby Data Platform — Flask API + Airflow ETL → Postgres DWH

A small end-to-end data platform I built to practice the full path from an **operational REST API** to an **analytics-ready data warehouse**: collect baby-care events (sleep, diapers, formula feeds) through a Flask service, and load them into a Kimball-style star schema in Postgres using an Apache Airflow pipeline.

The project is intentionally split into **two independent flows** that meet in the same Postgres instance — so the same data can be served transactionally by the app and analytically by the warehouse.

---

## Architecture

```
                      ┌──────────────────────────┐
                      │  Flask REST API (web)    │
  Client / CSV ──────►│  JWT auth, CRUD, OpenAPI │◄──── Swagger UI
                      │  SQLAlchemy Core         │
                      └────────────┬─────────────┘
                                   │  public.* (OLTP)
                                   ▼
                          ┌────────────────┐
                          │   Postgres     │
                          │  baby_data_db  │
                          └────────┬───────┘
                                   │
                                   │ extract (db / api / csv)
                                   ▼
                      ┌──────────────────────────┐
                      │   Apache Airflow DAGs    │
                      │   (initial + incremental)│
                      └────────────┬─────────────┘
                                   │ staging.*  →  core.*
                                   ▼
                          ┌──────────────────┐
                          │  Star schema     │
                          │  (facts + dims)  │
                          └──────────────────┘
```

Everything is containerized with **Docker Compose**: two Postgres instances (app DB + Airflow metadata DB), the Flask service, and the Airflow init / webserver / scheduler stack.

---

## Flow 1 — Flask operational API

The transactional side of the platform. It owns the raw business data.

**What it does**
- Exposes a REST API for managing babies, sleep sessions, diaper changes and the users who access them.
- Handles authentication with JWT (access + refresh tokens) and two roles (`ADMIN`, `GUEST`) enforced per-endpoint.
- Auto-generates an OpenAPI 3 spec and a Swagger UI.
- On first boot, seeds a demo baby from bundled CSV files so the rest of the stack has something to work with.

**Layered design**

```
api/ (blueprints, schemas)  ──►  application/ (services)  ──►  db/ (repositories)  ──►  Postgres
```

Each layer only knows about the one below it. Services contain the business rules, repositories contain the SQL, and routes just translate HTTP ↔ service calls.

**Technologies**
- **Flask** + **flask-smorest** — routing, OpenAPI, Swagger UI.
- **flask-jwt-extended** — access / refresh tokens, `@jwt_required` guards.
- **passlib[argon2]** — password hashing.
- **marshmallow** + **marshmallow-dataclass** — request/response validation and serialization.
- **SQLAlchemy 2.x Core** (not the ORM) — explicit `Table` definitions, composable `insert/select/update/delete` statements.
- **psycopg2** — Postgres driver.
- **Alembic** — schema migrations for the warehouse side.

**Patterns I used**
- **Layered architecture** (API → Service → Repository → DB).
- **Repository pattern** behind explicit interfaces (`BabyRepository`, `SleepRepository`, …) — services depend on the interface, not on Postgres.
- **Service layer** as the single place where business rules live (validation, timezone checks, authorization).
- **DTO via dataclasses** for request payloads (marshmallow-dataclass).
- **Decorator-based authorization** (`@admin_required`, `@all_roles_allowed`) on top of JWT.

---

## Flow 2 — Airflow ETL → Postgres data warehouse

The analytical side. It treats the Flask DB and external sources as raw inputs and builds a clean, conformed star schema on top.

**What it does**
- Pulls data from **three source types** — the Flask REST API (diapers), the operational Postgres tables (babies, sleep), and a daily CSV drop (formula feeds).
- Lands everything into a `staging` schema with raw types, a row hash and job lineage columns.
- Transforms staging into a `core` schema (dimensions + facts) with hand-written, parameterized SQL.
- Tracks every run in a `metadata.etl_job` table (dag_id, task_id, logical_date, status, rows loaded, error, parent job id).
- Supports both an **initial full load** (`@once`) and a **daily incremental load** (`0 1 * * *`) with the same abstractions.

**The pipeline in one picture**

```
source (db / api / csv)
        │  Extractor (streaming: ijson / stream_results / DictReader)
        ▼
   staging.*  ──►  core.dim_*  ──►  core.fact_*
                       (SCD2 / SCD0 / junk dim)   (conformed surrogate keys)
```

**Warehouse model (Kimball star)**
- `dim_baby` — **SCD Type 2** on timezone changes (`valid_from`, `valid_to`, `is_current`, unknown row `baby_nk = -1`).
- `dim_date`, `dim_time` — generated reference dims (SCD0), `YYYYMMDD` / `HHMM` surrogate keys.
- `dim_diaper_status` — junk dimension.
- `fact_sleep`, `fact_diaper`, `fact_formula_feed` — one row per business event, conformed `baby_sk` + date/time keys, `job_id` + `loaded_at` for lineage.

**Technologies**
- **Apache Airflow 2.9** (LocalExecutor) — DAGs, pools, task retries, `on_failure_callback`.
- **Airflow providers** — `postgres` (connection + `PostgresHook.get_sqlalchemy_engine`), `http` (connection for the API extractor).
- **SQLAlchemy Core** for staging inserts and table metadata.
- **ijson** — streaming JSON parse of API responses (so a large payload doesn't load into memory).
- **requests** — authenticated calls to the Flask API (reuses the same JWT flow).
- **pendulum** — timezone-aware datetimes everywhere in the pipeline.
- **psycopg2** + hand-written SQL for the transform step.
- **Alembic** — versioned migrations for the `staging`, `core`, and `metadata` schemas.

**Patterns I used**
- **Template Method** — `StagingExtractRunnerTemplate` / `CoreExtractRunnerTemplate` define the run skeleton (dedup check → start job → write metadata → do work → finalize in `finally`). Each entity fills the slots.
- **Abstract Factory** — `ExtractorFactory` maps `"csv" | "api" | "db"` to concrete extractor classes so a runner only asks for a source *kind*, not a specific implementation.
- **Strategy via abstract hooks** — per-runner overrides of `get_sql`, `load_type`, `source_type`, `mapper`, `build_extractor`.
- **Repository pattern** again, split by responsibility: `StgPostgresRepository` (chunked inserts + broken-row logging), `CorePostgresRepository` (SQL execution + truncate), `MetadataPostgresRepository` (job lifecycle).
- **Idempotency + dedup** — `(dag_id, task_id, logical_date)` uniquely identifies a logical run; re-running a succeeded task raises `AirflowSkipException`.
- **Parent-job linkage** — each core load records which staging job produced the rows it consumed, so lineage is queryable.
- **Separation of bad rows** — `BrokenEntity` objects travel through the same pipeline and get written to a side log, so a single malformed row never fails a whole batch.
- **Orchestration gates** — `stg_tasks >> stg_done >> dim_tasks >> dim_done >> fact_tasks` using `EmptyOperator` to make dependencies readable.

---

## Optimizations done (indexes, SQL, data model)

A focused performance pass on the warehouse side. Each row below lists one concrete change, the query/plan it affected, and the complexity change it produced.

### Indexes

| Index | Before → After |
|---|---|
| `idx_dim_baby_current` (UNIQUE, partial `WHERE is_current=TRUE`) | seq scan of `dim_baby` → `O(log n)` index probe |
| `idx_dim_baby_nk_validity` | seq scan per event → `O(log n)` seek + tiny range filter |
| `idx_etl_job_dedup_lookup` | full-table `EXISTS` → `O(1)` index probe |
| `idx_etl_job_latest_success` | partial match + sort + `LIMIT 1` → `O(1)` backward index scan |
| `idx_etl_job_source_path_success` (partial `WHERE status='success'`) | seq scan per file → `O(1)` index probe, small on-disk |

### SQL / data model changes

| # | Change | Before → After |
|---|---|---|
| 6 | Range-partitioned fact tables by month on `*_date_sk` (monthly partitions + default) | Full-table scan on date filters → partition pruning (`O(months_touched)`); retention drop goes from `DELETE + VACUUM` to `O(1) DROP TABLE` |
| 7 | SCD2 range join in **initial** fact loads (was `is_current=TRUE`; now uses both range and `is_current`) | Initial and incremental now share one semantics; historically correct `baby_sk` on backfills, and the join uses index #2 |
| 8 | Incremental watermark moved into `metadata.etl_job.last_loaded_event_ts_watermark` | `SELECT MAX(col) FROM staging.*` (`O(n)` over growing staging) → single-row lookup via index #4 (`O(1)`) |
| 9 | Staging incremental SQL parameterized with `:watermark_ts` | No `MAX()` CTE over staging; handles first run naturally (`:watermark_ts IS NULL`) |
| 10 | Staging chunk insert switched to executemany | One inlined `INSERT … VALUES (…,…,…)` per chunk (risked the 65535 bind-param cap, heavy plan cache) → batched parameterized executemany |

---

## What this project demonstrates

- Designing two **independent but interoperable** systems (OLTP + OLAP) over the same database.
- Writing clean layers with **explicit interfaces**, so the services don't care whether data comes from Postgres, an API, or a CSV.
- Reasoning about **data-warehouse modeling** — star schema, conformed dimensions, SCD2, surrogate vs natural keys, fact grain.
- Building a pipeline that is **observable** (job metadata + lineage) and **safe to re-run** (dedup + skip + parent-job linkage).
- Handling **real-world data quality**: streaming large payloads, isolating broken rows, and chunked bulk inserts.
- Packaging everything in **Docker Compose** so it runs with a single command.

---

## Project structure

```
flask_app/           # Flow 1 — REST API
  api/               #   blueprints + marshmallow schemas + auth decorators
  application/       #   services + CSV import
  domain/            #   entities (Baby, Sleep, Diaper, User)
  db/                #   repositories, repository interfaces, table metadata, engine

etl/                 # Flow 2 — ETL code
  extract/           #   extractors (csv/api/db), mappers, entities, auth client
  transform_load/    #   template for core runners
  runners/           #   per-entity runners (stg + core, initial + incremental)
  db/                #   repositories, tables (staging/core/metadata), schemas
  sql/               #   hand-written SQL (organized by stg/core × initial/incremental)
  alembic/           #   migrations for staging/core/metadata schemas

airflow/dags/        # DAG definitions (initial + incremental)
fake_data/           # Fake incremental data generator for end-to-end testing
requirements/        # Separate pinned deps for flask vs etl
docker-compose.yml   # Postgres x2, Flask web, Airflow init/webserver/scheduler
```

---

## Running it locally

```bash
# 1. create a .env file with POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB / POSTGRES_HOST / POSTGRES_PORT
cp .env.example .env    # then edit

# 2. bring the stack up
docker compose up --build

# 3. open:
#    Flask API + Swagger UI  →  http://localhost:5000/swagger-ui
#    Airflow UI              →  http://localhost:8080   (admin / admin)

# 4. trigger the DAGs from the Airflow UI:
#    - initial_etl      (one-shot: public → staging → core)
#    - incremental_etl  (daily at 01:00 UTC)
```

The first time the Flask container boots it auto-imports a demo baby ("Adriana") from the bundled CSV files, so the DAGs have something to extract.

---

