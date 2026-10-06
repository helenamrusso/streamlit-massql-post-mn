# Changelog

All notable changes to the Post Molecular Networking MassQL app are listed here.
Releases are named by the `app_version` date shown in the app's **About** menu.

## [2026-10-04]

### Fixed
- Library search results now load again. They are fetched with `requests`
  instead of `gnpsdata`'s `pd.read_csv(url)`, because GNPS2's Cloudflare
  blocks that call's default User-Agent (HTTP 403, error 1010). The app tries
  the `prod`, `beta` and `de` GNPS2 servers in turn, and the error message
  lists which ones failed.

## [2026-07-14]

### Added
- Support for **Everything Bagel** tasks (FBMN mode only), alongside Feature-Based
  and Classical Molecular Networking. Each workflow's result-file paths are
  looked up from the task, and Everything Bagel's library columns are renamed to
  the names the rest of the app uses.
- An error message for unsupported workflows and for Everything Bagel modes other
  than `fbmn`.

### Changed
- `pyteomics` is pinned below 5, because 5.0 needs Python 3.10 or newer and the
  image uses Python 3.9.

## [2025-11-07]

These changes went live without a version bump. The app still showed version
`2025-08-12` while they were deployed.

### Added
- **Load Example** now loads a preset FBMN task (CMMC workshop data, including
  drug analogs). It selects the *Bile acids (stage 1)* queries and shows a short
  description of the dataset.
- Results for the example task are cached, so it opens without re-running the
  analysis (2025-11-04).
- TSV exports start with a header that lists the task ID and every query that was
  run (2025-10-06).
- Mirror plot links in the result tables, and a `pepmass` column for each scan
  (2025-08-24).
- GNPS2 analytics tracking (2025-08-13, updated 2025-10-15).

### Changed
- `streamlit` is pinned to 1.50, and the code is updated for the new `width=`
  arguments that replace `use_container_width` (2025-10-20).
- The **New Analysis** button moved above the Contributors section.
- An MGF that was already downloaded and cleaned for a task is reused instead of
  being downloaded again (2025-08-15).

### Fixed
- Leading and trailing whitespace is now removed from the task ID.
- Query-validation counts in the full table are now correct, and the validated
  MGF uses the same check to decide which scans passed (2025-10-20).

### Removed
- The "Load Precomputed Data" demo option. It was added on 2025-10-25 (PR #2)
  and reverted on 2025-11-04.

## [2025-08-12]

### Added
- **Download validated MGF**, which exports only the scans that passed the
  selected queries.
- A Contributors section and updated citations, including the N-acyl lipids
  paper (Cell, 2025).

### Changed
- Task result files are now fetched with the `gnpsdata` package.
- The page layout and styling were reworked (PR #1, app-reformat).
- Result caching was removed.

## [2025-06-18]

### Changed
- `matchms` is pinned to a fixed version.
- Deployment: a memory limit and a mount point were added to the Docker setup
  (2025-05-01), along with `.gitignore` updates.

## [2025-04-29]

### Added
- The app version and git hash are shown in the **About** menu.
- Results can be downloaded as tables.
- Docker, Makefile and template files for deploying on GNPS2.
- An email link for requesting a new predefined query (2025-04-26).

### Changed
- The handling of query results was refactored.
- The image is forced to use Python 3.9.

## [2025-04-25]

### Added
- More than one query or query group can be selected at once.
- A `?task_id=` URL parameter fills in the task ID (2025-04-23).

### Changed
- MGF processing and query handling were streamlined.

### Fixed
- The MassQL compendium queries.
- Reading the task ID from the URL parameter.

## [2025-04-11]

### Added
- A choice of query mode, between predefined query sets and custom queries.

### Changed
- MGF processing was improved.
- `pyyaml` was added to the requirements, and the README was updated.
- The GNPS2 Task ID field no longer has a default value.

## [2025-04-04]

### Added
- First release: a Streamlit app that runs MassQL queries on the MGF and
  library matches from a GNPS2 molecular networking job.
