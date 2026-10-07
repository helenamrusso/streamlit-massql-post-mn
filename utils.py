import os
import urllib.parse
from io import StringIO

import pandas as pd
import requests


def get_git_short_rev():
    try:
        with open('.git/logs/HEAD', 'r') as f:
            last_line = f.readlines()[-1]
            hash_val = last_line.split()[1]
        return hash_val[:7]
    except Exception:
        return ".git/ not found"


# GNPS2 servers a task can live on, in lookup order. Done here rather than with gnpsdata:
# its taskinfo.get_task_information and download_gnps2_task_resultfile only query prod.
GNPS2_SERVERS = {
    "prod": "https://gnps2.org",
    "beta": "https://beta.gnps2.org",
    "de": "https://de.gnps2.org",
}


def get_task_information(task_id: str) -> (str, dict):
    """Find which GNPS2 server holds the task. Returns (server_name, status_json)."""
    errors = []
    for server, base_url in GNPS2_SERVERS.items():
        try:
            r = requests.get(f"{base_url}/status.json", params={"task": task_id}, timeout=30)
            r.raise_for_status()
            # Servers that don't know the task answer 200 with an HTML page, not JSON
            return server, r.json()
        except Exception as e:
            errors.append(f"{server}: {e}")
    raise ValueError(f"Task {task_id} was not found on any GNPS2 server. Tried: {'; '.join(errors)}")


def gnps2_resultfile_url(task_id: str, result_path: str, server: str) -> str:
    return (f"{GNPS2_SERVERS[server]}/resultfile?task={task_id}"
            f"&file={urllib.parse.quote(result_path)}")


# Result-file locations per supported workflow. The Everything Bagel paths are for
# mode=fbmn (see get_workflow_paths); other EB modes lay files out differently.
WORKFLOW_PATHS = {
    "feature_based_molecular_networking_workflow": {
        "mgf": "nf_output/clustering/spectra_reformatted.mgf",
        "library": "nf_output/library/merged_results_with_gnps.tsv",
        "usi_mgf": "nf_output/clustering/spectra_reformatted.mgf",
    },
    "classical_networking_workflow": {
        "mgf": "nf_output/clustering/specs_ms.mgf",
        "library": "nf_output/library/merged_results_with_gnps.tsv",
        "usi_mgf": "nf_output/clustering/spectra_reformatted.mgf",
    },
    "everything_bagel_workflow": {
        "mgf": "nf_output/feature_finding/aligned_features_filled.mgf",
        "library": "nf_output/feature_library_search/merged_feature_library_search_results.tsv",
        "usi_mgf": "nf_output/feature_finding/aligned_features_filled.mgf",
    },
}

# Everything Bagel's library-search TSV names these columns differently; map them onto
# the schema the rest of the app expects (#Scan# is the join key, see run_analysis).
EB_LIBRARY_COLUMN_MAP = {
    "query_scan": "#Scan#",
    "NAME": "Compound_Name",
    "SPECTRUMID": "SpectrumID",
}


def get_workflow_paths(task_id: str) -> dict:
    """Resolve result-file locations for a task's workflow.

    Raises ValueError for unsupported workflows, and for Everything Bagel runs that
    are not in fbmn mode (their output layout differs from what this app handles).
    """
    server, task_info = get_task_information(task_id)
    workflowname = task_info.get("workflowname")

    if workflowname not in WORKFLOW_PATHS:
        raise ValueError(f"Unsupported workflow: {workflowname}. Cannot process this task.")

    if workflowname == "everything_bagel_workflow":
        params = task_info.get("submission_parameters") or {}
        mode = params.get("mode") if isinstance(params, dict) else None
        if mode != "fbmn":
            raise ValueError(
                f"Unsupported Everything Bagel mode: {mode!r}. Only 'fbmn' mode is supported."
            )

    return {"workflowname": workflowname, "server": server, **WORKFLOW_PATHS[workflowname]}


def gnps2_get_libray_dataframe_wrapper(task_id, paths):
    # Fetched with requests rather than gnpsdata's get_gnps2_task_resultfile_dataframe:
    # that one calls pd.read_csv(url), whose Python-urllib User-Agent is blocked by
    # GNPS2's Cloudflare (HTTP 403, error 1010), and it returns None on any failure.
    url = gnps2_resultfile_url(task_id, paths["library"], paths["server"])
    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text), sep="\t")
    except Exception as e:
        raise ValueError(
            f"Could not load library search results ({paths['library']}) for task {task_id} "
            f"from the GNPS2 {paths['server']} server: {e}"
        )
    if paths["workflowname"] == "everything_bagel_workflow":
        df = df.rename(columns=EB_LIBRARY_COLUMN_MAP)
    return df


def download_and_filter_mgf(task_id: str, paths: dict) -> (str, list, list):
    os.makedirs("temp_mgf", exist_ok=True)
    mgf_file_path = f"temp_mgf/{task_id}_mgf_all.mgf"
    cleaned_mgf = f"temp_mgf/{task_id}_mgf_cleaned.mgf"

    # Skip if cleaned file already exists
    if os.path.exists(cleaned_mgf):
        print(f"Skipping download, using existing file: {cleaned_mgf}")
        scan_list, pepmass_list = [], []
        with open(cleaned_mgf, "r") as mgf_file:
            for line in mgf_file:
                if line.startswith("SCANS="):
                    scan_list.append(line.strip().split("=")[1])
                elif line.startswith("PEPMASS="):
                    pepmass_list.append(line.strip().split("=")[1].split()[0])
        return cleaned_mgf, scan_list, pepmass_list

    url = gnps2_resultfile_url(task_id, paths["mgf"], paths["server"])
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(mgf_file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    scan_list, pepmass_list = [], []
    with open(mgf_file_path, "r") as mgf_file:
        lines = mgf_file.readlines()

    cleaned_mgf_lines = []
    inside_scan = False
    current_scan = []
    for line in lines:
        if line.startswith("BEGIN IONS"):
            inside_scan = True
            current_scan = [line]  # Start a new scan block
        elif line.startswith("END IONS"):
            current_scan.append(line)
            if any(
                len(peak.split()) == 2
                and all(part.replace(".", "", 1).isdigit() for part in peak.split())
                for peak in current_scan
            ):
                cleaned_mgf_lines.extend(current_scan)
            inside_scan = False
        elif inside_scan:
            current_scan.append(line)
        else:
            cleaned_mgf_lines.append(line)

    with open(cleaned_mgf, "w") as fout:
        fout.writelines(cleaned_mgf_lines)

    # Extract all scan numbers from the cleaned MGF file
    with open(cleaned_mgf, "r") as mgf_file:
        for line in mgf_file:
            if line.startswith("SCANS="):
                scan_list.append(line.strip().split("=")[1])
            elif line.startswith("PEPMASS="):
                pepmass_list.append(line.strip().split("=")[1].split()[0])

    return cleaned_mgf, scan_list, pepmass_list


def insert_mgf_info(task: str, input_mgf: str, validation_df: pd.DataFrame) -> StringIO:
    print(f"Inserting MGF info for task {task}...")

    mask = ~validation_df["query_validation"].str.contains('Did not pass any selected query', na=True, case=False)
    valid_scans = set(
        pd.to_numeric(validation_df.loc[mask, "#Scan#"], errors="coerce")
        .dropna().astype(int).tolist()
    )
    scan_to_validation = {
        int(k): v for k, v in zip(
            pd.to_numeric(validation_df["#Scan#"], errors="coerce").fillna(-1).astype(int),
            validation_df["query_validation"]
        ) if k != -1
    }

    buffer = StringIO()
    spectrum_lines = []
    skip_spectrum = False
    print(f"Processing MGF file: {input_mgf}")
    print(f"Filtering to {len(valid_scans)} scans that passed validation (out of {len(validation_df)} total scans)")

    file_contents = open(input_mgf, "r").readlines()
    for line in file_contents:
        if line.startswith("BEGIN IONS"):
            spectrum_lines = [line]
            skip_spectrum = False
        elif line.startswith("SCANS"):
            scan_number = int(line.split("=")[1].strip())
            spectrum_lines.append(line)

            if scan_number not in valid_scans:
                skip_spectrum = True
                continue

            validation_status = scan_to_validation.get(scan_number, "Unknown")

            insert_string = f"MASSQL_VALIDATION={validation_status}\n"

            for prev_line in spectrum_lines[:-1]:
                buffer.write(prev_line)
            buffer.write(insert_string)
            buffer.write(line)
            spectrum_lines = []

        elif line.startswith("END IONS"):
            if not skip_spectrum:
                spectrum_lines.append(line)
                for spectrum_line in spectrum_lines:
                    buffer.write(spectrum_line)
            spectrum_lines = []
        else:
            if not skip_spectrum:
                if spectrum_lines:
                    spectrum_lines.append(line)
                else:
                    buffer.write(line)
    print(f"Processed {input_mgf}")
    buffer.seek(0)
    return buffer


def create_mirrorplot_link(result_df: pd.DataFrame, task_id: str,
                           usi_mgf: str = "nf_output/clustering/spectra_reformatted.mgf"):
    result_df['mirror_link'] = result_df.apply(
        lambda x:
            "https://metabolomics-usi.gnps2.org/dashinterface/?usi1="
            + urllib.parse.quote(
                f"mzspec:GNPS2:TASK-{task_id}-{usi_mgf}:scan:{x['#Scan#']}"
            )
            + "&usi2="
            + urllib.parse.quote(
                f"mzspec:GNPS:GNPS-LIBRARY:accession:{x['SpectrumID']}"
            ) if pd.notna(x['SpectrumID']) else
            "https://metabolomics-usi.gnps2.org/dashinterface/?usi1="
            + urllib.parse.quote(
                f"mzspec:GNPS2:TASK-{task_id}-{usi_mgf}:scan:{x['#Scan#']}"
            ),
        axis=1
    )
