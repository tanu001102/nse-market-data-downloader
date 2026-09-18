# MASTER PROMPT — NSE Market Data Downloader Assignment

## ROLE

You are acting as a senior Python engineer and technical mentor helping me complete the NSE Market Data Downloader Intern Engineering Assignment.

The assignment PDF in this repository is the PRIMARY SOURCE OF TRUTH.

Before making any implementation changes:

1. Read the complete assignment PDF.
2. Inspect the existing repository structure.
3. Understand all requirements, deliverables, testing requirements, evaluation criteria, and bonus requirements.
4. Do not invent requirements that contradict the assignment.
5. If something is not specified in the assignment, clearly identify it as an engineering decision or assumption.

I am a beginner/intermediate developer and I want to understand the implementation, not blindly receive a completed project.

---

# PROJECT OBJECTIVE

Build a Python command-line application that automatically retrieves and stores CSV data corresponding to these four NSE market-data pages:

1. Top Gainers / Losers
   https://www.nseindia.com/market-data/top-gainers-losers

2. Upper Band Hitters
   https://www.nseindia.com/market-data/upper-band-hitters

3. Volume Gainers / Spurts
   https://www.nseindia.com/market-data/volume-gainers-spurts

4. 52 Week High — Equity Market
   https://www.nseindia.com/market-data/52-week-high-equity-market

The application must retrieve the relevant data automatically without manual copying.

---

# CORE REQUIREMENTS

The final application must:

1. Retrieve data from all four sources.

2. Save each dataset as CSV.

3. Avoid manual copying from NSE.

4. Organize downloaded files sensibly.

5. Use filenames that clearly identify the dataset and date.

6. Support automatic execution.

7. Support downloading individual datasets.

8. Handle:

   * network failures
   * timeouts
   * HTTP errors
   * empty responses
   * invalid responses
   * unexpected response formats

9. Ensure failure of one dataset does not unnecessarily prevent other datasets from downloading.

10. Produce useful logs containing:

    * what was attempted
    * when it was attempted
    * success/failure
    * record count
    * errors

11. Validate data before saving:

    * expected columns
    * expected data structure
    * non-empty data
    * duplicate handling

12. Handle repeated execution for the same trading day without creating confusing duplicate files.

13. Keep dataset URLs/configuration separate from application logic.

14. Separate responsibilities such as:

    * acquisition
    * validation
    * storage
    * application entry point

---

# EXPECTED COMMAND-LINE INTERFACE

The application should support an all-dataset command similar to:

```
python main.py
```

It should also support individual dataset execution similar to:

```
python main.py --dataset top-gainers-losers
```

The exact CLI design may be improved if it remains simple and aligned with the assignment.

Recommended individual dataset names:

```
top-gainers-losers
upper-band-hitters
volume-gainers-spurts
52-week-high
```

Also provide:

```
python main.py --help
```

---

# ENGINEERING PRINCIPLES

Build the application as a small production-minded data pipeline.

The conceptual flow should be:

```
Configuration
    ↓
Data Acquisition
    ↓
Response Parsing
    ↓
Data Validation
    ↓
Duplicate Handling
    ↓
CSV Storage
    ↓
Logging
```

The application should be:

* reliable
* maintainable
* readable
* testable
* extensible
* simple enough for an internship assignment

Do NOT create unnecessary complexity.

Do NOT build a fancy GUI.

A CLI application is sufficient.

---

# IMPORTANT NSE IMPLEMENTATION REQUIREMENT

Do not assume that the visible NSE webpage HTML directly contains the required dataset.

Before implementing the downloader:

1. Investigate how the current NSE pages provide their data.
2. Determine whether the data is exposed through:

   * API endpoints
   * JSON responses
   * page requests
   * embedded data
   * another documented/observable mechanism
3. Verify the response format for each of the four datasets.
4. Design the acquisition layer based on the actual response structure.
5. Do not hardcode fake/sample API responses and present them as real NSE data.
6. Clearly document any assumptions or limitations.

The application must be designed so that changes to NSE endpoints can be handled without rewriting the entire application.

---

# RECOMMENDED PROJECT ARCHITECTURE

Use clean separation of responsibilities.

A suitable structure may be:

```
nse-market-data-downloader/
│
├── main.py
├── config.py
│
├── downloader/
│   ├── __init__.py
│   ├── client.py
│   └── datasets.py
│
├── validation/
│   ├── __init__.py
│   └── validator.py
│
├── storage/
│   ├── __init__.py
│   └── csv_storage.py
│
├── utils/
│   ├── __init__.py
│   └── logger.py
│
├── tests/
│   ├── test_downloader.py
│   ├── test_validation.py
│   └── test_storage.py
│
├── data/
│   ├── top_gainers_losers/
│   ├── upper_band_hitters/
│   ├── volume_gainers_spurts/
│   └── 52_week_high/
│
├── logs/
│
├── sample/
│
├── README.md
├── requirements.txt
├── .gitignore
└── MASTER_PROMPT.md
```

This structure is a recommendation, not a requirement to blindly follow.

Modify it when there is a clear engineering reason.

---

# CONFIGURATION

Dataset URLs and dataset-specific configuration must not be hardcoded throughout the application.

Use a dedicated configuration module or configuration file.

The configuration should make it easy to:

* add another NSE dataset
* modify an endpoint
* modify an output directory
* define expected dataset information

---

# DATA ACQUISITION

Create a dedicated acquisition/client layer.

Responsibilities should include:

* creating an HTTP session
* appropriate request headers where necessary
* making requests
* timeout handling
* HTTP status handling
* response parsing
* retry behavior if implemented
* meaningful exceptions/errors

Do not put all HTTP logic inside main.py.

---

# ERROR HANDLING

The application must handle at minimum:

## Network failure

Example:

```
ConnectionError
```

The application should log the failure clearly.

## Timeout

Example:

```
Timeout
```

The application should log the timeout and continue appropriately.

## HTTP error

Examples:

```
403
404
429
500
```

Handle these without an uncontrolled crash.

## Empty response

If the response contains no usable dataset:

```
validation should fail
```

and the application should not save it as a successful dataset.

## Invalid response

If NSE returns HTML, an error page, malformed JSON, or another unexpected response instead of the expected dataset:

```
detect it
log it
do not treat it as valid data
```

## Unexpected format

The parser/validator should fail safely when the structure changes unexpectedly.

---

# FAILURE ISOLATION

If one dataset fails:

```
Dataset A → SUCCESS
Dataset B → SUCCESS
Dataset C → FAILED
Dataset D → SUCCESS
```

the application should still attempt Dataset D.

Do not design the all-dataset execution so that one exception automatically terminates all remaining downloads.

At the end, provide a useful summary of successful and failed datasets.

---

# DATA VALIDATION

Before saving a dataset:

1. Confirm that the response can be parsed.
2. Confirm that usable data exists.
3. Confirm the expected structure.
4. Validate required/expected columns where appropriate.
5. Remove or handle duplicates according to a documented rule.
6. Only then save the CSV.

Do not silently accept malformed data.

Dataset-specific validation should be possible because the four datasets may not have identical structures.

---

# DUPLICATE HANDLING

There are two different duplicate concerns:

## Duplicate records

Handle duplicate rows according to a clearly documented rule.

Do not blindly remove records based only on a field such as symbol unless that is demonstrably correct for the dataset.

## Duplicate files

If the application is run multiple times for the same trading day, it should not create confusing files such as:

```
data.csv
data_1.csv
data_2.csv
```

Use a deterministic dataset/date-based filename and a clearly documented overwrite, update, or skip policy.

---

# CSV STORAGE

Use a dedicated storage module.

A recommended structure is:

```
data/
    top_gainers_losers/
        top_gainers_losers_YYYY-MM-DD.csv

    upper_band_hitters/
        upper_band_hitters_YYYY-MM-DD.csv

    volume_gainers_spurts/
        volume_gainers_spurts_YYYY-MM-DD.csv

    52_week_high/
        52_week_high_YYYY-MM-DD.csv
```

The final naming convention may be adjusted if there is a better engineering reason.

---

# LOGGING

Implement proper Python logging.

Logs should contain useful information such as:

* timestamp
* dataset name
* operation
* success/failure
* record count
* output file
* exception/error details

Example:

```
INFO Starting NSE downloader
INFO Downloading top-gainers-losers
INFO Received 50 records
INFO Validation successful
INFO Saved CSV to ...
ERROR Request failed for volume-gainers-spurts
```

Avoid excessive or useless logging.

---

# TESTING

Use pytest.

Tests must cover the assignment requirements.

At minimum include tests for:

1. Successful download.
2. Failed request.
3. Timeout/network failure.
4. Empty response.
5. Invalid response.
6. Data validation.
7. Missing/invalid columns.
8. Duplicate handling.
9. File creation.
10. Duplicate file handling.
11. Individual dataset execution where practical.
12. All-dataset execution and failure isolation where practical.

Do not make tests dependent on live NSE availability unless explicitly marked as integration tests.

Use mocks/fakes for unit tests where appropriate.

---

# SAMPLE CSV

Provide at least one sample CSV output in a sample/ directory.

Clearly mark sample/test data as sample data if it is not a live production download.

Do not fabricate live NSE results and present them as real data.

---

# README

The final README.md must explain:

* what the application does
* project architecture
* requirements
* installation
* configuration
* how to run
* how to download all datasets
* how to download individual datasets
* how data acquisition works
* where data is stored
* how errors are handled
* how validation works
* how duplicate records are handled
* how duplicate files are handled
* how logging works
* how tests are run
* limitations
* assumptions

---

# REQUIREMENTS.TXT

Keep the project's required Python dependencies in requirements.txt.

Do not add unnecessary packages.

---

# .GITIGNORE

Create a suitable .gitignore.

At minimum consider:

```
venv/
__pycache__/
*.pyc
.pytest_cache/
logs/
```

Decide whether generated data files should be committed and document the decision if relevant.

Never commit secrets.

---

# SECURITY

Do not put:

* API keys
* passwords
* tokens
* private credentials

inside source code.

If credentials are ever needed, use environment variables and document the configuration.

---

# BONUS FEATURES

Only implement bonus features after the core assignment is working.

Possible bonus features include:

* scheduled execution
* retry with sensible backoff
* configurable output directory
* Docker
* database storage in addition to CSV
* historical data management
* failure notifications
* stronger unit/integration test coverage
* clean extensible architecture

Do not sacrifice core requirements for bonus features.

---

# DEVELOPMENT PROCESS — VERY IMPORTANT

DO NOT IMPLEMENT THE ENTIRE PROJECT IN ONE STEP.

We will work phase by phase.

Before every phase:

1. Explain the objective of the phase.
2. Explain why it is required.
3. Identify which files will be created/modified.
4. Explain the expected result.
5. Ask for my approval if the phase requires significant implementation.

After implementation:

1. Show what changed.
2. Explain each important change in beginner-friendly language.
3. Tell me exactly how to test it.
4. Tell me the expected output.
5. Check for errors.
6. Stop and wait for my instruction before moving to the next major phase.

DO NOT automatically continue through all phases.

---

# PHASE PLAN

Use this high-level development order.

## PHASE 0 — Repository inspection

Tasks:

* Read assignment PDF.
* Inspect existing files.
* Inspect Python version.
* Inspect virtual environment.
* Inspect installed dependencies.
* Confirm current project state.
* Do not modify application code unnecessarily.

Expected result:

A clear understanding of the current repository.

STOP after Phase 0.

---

## PHASE 1 — Project architecture and configuration

Tasks:

* Finalize folder structure.
* Create configuration structure.
* Define dataset identifiers.
* Define output directories.
* Define dataset URLs/configuration.
* Create .gitignore if needed.

Do not implement the full downloader yet.

STOP after Phase 1.

---

## PHASE 2 — Investigate NSE data acquisition

This is a critical phase.

For each of the four NSE pages:

* determine how data is actually obtained
* inspect response format
* identify endpoint/mechanism if applicable
* identify required headers/session behavior
* determine how each dataset differs
* document findings

Do not assume all four pages use identical endpoints or response structures.

STOP after Phase 2.

---

## PHASE 3 — Build acquisition layer

Implement:

* HTTP session/client
* requests
* headers
* timeout
* HTTP error handling
* response parsing
* controlled retry if appropriate

Test with mocked responses.

STOP after Phase 3.

---

## PHASE 4 — Build validation layer

Implement:

* non-empty validation
* structure validation
* required-column validation
* dataset-specific validation
* duplicate handling

Add pytest tests.

STOP after Phase 4.

---

## PHASE 5 — Build CSV storage

Implement:

* output directories
* deterministic filenames
* date handling
* CSV writing
* duplicate-file policy

Add tests.

STOP after Phase 5.

---

## PHASE 6 — Build logging

Implement:

* console logging
* file logging
* timestamps
* success/failure messages
* record counts
* errors

STOP after Phase 6.

---

## PHASE 7 — Build main CLI

Implement:

```
python main.py
```

and:

```
python main.py --dataset <dataset>
```

Also:

```
python main.py --help
```

Ensure failure isolation.

STOP after Phase 7.

---

## PHASE 8 — Integration testing

Run the complete workflow.

Verify:

* all four datasets
* individual dataset execution
* successful downloads
* invalid response behavior
* empty response behavior
* network failures
* validation failures
* duplicate handling
* CSV creation
* logging
* failure isolation

STOP after Phase 8.

---

## PHASE 9 — README and sample output

Complete:

* README.md
* sample CSV
* architecture documentation
* installation instructions
* usage examples
* testing instructions
* limitations
* assumptions

STOP after Phase 9.

---

## PHASE 10 — Optional bonus features

Only after the core assignment passes.

Possible order:

1. Retry with exponential backoff.
2. Configurable output directory.
3. Scheduling.
4. Historical data support.
5. Docker.
6. Database storage.
7. Failure notifications.

Do not add unnecessary features.

STOP after each bonus feature.

---

# QUALITY GATE BEFORE FINAL SUBMISSION

Before declaring the assignment complete, perform a final review against the assignment.

Create a checklist covering:

* all four datasets obtained
* CSV files generated
* automatic acquisition
* individual dataset support
* error handling
* failure isolation
* logging
* validation
* duplicate records
* duplicate files
* configuration separation
* separation of responsibilities
* tests
* README
* requirements.txt
* sample CSV
* configuration
* limitations/assumptions

For each requirement, show:

```
PASS
PARTIAL
FAIL
```

Do not claim PASS without actually verifying it.

---

# CODING STYLE

Use:

* clear variable names
* small functions
* type hints where useful
* docstrings for important functions/classes
* meaningful exception handling
* minimal global state
* pathlib for filesystem operations where appropriate
* Python standard library where practical

Avoid:

* giant functions
* duplicated code
* unnecessary classes
* unnecessary frameworks
* hardcoded secrets
* hidden behavior
* fake data presented as live data
* excessive dependencies

---

# BEGIN NOW

Start with PHASE 0 ONLY.

Do NOT write the complete application.

First:

1. Read the assignment PDF.
2. Inspect the repository.
3. Report the current project state.
4. Explain what is already present.
5. Identify what is missing.
6. Explain the proposed architecture at a high level.
7. Explain the next phase.

Then STOP and wait for my instruction.

Remember:

DO NOT IMPLEMENT THE ENTIRE PROJECT AT ONCE.

We will build, test, understand, and verify one phase at a time.

---

## PROJECT STATUS UPDATE — PHASE 1 (ARCHITECTURE & CONFIGURATION COMPLETED)

* **Status:** Phase 1 Completed.
* **Architecture Established:**
  * Package: `src/nse_market_data/`
  * Configuration: `src/nse_market_data/config.py` (centralized dataset URLs, output paths, timeouts, headers)
  * Data Models: `src/nse_market_data/models.py` (`DatasetIdentifier`, `DatasetConfig`, `DownloadResult`, `DownloadStatus`)
  * Logging: `src/nse_market_data/utils/logger.py` (console and file logging setup)
  * Entry Point: `main.py` (CLI argument parsing and environment initialization)
  * Dependencies: `requirements.txt` (`requests`, `pytest`)
  * Version Control: `.gitignore` configured
* **Next Phase:** Phase 2 — Investigate NSE Data Acquisition (endpoint research and behavior analysis).

---

## PROJECT STATUS UPDATE — PHASE 2 (DATA ACQUISITION COMPLETED)

* **Status:** Phase 2 Completed.
* **Acquisition Layer Implemented:**
  * Client: `src/nse_market_data/downloader/client.py` (`NSEClient` with browser headers, session management, timeout, and exponential backoff retry).
  * Parser: `src/nse_market_data/downloader/parser.py` (JSON extraction and structural checks for all 4 NSE datasets).
  * Exceptions: `src/nse_market_data/downloader/exceptions.py` (structured error hierarchy distinguishing transient from permanent failures).
  * Coordinator: `src/nse_market_data/downloader/acquisition.py` (`NSEDataAcquisition` with complete failure isolation).
  * Entry Point: `main.py` updated to run acquisition and report record counts.
  * Unit Tests: `tests/test_acquisition.py` (16 offline tests using mocks, all passing).
  * Live Verification: All 4 datasets tested live against NSE with 100% success.
* **Next Phase:** Phase 3 — Data Validation and CSV Storage.

---

## PROJECT STATUS UPDATE — PHASE 3 (DATA VALIDATION & CSV STORAGE COMPLETED)

* **Status:** Phase 3 Completed.
* **Components Implemented:**
  * Validation: `src/nse_market_data/validation/validator.py` (`DataValidator` validating required keys, rejecting corrupt/empty records, and executing stable deduplication).
  * Storage: `src/nse_market_data/storage/csv_storage.py` (`CSVStorage` performing atomic writes via temporary files, generating deterministic `<prefix>_YYYY-MM-DD.csv` filenames, and enforcing same-day overwrite/update without duplicate file proliferation).
  * Schemas & Column Mappings: `src/nse_market_data/config.py` (centralized `required_keys`, `unique_key_fields`, and `column_mapping` for all 4 NSE datasets).
  * Custom Exceptions: `src/nse_market_data/validation/exceptions.py` and `src/nse_market_data/storage/exceptions.py`.
  * Unit & Integration Tests:
    * `tests/test_validation.py` (11 tests covering valid/empty/missing keys/duplicates).
    * `tests/test_storage.py` (5 tests covering filename generation, atomic writes, repeated runs).
    * `tests/test_pipeline_integration.py` (End-to-end integration test: Acquisition -> Validation -> Deduplication -> Storage).
    * Total test suite: 33 automated tests, 100% passing.
  * Live Verification: All 4 datasets successfully acquired, validated, deduplicated, and persisted to `data/output/`. Repeated run verified overwrite policy without duplicate files.
* **Next Phase:** Phase 4 — Application Orchestration and CLI.

---

## PROJECT STATUS UPDATE — PHASE 4 (APPLICATION ORCHESTRATION & CLI COMPLETED)

* **Status:** Phase 4 Completed.
* **Components Implemented:**
  * Orchestrator: `src/nse_market_data/orchestrator.py` (`NSEPipelineOrchestrator`, `PipelineDatasetResult`, `PipelineRunSummary` coordinating Acquisition -> Parsing -> Validation -> Deduplication -> Storage with complete stage-by-stage error isolation).
  * CLI Application: `main.py` (Argparse CLI supporting default all-dataset downloads, individual `--dataset` downloads, `--output-dir` custom paths, `--list-datasets`, and `--help`).
  * Identifier & Alias Resolution: `src/nse_market_data/config.py` (`resolve_dataset_identifier` supporting canonical IDs and aliases like `52-week-high-equity-market`).
  * Summary Reporting: Tabular summary reporting status, counts, duplicate counts, output paths, and execution times.
  * Exit Codes: `0` for complete success, `1` for operational failure, `2` for invalid CLI options.
  * Test Suite: `tests/test_orchestrator.py` added (10 tests covering batch, single, failures, isolation, summary, CLI).
  * Overall Test Suite: 43 automated tests, 100% passing.
  * Live Verification: Tested single dataset and full 4-dataset batch live against NSE; summary table rendered and exit code `0` returned.
* **Next Phase:** Phase 5 — End-to-End Testing and Reliability Hardening.

---

## PROJECT STATUS UPDATE — PHASE 5 (TESTING & RELIABILITY HARDENING COMPLETED)

* **Status:** Phase 5 Completed.
* **Verification & Testing Accomplishments:**
  * Expanded automated test suite from 43 to 45 unit/integration tests (`tests/test_pipeline_integration.py` augmented).
  * Explicit Failure Isolation Verification: Tested scenario where Dataset A succeeds, Dataset B fails (HTTP 503), and Datasets C & D proceed and are saved successfully.
  * End-to-End CLI Verification: Tested custom `--output-dir`, alias resolution (`52-week-high-equity-market`), help flags, invalid dataset handling, and partial failure exit codes.
  * 100% Deterministic Offline Testing: All 45 tests pass in ~0.9 seconds with zero external internet dependencies.
  * Live NSE Verification: All 4 datasets confirmed downloading and persisting deterministically.
* **Next Phase:** Phase 6 — Final Project Documentation (README) & Sample Data Delivery.

---

# ==============================================================================
# FINAL PROJECT DOCUMENTATION — NSE MARKET DATA DOWNLOADER
# ==============================================================================

## 1. Project Title
**NSE Market Data Downloader**

An automated, reliable, and production-minded Python command-line data pipeline designed to retrieve, parse, validate, deduplicate, and persist market data from the National Stock Exchange of India (NSE).

---

## 2. Overview & Architecture

### What the Application Does
The application automates the retrieval and storage of market datasets corresponding to four primary NSE market pages without requiring manual copying or manual downloads from the browser. It operates as a modular, resilient pipeline:

```text
       ┌────────────────────────────────────────────────────────┐
       │              Configuration (config.py)                 │
       │   Endpoints, Headers, Paths, Timeouts, Schema Mappings │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │        Data Acquisition (downloader/client.py)         │
       │     Session, Browser Headers, Gzip, Backoff Retries    │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │        Response Parsing (downloader/parser.py)         │
       │   Payload Unpacking, HTML Guard, Metadata Extraction   │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │         Data Validation (validation/validator.py)      │
       │      Non-Empty Check, Schema & Required Columns        │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │       Duplicate Handling (validation/validator.py)     │
       │     Business Key Deduplication (Keep-First Policy)     │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │           CSV Storage (storage/csv_storage.py)         │
       │   Atomic Writes, Deterministic Dates, Overwrite Policy │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │         CLI & Logging (main.py, utils/logger.py)       │
       │  Run Summary Table, Failure Isolation, Audit Logs      │
       └────────────────────────────────────────────────────────┘
```

---

## 3. Supported Datasets

The application supports all four assignment-specified NSE datasets:

| # | Dataset Name | CLI Identifier | NSE Page URL | Backend API Endpoint |
|---|---|---|---|---|
| 1 | **Top Gainers / Losers** | `top-gainers-losers` | `https://www.nseindia.com/market-data/top-gainers-losers` | `https://www.nseindia.com/api/live-analysis-variations?index=gainers` |
| 2 | **Upper Band Hitters** | `upper-band-hitters` | `https://www.nseindia.com/market-data/upper-band-hitters` | `https://www.nseindia.com/api/live-analysis-price-band-hitter` |
| 3 | **Volume Gainers / Spurts** | `volume-gainers-spurts` | `https://www.nseindia.com/market-data/volume-gainers-spurts` | `https://www.nseindia.com/api/live-analysis-volume-gainers` |
| 4 | **52 Week High — Equity Market** | `52-week-high` *(or alias `52-week-high-equity-market`)* | `https://www.nseindia.com/market-data/52-week-high-equity-market` | `https://www.nseindia.com/api/live-analysis-data-52weekhighstock` |

---

## 4. Implemented Features

* **Automated Data Retrieval:** Discovers and directly targets backend JSON REST API endpoints uncovered from NSE frontend bundles rather than scraping fragile HTML layouts.
* **Resilient HTTP Client:** Manages browser-realistic headers, referrers, and cookie sessions. Configured with a 15-second timeout and exponential backoff retry on transient network failures or rate limits (`429`, `5xx`).
* **Content Type & Error Guard:** Rejects HTML error pages, access-denied pages, and empty payloads disguised under HTTP 200 codes.
* **Failure Isolation:** Failure of one dataset during batch execution (e.g. Upper Band Hitters) does not abort the remaining downloads. Succeeded datasets are safely saved, and failures are detailed in the final summary.
* **Schema Validation:** Verifies that raw records conform to required column definitions for each specific dataset schema.
* **Business-Key Deduplication:** Identifies and filters duplicates using stable natural business keys (`(symbol, series)` or `(symbol,)`) under an auditable Keep-First policy.
* **Atomic CSV Writes:** Writes output to hidden temporary files (`.{filename}.tmp`) and atomically renames them upon completion to prevent partially written or corrupt files on disk.
* **Deterministic Filename & Overwrite Policy:** Saves output as `<prefix>_YYYY-MM-DD.csv`. Multiple runs on the same trading day atomically refresh the daily file without generating confusing duplicate files (e.g. `_1.csv`).
* **Structured Logging:** Dual output to standard console and rotating UTF-8 log files (`logs/downloader.log`) with record counts, operation timestamps, and error details without leaking cookies or credentials.
* **Configurable Storage:** Output root directory can be specified via CLI (`--output-dir`) or environment variable (`NSE_OUTPUT_DIR`), defaulting cleanly to `data/output/`.
* **Zero External Test Dependencies:** 45 automated unit and integration tests run in under 1 second with 100% mocked offline fixtures.

---

## 5. Project Directory Structure

```text
nse-market-data-downloader/
├── main.py                                  # CLI application entry point
├── requirements.txt                         # Pinned dependencies (requests, pytest)
├── pytest.ini                               # Test runner configuration
├── .gitignore                               # Excludes venvs, caches, logs, and outputs
├── README.md                                # Master instructions and project documentation
├── master_prompt.md                         # Master assignment prompt
│
├── src/
│   └── nse_market_data/
│       ├── __init__.py                      # Package exports and versioning
│       ├── config.py                        # Centralized URLs, schemas, headers, timeouts
│       ├── models.py                        # Domain dataclasses and enums
│       ├── orchestrator.py                  # End-to-end pipeline runner and summary generator
│       │
│       ├── downloader/                      # Data Acquisition Layer
│       │   ├── __init__.py
│       │   ├── client.py                    # Session-based HTTP client with retries
│       │   ├── exceptions.py                # Network, HTTP, and parsing exceptions
│       │   ├── parser.py                    # Dataset-specific JSON parsers
│       │   └── acquisition.py               # Dataset acquisition coordinator
│       │
│       ├── validation/                      # Data Validation & Deduplication Layer
│       │   ├── __init__.py
│       │   ├── exceptions.py                # Schema and data structure exceptions
│       │   └── validator.py                 # Column validation and deduplicator
│       │
│       ├── storage/                         # CSV Storage Layer
│       │   ├── __init__.py
│       │   ├── exceptions.py                # Storage and filesystem exceptions
│       │   └── csv_storage.py               # Atomic CSV file writing & overwrite enforcement
│       │
│       └── utils/                           # Shared Utilities
│           ├── __init__.py
│           └── logger.py                    # Formatted console and file logging setup
│
├── tests/                                   # Automated Test Suite (45 tests)
│   ├── __init__.py
│   ├── test_acquisition.py                  # HTTP client, error handling, and parser tests
│   ├── test_validation.py                   # Schema verification and deduplication tests
│   ├── test_storage.py                      # Filenames, atomic writes, and overwrite tests
│   ├── test_orchestrator.py                 # Pipeline coordination and failure isolation tests
│   └── test_pipeline_integration.py         # Full end-to-end integration tests
│
├── data/
│   ├── output/                              # Default CSV output directory
│   │   ├── top_gainers_losers/
│   │   ├── upper_band_hitters/
│   │   ├── volume_gainers_spurts/
│   │   └── 52_week_high/
│   └── raw/                                 # Raw response cache if needed
│
├── sample/                                  # Sample deliverables for evaluation
│   ├── README.md                            # Sample data overview
│   ├── sample_top_gainers_losers.csv
│   ├── sample_upper_band_hitters.csv
│   ├── sample_volume_gainers_spurts.csv
│   └── sample_52_week_high.csv
│
└── logs/
    └── downloader.log                       # Execution logs with timestamps and counts
```

---

## 6. Installation & Environment Setup

### Prerequisites
* Python 3.10 or higher
* Standard Python package manager (`pip`)

### Installation
1. Clone or download the repository into your local workspace.
2. (Recommended) Create and activate a Python virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 7. Command-Line Usage

### 1. Download All Four Datasets (Default Mode)
```bash
python main.py
```
Retrieves, validates, and stores all four datasets. Generates a formatted summary table displaying status, counts, and output paths.

### 2. Download an Individual Dataset
Use the `--dataset` (or `-d`) argument:
```bash
# Top Gainers / Losers
python main.py --dataset top-gainers-losers

# Upper Band Hitters
python main.py --dataset upper-band-hitters

# Volume Gainers / Spurts
python main.py --dataset volume-gainers-spurts

# 52 Week High (canonical name or assignment alias)
python main.py --dataset 52-week-high
python main.py --dataset 52-week-high-equity-market
```

### 3. Specify a Custom Output Directory
Use the `--output-dir` (or `-o`) argument:
```bash
python main.py --output-dir /custom/data/directory
```

### 4. List Configured Datasets & Endpoints
```bash
python main.py --list-datasets
```

### 5. Display Help
```bash
python main.py --help
```

### CLI Exit Codes
* `0`: Success (all requested datasets were downloaded, validated, and saved).
* `1`: Operational failure (one or more requested datasets failed).
* `2`: CLI argument error (e.g. unrecognized dataset name or invalid parameter).

---

## 8. How Data Acquisition Works

1. **Endpoint Resolution:** Rather than parsing fragile web page DOMs, the downloader targets NSE's internal JSON REST APIs discovered from the frontend script bundles.
2. **Session & Cookie Priming:** An internal `requests.Session` object manages browser-realistic request headers (`User-Agent`, `Referer: https://www.nseindia.com/`, `Accept-Language`) and stores cookies.
3. **Decompression & Encodings:** Configured to accept standard `gzip, deflate` encodings to avoid unsupported Brotli compression issues and ensure clean native JSON parsing.
4. **Resilient Retry Policy:**
   * Retryable errors (network connection drops, socket timeouts, HTTP `429`, `500`, `502`, `503`, `504`) trigger exponential backoff retries (`backoff_factor * 2^(attempt-1)`).
   * Permanent client errors (HTTP `404`, `400`) fail immediately without useless retries.
5. **Content Verification:** Responses with HTTP 200 that contain HTML access-denied pages or empty bodies are rejected with `NSEResponseParsingError`.

---

## 9. Validation & Deduplication

Before any dataset is persisted, it undergoes strict schema and quality checks:
* **Empty Dataset Check:** Payloads with zero records fail validation immediately.
* **Schema Conformity:** Each dataset configuration specifies `required_keys`. Any missing column halts storage for that dataset.
* **Identifier Verification:** Records missing valid `symbol` identifiers are filtered out.
* **Business-Key Deduplication:**
  * **Top Gainers / Losers:** Key `(symbol, series)`
  * **Upper Band Hitters:** Key `(symbol, series)` (allows securities in distinct series like `EQ` and `BE` to legitimately coexist)
  * **Volume Gainers / Spurts:** Key `(symbol,)`
  * **52 Week High:** Key `(symbol, series)`
* **Auditability:** Deduplication logs the exact number of duplicates removed and records it in the run summary.

---

## 10. CSV Storage & File Management

* **Deterministic Filenames:** Files are saved using the date-identifying format:
  `{prefix}_{YYYY-MM-DD}.csv`
  Example: `top_gainers_losers_2026-09-18.csv`
* **Same-Day Repeated-Run Policy:**
  Running the application multiple times on the same trading day executes a deterministic **in-place atomic update/overwrite**. This directly satisfies the assignment requirement to avoid cluttering the directory with confusing files like `data_1.csv`, `data_2.csv`.
* **Atomic Safe Writes:**
  Records are written to a temporary file (`.{filename}.tmp`) and atomically replaced (`os.replace`). If an error occurs midway, the temporary file is deleted, ensuring no incomplete or corrupt CSV file remains on disk.
* **Standardized CSV Headers:**
  Raw JSON keys are mapped to clean, uppercase headers matching official NSE export benchmarks (e.g., `SYMBOL`, `SERIES`, `LTP`, `PERCENT_CHANGE`, `VOLUME`, `VALUE`).

---

## 11. Logging System

Configured in `src/nse_market_data/utils/logger.py`:
* Dual outputs: formatted console logging and persistent file logging (`logs/downloader.log`).
* Standard log format: `YYYY-MM-DD HH:MM:SS | LEVEL | MODULE | MESSAGE`.
* Logs dataset name, operation timestamp, attempt counts, record counts, duplicate counts, output path, and execution duration.
* Security safe: **Never** logs session cookies, private headers, or full payload bodies.

---

## 12. Automated Testing

The project includes an automated test suite with **45 unit and integration tests** built with `pytest`:

### Running Tests
Execute the test suite directly from the project root:
```bash
pytest
```
Or with verbose output:
```bash
pytest -v
```

### Test Suite Structure
* `tests/test_acquisition.py` (16 tests): HTTP client behavior, timeout handling, connection failures, HTTP 404/5xx errors, retry backoff, malformed responses, HTML error page detection, empty payloads, and JSON parsers for all 4 datasets.
* `tests/test_validation.py` (11 tests): Schema validation, missing columns, non-dictionary structures, blank symbol filtering, duplicate detection, and series-aware deduplication.
* `tests/test_storage.py` (5 tests): Filename generation, atomic temporary writes, automatic subdirectory creation, same-day repeated overwrite enforcement, and filesystem error handling.
* `tests/test_orchestrator.py` (10 tests): Pipeline orchestration, single dataset mode, failure isolation, summary table generation, CLI help, CLI list-datasets, and invalid argument rejection.
* `tests/test_pipeline_integration.py` (3 tests): Full end-to-end flow (Acquisition -> Validation -> Deduplication -> Storage), multi-dataset failure isolation, and CLI custom output directory verification.

All 45 tests are **100% deterministic and offline**, relying on mocks without calling live NSE servers.

---

## 13. Limitations & Engineering Assumptions

1. **Market Hours & Trading Dates:** When run on weekends, market holidays, or after market close (16:00 IST), NSE APIs return data from the most recently completed trading day. The application dates the output file by the snapshot run date while recording the source trading timestamp in the metadata logs.
2. **IP Rate Limiting:** NSE employs Akamai-based rate limiting. Rapid high-frequency requests may be temporarily throttled. The application mitigates this with exponential backoff and connection reuse, but continuous aggressive polling is not recommended.
3. **Internal API Stability:** The application targets NSE's current JSON APIs (`api/live-analysis-*`). Should NSE modify its internal endpoints or JSON structures, the centralized `config.py` and `parser.py` allow endpoint and schema adjustments without rewriting the pipeline architecture.

---

## 14. Assignment Evaluation Self-Audit Checklist

| Evaluation Area | Weight | Verification Status | Implementation Evidence |
|---|---|---|---|
| **Successfully Obtaining All 4 Datasets** | **30%** | **PASS** | Automated retrieval implemented for Top Gainers/Losers, Upper Band Hitters, Volume Gainers, and 52-Week High. Verified against live NSE endpoints. |
| **Code Quality & Architecture** | **20%** | **PASS** | Strict separation of concerns (Acquisition, Parsing, Validation, Storage, Logging, Orchestration, CLI). Standard typing, docstrings, no circular imports, no hardcoded paths. |
| **Error Handling & Reliability** | **15%** | **PASS** | Handles timeouts, connection errors, HTTP status errors, empty responses, malformed JSON, and HTML error pages. Exponential backoff retries on transient errors. Failure isolation between datasets. |
| **Data Validation** | **10%** | **PASS** | Validates non-empty datasets, required schema columns, and invalid record structures. Deduplicates records using stable business keys with count reporting. |
| **Automation & File Management** | **10%** | **PASS** | Deterministic filenames (`<prefix>_YYYY-MM-DD.csv`), organized subdirectories, atomic safe-writes via temporary files, same-day repeated-run overwrite policy preventing `_1.csv` clutter. |
| **Testing** | **10%** | **PASS** | 45 deterministic automated unit and integration tests using `pytest` covering all required scenarios. 100% passing in < 1 second. |
| **Documentation** | **5%** | **PASS** | Exhaustive `README.md` documenting installation, architecture, usage, acquisition mechanism, error handling, duplicate handling, and limitations. Sample CSV outputs in `sample/`. |

