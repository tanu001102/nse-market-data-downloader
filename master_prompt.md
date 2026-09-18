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
