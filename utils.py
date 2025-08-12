import streamlit as st
from gnpsdata import taskresult, workflow_fbmn

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