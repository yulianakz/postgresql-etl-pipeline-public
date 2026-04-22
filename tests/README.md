# Tests

Unit tests for the Flask application (`flask_app/`) and the ETL pipeline
(`etl/`). Everything runs without a database, without Airflow, and without
a live HTTP service — dependencies are replaced by in-memory fakes or
mocks.

## Layout

```
tests/
├── flask_app_tests/
│   ├── conftest.py               # app + client + JWT header + mock_services fixtures
│   ├── test_logging_config.py    # configure_logging() unit tests
│   ├── api_layer/                # HTTP-level tests (flask-smorest routes)
│   ├── service_layer/            # business-logic tests with fake repos
│   └── db_layer/                 # PostgreSQL repo tests with a fake SQLAlchemy engine
└── etl_flow_tests/
    ├── conftest.py               # stubs the `airflow` package so ETL imports work
    ├── domain/                   # mappers, entities, utilities, broken-row logger
    ├── extractors/               # CSV / DB / API extractors + factory
    ├── services/                 # ApiAuthClient + ExtractService
    ├── repositories/             # stg / core / metadata Postgres repos
    ├── runners/                  # staging + core runner template & concrete runners
    └── test_sql_loader.py        # SQL file loader helper
```

Run everything:

```bash
pytest tests
```

Run a single layer:

```bash
pytest tests/flask_app_tests/api_layer
pytest tests/etl_flow_tests/runners
```

Counts at time of writing: **214 Flask tests** + **171 ETL tests** =
**385 tests**.

## Shared conventions

- **No real database.** Repository tests use a lightweight fake SQLAlchemy
  engine (`_fake_engine.py`) that records executed statements and lets
  tests control what `scalar() / scalar_one() / scalar_one_or_none() /
  rowcount` return.
- **No real HTTP.** Tests that touch `requests` monkeypatch
  `requests.post` / `requests.get` and return a `SimpleNamespace` response
  object.
- **No real Airflow.** `tests/etl_flow_tests/conftest.py` installs a stub
  `airflow.exceptions.AirflowSkipException` into `sys.modules` before any
  ETL module is imported. The runner templates that `raise
  AirflowSkipException` therefore work without Apache Airflow installed.
- **API tests use `mock_services`.** The fixture in
  `tests/flask_app_tests/conftest.py` swaps every `MethodView`'s service
  attribute for a `MagicMock` so API tests exercise routing / auth /
  serialization without running real business logic.
- **JWT headers.** `admin_headers` and `guest_headers` produce valid
  tokens for role-gated endpoints using `flask_jwt_extended.create_access_token`.
- **marshmallow-dataclass quirk.** Required fields declared as
  `load_only=True` on a `@dataclass` schema raise `TypeError` (not
  `ValidationError`) when missing on some versions of
  `marshmallow-dataclass`. Tests handle this in two ways:
  1. The schema-level suite uses a `_assert_invalid_payload` helper that
     accepts both `ValidationError` and `TypeError`.
  2. The API-layer suite probes the 422 path by sending an **unknown**
     field rather than omitting a required one — this goes through the
     normal `ValidationError` branch that `flask-smorest` maps to 422.

---

## Flask app tests — `tests/flask_app_tests/`

### `conftest.py`

Sets dummy env vars (`JWT_SECRET_KEY`, Postgres connection variables) *before*
`create_app()` runs, then exposes:

- `app` (session-scoped Flask app, `TESTING=True`),
- `client` (Flask test client),
- `mock_services` — replaces every API view's `*_service` attribute with
  a `MagicMock` and restores the originals on teardown,
- `admin_headers`, `guest_headers` — `Authorization: Bearer ...` dicts.

### `test_logging_config.py`

Covers `flask_app/logging_config.py::configure_logging`. Each test
redirects `LOG_DIR` / `CSV_LOG_FILE` to `tmp_path`, resets the
module-level `_configured` guard, and restores the `csv_loader` logger's
original handlers on teardown so process-wide logging state stays clean.

- creates the log directory if it doesn't exist,
- attaches exactly one `FileHandler` pointing at `CSV_LOG_FILE`,
- sets the `csv_loader` logger to `WARNING` and disables propagation,
- `logger.warning(...)` actually writes to the file with the configured
  `[LEVEL] message` format,
- the one-time `_configured` guard prevents duplicate handlers when
  `configure_logging()` is called repeatedly,
- the guard flag starts `False` and flips to `True` after the first call.

### `api_layer/`

HTTP-level tests that go through `flask-smorest` routing, schema validation
and `@auth_decorators`. Status codes covered: 200, 201, 400, 401, 403, 422.

- **`test_schemas.py`** — direct `schema.load(...)` tests for
  `LoginInputSchema`, `RegisterInputSchema`, `BabyInputSchema`,
  `DiaperInputSchema`, `SleepInputSchema`:
  - happy-path loads return the dataclass instance with correct types,
  - unknown fields raise `ValidationError`,
  - required fields missing raise either `ValidationError` or `TypeError`
    (handled by `_assert_invalid_payload`),
  - wrong types (string for int, bad ISO datetime, int for status) raise
    `ValidationError`.
- **`test_auth_api.py`** — `/auth/register`, `/auth/login`:
  - 201 on successful registration (service mocked to return the created
    user),
  - 401 on bad credentials (`ValueError` from service → 401),
  - 422 when the payload contains an unknown field,
  - role enforcement: admin-only register endpoints reject guests.
- **`test_baby_api.py`** — `/baby` GET/POST/PUT/DELETE:
  - auth required (401 without token),
  - admin-only endpoints reject guest tokens (403),
  - 201 on create, 200 on get/update/delete,
  - 400 when the service raises `ValueError` (e.g. duplicate),
  - 422 for schema violations (unknown fields / bad payloads).
- **`test_sleep_api.py`** — `/sleep` endpoints:
  - 201 create / 200 list / 200 update / 200 delete,
  - 400 on service-layer `ValueError` (invalid duration, future date),
  - 422 on schema errors.
- **`test_diaper_api.py`** — `/diaper` endpoints: same axes as sleep.

### `service_layer/`

Pure business-logic tests using in-memory fake repositories. Each service
is tested for happy path + every input validation rule the service layer
actually performs.

- **`test_baby_service.py`** — `BabyService`:
  - `create`: name length, trimmed whitespace, required timezone, IANA
    format, duplicate check via repo,
  - `update`: partial updates, missing record raises `ValueError`,
  - `delete`: success and missing-id error,
  - `list` and `get_by_id` delegation.
- **`test_sleep_service.py`** — `SleepService`:
  - duration must be positive, cannot be `None`, must fit `int` range,
  - `sleep_start` cannot be in the future,
  - baby must exist (checked via baby repo),
  - update/delete success and not-found errors.
- **`test_diaper_service.py`** — `DiaperService`:
  - status is one of the allowed enum values,
  - `change_time` cannot be in the future,
  - baby must exist,
  - update/delete flows mirror sleep.
- **`test_user_service.py`** — `UserService`:
  - create stores the hashed password (never the plaintext),
  - username uniqueness,
  - `get_by_user_name` returns `None` when missing,
  - role defaults to `guest`.
- **`test_auth_service.py`** — `AuthService`:
  - `login` returns a JWT for valid credentials, raises `ValueError` for
    bad username / bad password,
  - `register` delegates to `UserService` with a hashed password and
    forwards role,
  - tokens encode the expected claims (`identity` + `role`).

### `db_layer/`

PostgreSQL repository tests using `_fake_engine.py` (a minimal
Engine/Connection/Result stand-in). They validate the SQLAlchemy
statements that would be sent to Postgres and the row-to-entity mapping
(`_to_entity`), without touching a real database.

- **`_fake_engine.py`** — `FakeEngine`, `FakeConnection`, `FakeExecResult`
  used by every repo test in this folder.
- **`test_postgres_baby_repo.py`** — select/insert/update/delete for
  `baby_info`, row-to-entity mapping, `NULL` handling.
- **`test_postgres_sleep_repo.py`** — `sleep_data` CRUD + filtering by
  baby id.
- **`test_postgres_diaper_repo.py`** — `diaper_data` CRUD.
- **`test_postgres_user_repo.py`** — `users` CRUD, `get_by_user_name`.

---

## ETL tests — `tests/etl_flow_tests/`

### `conftest.py`

Registers a minimal stub for the `airflow` package *before any ETL module
is imported* so the runner templates (which only use
`AirflowSkipException`) can run in a plain Python environment.

### `domain/`

- **`test_utils.py`** — `safe_int`, `safe_datetime`, `safe_str`,
  `_normalize`:
  - happy paths and whitespace trimming,
  - blanks / `None` → `None`,
  - every common datetime format supported,
  - invalid inputs raise `MapperError` with the original error attached.
- **`test_entities_mappers.py`** — one class per mapper:
  - `BabyDataEntityMapper.api_baby_mapper` / `db_baby_mapper`,
  - `DiaperDataEntityMapper.api_diaper_mapper` (explicit `baby_id` and
    fallback from row) + `db_diaper_mapper`,
  - `SleepDataEntityMapper.api_sleep_mapper` / `db_sleep_mapper`,
  - `FormulaDataEntityMapper.csv_formula_mapper` (CSV headers `ID`,
    `Time`, `Amount (ml)`, `Baby ID`),
  - verifies mapped fields and that invalid inputs propagate as
    `MapperError`.
- **`test_extract_entities.py`** — `BaseEntity.row_hash`:
  - auto-computed when not provided,
  - preserved when provided,
  - identical for equal business content,
  - changes when business fields change,
  - **unaffected** by `job_id` / `loaded_at` (the `META_FIELDS` set).
  - `FormulaDataEntity.__post_init__`: default `baby_id = 1`, derived
    `source_id` SHA256 prefix, explicit `source_id` preserved.
- **`test_broken_rows_logger.py`** — `log_bad_row` writes JSONL to
  `LOG_FILE`, creates the directory if missing, appends on subsequent
  calls.
- **`test_exceptions.py`** — `MapperError` stores value / expected_type /
  original_error / optional row, and its message includes all three.

### `extractors/`

- **`test_csv_extractor.py`** — happy path, empty file, broken rows
  wrapped in `BrokenEntity`, missing file raises `FileNotFoundError`, UTF-8
  BOM is stripped by `utf-8-sig`.
- **`test_db_extractor.py`** — fake engine + connection verify:
  `stream_results=True`, params forwarded, broken rows wrapped in
  `BrokenEntity`, empty result yields nothing.
- **`test_api_extractor.py`** — `requests.get` + `ijson.items`
  monkeypatched to verify: URL concatenation, auth + extra headers merge,
  `params` and `stream=True`, broken rows wrapped, HTTP errors propagate
  via `raise_for_status()`.
- **`test_extract_factory.py`** — `ExtractorFactory.get_extractor`
  returns the correct extractor class for `"csv"`, `"db"`, `"api"`, is
  case-insensitive, and raises `ValueError("Unsupported source type")`
  for unknown types.

### `services/`

- **`test_auth_client.py`** — `ApiAuthClient`:
  - login stores the `access_token`,
  - HTTP error → `AuthError` (status code preserved, token stays `None`),
  - missing token key in response → `AuthError`,
  - `.headers` raises `AuthError` before login,
  - `AuthError.__str__` includes URL + status code + original error.
- **`test_extract_service.py`** — `ExtractService.extractor_run`:
  - iterates `extractor.extract()` once,
  - forwards `job_id`, `entity_type`, and the full entity stream to
    `repo.chunk_load`,
  - returns the repo's rows-loaded count.

### `repositories/`

- **`_fake_engine.py`** — `FakeEngine` (`begin()` and `connect()` context
  managers), `FakeConnection` (records `(stmt, params)`), `FakeResult`
  (configurable `scalar` / `scalar_one` / `scalar_one_or_none` /
  `rowcount`).
- **`test_stg_postgres_repo.py`** — `StgPostgresRepository`:
  - `_get_table` resolves every entity type, raises on unknown types,
  - `do_truncate` compiles to
    `TRUNCATE TABLE staging.<table>`,
  - `chunk_load` happy path (single flush), chunked flushes at
    `chunk_size`, `None` entries skipped, `BrokenEntity` entries logged
    (via monkeypatched `log_bad_row`) and excluded from inserts,
  - `job_id` and `loaded_at` are written back onto each entity,
  - empty iterator does not execute anything,
  - unknown entity type raises `ValueError`.
- **`test_core_postgres_repo.py`** — `CorePostgresRepository`:
  - `_get_table` lookup and `ValueError` on unknown names,
  - `do_truncate` compiles to `TRUNCATE TABLE core.<table>`,
  - `raw_sql_load` splits statements with `sqlparse.split`, sums positive
    `rowcount` values, ignores zero/negative rowcounts, empty SQL returns
    `0` with no execution, `params` default to `{}`.
- **`test_meta_postgres_repo.py`** — `MetadataPostgresRepository`:
  - `start_job` returns the inserted `job_id` via `scalar_one`,
  - `add_job_metadata` executes one update,
  - `finish_job` accepts `success` / `failed`, rejects other strings with
    `ValueError`, and raises `RuntimeError` when `rowcount == 0` (called
    before `start_job`),
  - `dedup_job_done`, `find_running_job`, `is_file_loaded`,
    `get_last_successful_job_id` return the expected scalar and handle
    `None`.

### `runners/`

- **`test_stg_runner_template.py`** — `StagingExtractRunnerTemplate`:
  - builds a minimal concrete `_Runner` subclass and drives the full
    `extract_run` flow with in-memory `_FakeMetaRepo` / `_FakeStgRepo`,
  - asserts the sequence of meta calls: `dedup_job_done` → `find_running_job`
    → `start_job` → `add_job_metadata` → `finish_job`,
  - `full_reload` truncates the staging table first; `initial` does not,
  - existing running job id is reused (no extra `start_job`),
  - dedup-hit short-circuits before any metadata is written,
  - CSV incremental with "file already loaded" raises
    `AirflowSkipException`; the job record is still closed in `finally`
    with `status=None`, and `add_job_metadata` is **not** called,
  - an exception inside `_extracting` marks the job `failed`, embeds the
    step tag (`[step=extract] ...`) in the error message, and re-raises.
- **`test_core_runner_template.py`** — `CoreExtractRunnerTemplate`:
  - happy path: truncate + `raw_sql_load` + `finish_job(success, rows)`,
  - `initial` and `full_reload` both truncate; `incremental` does not,
  - parent `job_id` resolution uses the staging source path's last
    segment, pipeline_stage `"extract"`,
  - `full_reload` skips parent-job lookup and writes `parent_job_id=None`
    into `add_job_metadata`,
  - dedup-hit short-circuits before any SQL runs,
  - `None` rows_affected normalized to `0`,
  - exception in `raw_sql_load` marks the job `failed`, re-raises, and
    embeds `[step=transform_load]` in the error message.
- **`test_concrete_runners.py`** — smoke tests for every concrete runner:
  - **Staging initial:** `BabyStgFullExtractRunner`,
    `SleepStgFullExtractRunner`, `FormulaStgFullExtractRunner`,
    `DiaperStgFullExtractRunner`.
  - **Staging incremental:** `BabyStgIncrementalExtractRunner`,
    `SleepStgIncrementalExtractRunner`,
    `DiaperStgIncrementalExtractRunner`,
    `FormulaStgIncrementalExtractRunner`.
  - **Core initial:** `BabyCoreInitialExtractRunner`,
    `DateCoreInitialExtractRunner`, `TimeCoreInitialExtractRunner`,
    `DiaperStatusCoreInitialExtractRunner`,
    `DiaperDataCoreInitialExtractRunner`,
    `SleepDataCoreInitialExtractRunner`,
    `FormulaDataCoreInitialExtractRunner`.
  - **Core incremental:** `BabyCoreIncrementalExtractRunner`,
    `DiaperCoreIncrementalExtractRunner`,
    `DiaperStatusCoreIncrementalExtractRunner`.
  - Asserts that every runner returns the correct constants
    (`pipeline_stage`, `source_type`, `source_path`,
    `destination_table_name`, `load_type`, `entity_type`).
  - `build_extractor` returns the right extractor class (CSV vs DB),
    the formula-incremental runner's `source_path` targets a fixed CSV
    file, and `DiaperStgFullExtractRunner.build_extractor` raises
    `NotImplementedError` (it uses a custom per-baby loop).
  - Every core runner's `get_sql()` loads a non-empty SQL template and
    `get_sql_params(job_id)` forwards the `job_id` (or returns `None`
    for dimension runners that don't need it).

### `test_sql_loader.py`

- `load_sql` reads an existing SQL file relative to `etl/sql/`,
- missing paths raise `FileNotFoundError`.
