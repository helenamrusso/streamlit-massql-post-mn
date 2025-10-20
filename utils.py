import os
import urllib.parse
from io import StringIO

import pandas as pd
from gnpsdata import taskresult, workflow_fbmn, taskinfo


def get_git_short_rev():
    try:
        with open('.git/logs/HEAD', 'r') as f:
            last_line = f.readlines()[-1]
            hash_val = last_line.split()[1]
        return hash_val[:7]
    except Exception:
        return ".git/ not found"


def gnps2_download_resultfile_wrapper(mgf_file_path, task_id):
    return taskresult.download_gnps2_task_resultfile(task_id, "nf_output/clustering/specs_ms.mgf", mgf_file_path)


def fbmn_download_mgf_wrapper(mgf_file_path, task_id):
    return workflow_fbmn.download_mgf(task_id, mgf_file_path)


def gnps2_get_libray_dataframe_wrapper(task_id):
    return taskresult.get_gnps2_task_resultfile_dataframe(task_id, 'nf_output/library/merged_results_with_gnps.tsv')


def download_and_filter_mgf(task_id: str) -> (str, list, list):
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

    task_info = taskinfo.get_task_information(task_id)
    workflowname = task_info.get('workflowname')
    if workflowname == 'feature_based_molecular_networking_workflow':
        fbmn_download_mgf_wrapper(mgf_file_path, task_id)
    elif workflowname == 'classical_networking_workflow':
        gnps2_download_resultfile_wrapper(mgf_file_path, task_id)
    else:
        raise ValueError(f"Unsupported workflow: {workflowname}. Cannot download MGF.")

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


def create_mirrorplot_link(result_df: pd.DataFrame, task_id: str):
    result_df['mirror_link'] = result_df.apply(
        lambda x:
            "https://metabolomics-usi.gnps2.org/dashinterface/?usi1="
            + urllib.parse.quote(
                f"mzspec:GNPS2:TASK-{task_id}-nf_output/clustering/spectra_reformatted.mgf:scan:{x['#Scan#']}"
            )
            + "&usi2="
            + urllib.parse.quote(
                f"mzspec:GNPS:GNPS-LIBRARY:accession:{x['SpectrumID']}"
            ) if pd.notna(x['SpectrumID']) else
            "https://metabolomics-usi.gnps2.org/dashinterface/?usi1="
            + urllib.parse.quote(
                f"mzspec:GNPS2:TASK-{task_id}-nf_output/clustering/spectra_reformatted.mgf:scan:{x['#Scan#']}"
            ),
        axis=1
    )
