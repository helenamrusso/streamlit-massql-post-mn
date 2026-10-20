# PostMN MassQL

Run MassQL queries on the results of a GNPS2 molecular networking job. The app
downloads the job's MGF and library matches, runs the queries you pick, and
marks each spectrum with the queries it passed, next to its library annotation.

It comes with ready-made query sets for bile acids, N-acyl lipids and the
MassQL compendium, and you can edit them or write your own.

## Use it online

- **Streamlit app:** <https://massqlpostmn.gnps2.org/>
- **Browser version:** <https://apps.gnps2.org/postmn_massql>. It's the same
  analysis in a single HTML file, with the queries running in your browser.
  See [`webapp/`](webapp/) and its [changelog](webapp/CHANGELOG.md).

Both accept the task ID of a Feature-Based or Classical Molecular Networking
job. The Streamlit app also accepts Everything Bagel jobs in FBMN mode. Both
have a **Load example** option.

## How it works

1. Enter a GNPS2 task ID.
2. Choose predefined queries, or add your own.
3. The app downloads the MGF, removes empty spectra and runs each query.
4. Results are joined with the GNPS library matches.
5. Browse the tables, and download them as TSV, or download an MGF with only
   the spectra that passed.

## Run locally

```bash
git clone https://github.com/helenamrusso/streamlit-massql-post-mn.git
cd streamlit-massql-post-mn
pip install -r requirements.txt
streamlit run app.py
```

The Docker image uses Python 3.9. With Docker, run `make server-compose`.

The browser version needs no installation: download
[`webapp/postmn_massql.html`](webapp/postmn_massql.html) and open it in your
browser. It works offline with an `.mgf` file from your computer (and
optionally the library-matches `.tsv`). Loading a job by task ID, including
the example, only works on the online version, because GNPS2 only lets
`apps.gnps2.org` request its result files.

## Changelog

- Streamlit app: [CHANGELOG.md](CHANGELOG.md)
- Browser version: [webapp/CHANGELOG.md](webapp/CHANGELOG.md)

## Citation

If you use this app, please cite MassQL and the paper behind the queries you ran:

- **MassQL and the compendium queries:** Damiani T. et al. *A universal language
  for finding mass spectrometry data patterns.* Nature Methods 22, 1247–1254
  (2025). <https://doi.org/10.1038/s41592-025-02660-z>
- **Bile acid queries:** Mohanty I. et al. *The underappreciated diversity of
  bile acid modifications.* Cell 187(7), 1801–1818 (2024).
  <https://doi.org/10.1016/j.cell.2024.02.019>
- **N-acyl lipid queries:** Mannochio-Russo H. et al. *The microbiome
  diversifies long- to short-chain fatty acid-derived N-acyl lipids.* Cell
  188(15), 4154–4169 (2025). <https://doi.org/10.1016/j.cell.2025.05.015>

Part of the GNPS2 MetaboApps. See also
[Multi-step MassQL](https://multistep-massql.gnps2.org/) for bile acid isomer
annotation.
