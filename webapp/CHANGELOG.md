# Changelog — PostMN MassQL web app

All notable changes to `postmn_massql.html` are listed here. This is the
client-side version of the PostMN MassQL app: one self-contained HTML file
that runs MassQL in the browser, without Streamlit or a server. The changes to
the Streamlit app are in the [`CHANGELOG.md`](../CHANGELOG.md) at the root of
this repository.

- **Live:** <https://apps.gnps2.org/postmn_massql>
- **Releases** are named by the date shown as **App version** in the page footer.
- **Source:** the file is generated from `build/metaboapps/` in the
  [NextGenWebApps](https://github.com/Wang-Bioinformatics-Lab/NextGenWebApps)
  repository (`postmn.head.html`, `postmn.app.js` and
  `data/postmn_queries.json`, assembled by `build.py`). Make changes there and
  copy the rebuilt file here. If you edit this copy by hand, the next build
  overwrites your change.
- **Running it locally:** you can open the file directly or serve it from
  anywhere, and dropping an `.mgf` works offline. Fetching a GNPS2 task by ID
  only works from `apps.gnps2.org`, because GNPS2 allows only that origin to
  request its result files.

## [2026-10-20]

### Added
- A **Load example** button next to **Fetch task**. It loads the public GNPS2
  task `a322acf7936c4f91a41fd2f267d9b613` from `gnps2.org`.

## [2026-10-16]

### Added
- A filter box for the predefined queries. Type part of a name (for example
  *dihydroxy* or *glycine*) and the list shows the matching single queries from
  every group, so you can add one query without adding its whole group.
- **Paste queries…** adds many queries at once. Paste two columns,
  `name⇥query`, straight from Excel or Google Sheets, or paste one query per
  line. A header row is optional, and lines starting with `#` are ignored.
- **Import queries…** reads the same format from a `.tsv` or `.txt` file. You
  can also drop the file on the queries card.
- **Export queries** saves the current query list in the same format, so it can
  be imported again later.
- A **replace the list on import** option. When it's off, imported queries are
  added to the current list.

## [2026-10-06]

### Added
- The **App version** date in the page footer, like the `app_version` the
  Streamlit app shows in its About menu.
- The full predefined query set from this repository's `queries.py`: 106
  queries in four groups (bile acids stage 1, bile acids stage 2, N-acyl lipids
  and the MassQL compendium). They're offered in an **Add predefined queries…**
  dropdown. As in the Streamlit app, each group is added as a whole except the
  compendium, whose queries are offered one by one.
- Each predefined query can only be added once. Queries that are already in the
  list are greyed out and ticked in the dropdown.
- Columns in the **Full Table** and **Library Matches** tables can be sorted by
  clicking their headers.
- The **Full Table** shows each scan's first library match (compound name and
  `SpectrumID`), and its TSV export includes those columns.
- Mirror-plot links against the library hit, like the Streamlit app's
  `mirror_link`.
- Citations for the three sources of the predefined queries in the footer:
  MassQL compendium (Damiani et al. 2025), bile acids (Mohanty et al. 2024) and
  N-acyl lipids (Mannochio-Russo et al. 2025).

### Changed
- **Full Table** is now the first tab, ahead of **Library Matches**.
- The upstream query set replaces the two small built-in query packs (bile
  acids stage 1, and an example product-ion query).

### Fixed
- Results were shifted onto the wrong scans when the MGF contained empty
  entries. FBMN writes an entry without peaks for every feature that has no
  MS2, and the MassQL engine carried that entry's `SCANS=` and `PEPMASS=` into
  the next spectrum. So every real spectrum after an empty entry was reported
  under the wrong scan number, with a precursor m/z of 0. Empty entries are now
  skipped before the queries run, and the file summary says how many were
  skipped.

## [2026-08-17]

The first release. The page did not show a version yet.

### Added
- A client-side port of this Streamlit app. Give it a GNPS2 task ID and a server
  (`gnps2.org` or `beta.gnps2.org`), and it fetches the task's consensus MGF and
  library matches. Or drop an `.mgf` (and optionally a library-matches `.tsv`)
  from your computer.
- MassQL runs in the browser with the same Rust engine, compiled to
  WebAssembly, as the GNPS2 MassQL Playground. The engine is embedded in the
  file, so nothing is uploaded.
- Every scan is tagged with the queries it passed. The results are shown in
  **Library Matches**, **Full Table** and **Executed Queries** tabs.
- TSV export of each table, and a **validated MGF** export with only the scans
  that passed.
