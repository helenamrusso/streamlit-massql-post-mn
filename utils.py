import os

import streamlit as st
from gnpsdata import taskresult, workflow_fbmn, taskinfo


def get_git_short_rev():
    try:
        with open('.git/logs/HEAD', 'r') as f:
            last_line = f.readlines()[-1]
            hash_val = last_line.split()[1]
        return hash_val[:7]
    except Exception:
        return ".git/ not found"


@st.cache_data
def gnps2_download_resultfile_wrapper(mgf_file_path, task_id):
    return taskresult.download_gnps2_task_resultfile(task_id, "nf_output/clustering/specs_ms.mgf", mgf_file_path)


@st.cache_data
def fbmn_download_mgf_wrapper(mgf_file_path, task_id):
    return workflow_fbmn.download_mgf(task_id, mgf_file_path)


@st.cache_data
def gnps2_get_libray_dataframe_wrapper(task_id):
    return taskresult.get_gnps2_task_resultfile_dataframe(task_id, 'nf_output/library/merged_results_with_gnps.tsv')


@st.cache_data
def download_and_filter_mgf(task_id: str) -> (str, str):
    os.makedirs("temp_mgf", exist_ok=True)
    mgf_file_path = f"temp_mgf/{task_id}_mgf_all.mgf"

    task_info = taskinfo.get_task_information(task_id)
    workflowname = task_info.get('workflowname')
    if workflowname == 'feature_based_molecular_networking_workflow':
        fbmn_download_mgf_wrapper(mgf_file_path, task_id)
    elif workflowname == 'classical_networking_workflow':
        gnps2_download_resultfile_wrapper(mgf_file_path, task_id)
    else:
        raise ValueError(f"Unsupported workflow: {workflowname}. Cannot download MGF.")
    scan_list = []
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
    # Save the cleaned MGF file
    cleaned_mgf = f"temp_mgf/{task_id}_mgf_cleaned.mgf"
    with open(cleaned_mgf, "w") as fout:
        fout.writelines(cleaned_mgf_lines)

    # Extract all scan numbers from the cleaned MGF file
    with open(cleaned_mgf, "r") as mgf_file:
        for line in mgf_file:
            if line.startswith("SCANS="):
                scan_list.append(line.strip().split("=")[1])

    return cleaned_mgf, scan_list
