import ast
import base64
import glob
import os
import urllib.parse

import pandas as pd
import streamlit as st
from gnpsdata import taskinfo
from massql import msql_engine
from streamlit.components.v1 import html

from queries import *
from utils import fbmn_download_mgf_wrapper, gnps2_download_resultfile_wrapper, gnps2_get_libray_dataframe_wrapper, \
    get_git_short_rev

page_title = "Post MN MassQL"
git_hash = get_git_short_rev()
repo_link = "https://github.com/helenamrusso/streamlit-massql-post-mn"

# TODO: Bump version
app_version = "2025-08-12"

st.set_page_config(page_title=page_title, page_icon=":flashlight:",
                   menu_items={"About": (f"**App version**: {app_version} | "
                                         f"[**Git Hash**: {git_hash}]({repo_link}/commit/{git_hash})")})

# Add a tracking token
# TODO: Add token
html('<script async defer data-website-id="<your_website_id>" src="https://analytics.gnps2.org/umami.js"></script>',
     width=0, height=0)

citations = {
    "MassQL and Compendium queries": """Jarmusch, A.K., Aron, A.T., Petras, D., et al. (2022). A Universal Language for Finding Mass Spectrometry Data Patterns. bioRxiv. https://doi.org/10.1101/2022.08.06.503000""",
    "Bile acid queries": """Mohanty, I., Mannochio-Russo, H., Schweer, J.V., et al. (2024). The underappreciated diversity of bile acid modifications. Cell, 187(7), 1801–1818.e20. https://doi.org/10.1016/j.cell.2024.02.019""",
    "N-acyl lipids queries": """Mannochio-Russo, H., Charron-Lamoureux, V., van Faassen, M., et al. (2024). The microbiome diversifies N-acyl lipid pools – including short-chain fatty acid-derived compounds. bioRxiv. https://doi.org/10.1101/2024.10.31.621412""",
}

st.title("Post Molecular Networking MassQL")

query_params = st.query_params
# Input task ID
task_id = st.text_input(
    "Enter GNPS2 Task ID",
    placeholder="Enter a GNPS2 task ID",
    value=query_params.get("task_id", ""),
)

# Flatten only the Compendium queries
flattened_queries = {"Manual entry": {"query1": ""}}
for category, query_dict in ALL_QUERIES.items():
    if "Compendium" in category:
        for name, query in query_dict.items():
            label = f"{name}"
            flattened_queries[label] = {label: query}
    else:
        flattened_queries[category] = query_dict

# Generate link to email template (add a predefined query)
with open("email_template.txt", "r") as file:
    email_template = file.read()

subject = urllib.parse.quote("Compendium query addition")
body = urllib.parse.quote(email_template, safe="")
link = f"mailto:hmannochiorusso@health.ucsd.edu?subject={subject}&body={body}"

# Multiselect to choose one or more queries or groups
defined_query_modes = st.multiselect(
    f"Select one or more queries or groups ([add a predefined query]({link}))",
    list(flattened_queries.keys()),
)

# Combine selected queries
selected_query_dict = {}
for mode in defined_query_modes:
    selected_query_dict.update(flattened_queries[mode])

# Editable table for selected queries
editable_df = pd.DataFrame(
    [{"name": name, "query": query} for name, query in selected_query_dict.items()]
)

run_button = None
if selected_query_dict:
    st.markdown("### Query Editor")
    st.markdown("Edit the selected MassQL query or enter a new one below:")
    edited_df = st.data_editor(
        editable_df, num_rows="dynamic", use_container_width=True
    )
    run_button = st.button("Run Analysis")


    # Update custom queries
    def get_custom_queries(df):
        return {
            row["name"]: row["query"]
            for _, row in df.iterrows()
            if row["name"] and row["query"]
        }


    custom_queries = get_custom_queries(edited_df)


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


if run_button:
    # Initialize a list to store the queries that were run
    executed_queries = []

    with st.spinner("Downloading files and running queries..."):
        library_matches = gnps2_get_libray_dataframe_wrapper(task_id)
        cleaned_mgf_path, all_scans = download_and_filter_mgf(task_id)
        mgf_path = cleaned_mgf_path

    with st.spinner("Running MassQL queries... This may take a while, please be patient!"):
        all_query_results_df = []
        container = st.empty()
        for query_name, input_query in custom_queries.items():
            with container:
                st.write(f"Running query: {query_name}")
                executed_queries.append(f"{query_name}: {input_query}")
                try:
                    results_df = msql_engine.process_query(input_query, mgf_path)
                except KeyError:
                    results_df = pd.DataFrame()

            if len(results_df) == 0:
                all_query_results_df.append({"query": query_name, "scan_list": "NA"})
            else:
                passed_scan_ls = results_df["scan"].values.tolist()
                passed_scan_ls = [int(x) for x in passed_scan_ls]
                all_query_results_df.append({"query": query_name, "scan_list": passed_scan_ls})

        all_query_results_df = pd.DataFrame(all_query_results_df)
        all_query_results_df["scan_list"] = all_query_results_df["scan_list"].replace("NA", "[]")
        all_query_results_df["scan_list"] = all_query_results_df["scan_list"].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        all_query_results_df = all_query_results_df.explode("scan_list")
        all_query_results_df = all_query_results_df.rename(columns={"scan_list": "#Scan#", "query": "query_validation"})

    with st.spinner("Merging and displaying results..."):
        all_query_results_df["#Scan#"] = all_query_results_df["#Scan#"].astype(str)
        library_matches["#Scan#"] = library_matches["#Scan#"].astype(str)

        library_final = pd.merge(library_matches, all_query_results_df, on="#Scan#", how="left")
        fallback_label = "Did not pass any selected query"
        library_final["query_validation"] = library_final["query_validation"].fillna(fallback_label)

        library_final = library_final[["query_validation", "Compound_Name"] + [col for col in library_final.columns if
                                                                               col not in ["query_validation",
                                                                                           "Compound_Name"]]]

        library_final = library_final.groupby("#Scan#", as_index=False).agg(
            {
                "query_validation": lambda x: ", ".join(set(x)),
                **{
                    col: "first"
                    for col in library_final.columns
                    if col not in ["#Scan#", "query_validation"]
                },
            }
        )

        feather_files = glob.glob("temp_mgf/*.feather")
        for file in feather_files:
            try:
                os.remove(file)
            except Exception as e:
                st.warning(f"Could not delete {file}: {e}")

        st.success("Analysis complete!", icon="✅")
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "📚 Library Matches",
                "📋 Full Table",
                "🛠️ Executed Queries",
                "📖 Citations",
            ]
        )

        with tab1:
            st.markdown("## Table With Library Matches Only")
            st.dataframe(library_final)

            library_download = library_final.to_csv(sep='\t', index=False)
            b64 = base64.b64encode(library_download.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="library_matches.tsv">Download TSV table</a>'
            st.markdown(href, unsafe_allow_html=True)

            # Summary for library table
            st.markdown("#### Summary for Library Table")
            total_library_matches = library_final['#Scan#'].nunique()
            st.write(f"Total number of scans that matched with the library: {total_library_matches}")
            query_summary_library = library_final.groupby('query_validation')['#Scan#'].nunique()

            st.write("Number of scans that matched each query:")
            st.dataframe(query_summary_library)

        with tab2:
            # Create a full table with all scans
            all_scans_df = pd.DataFrame({'#Scan#': all_scans})
            all_scans_df['#Scan#'] = all_scans_df['#Scan#'].astype(str)

            full_table = pd.merge(all_scans_df, all_query_results_df, on='#Scan#', how='left')
            full_table = pd.merge(full_table, library_matches, on='#Scan#', how='left')
            full_table['query_validation'] = full_table['query_validation'].fillna(fallback_label)

            # Allow multiple queries per scan in the full table
            full_table = full_table.groupby(['#Scan#', 'query_validation'], as_index=False).first()
            col_order = ['#Scan#', 'query_validation', 'Compound_Name']
            full_table = full_table[col_order + [col for col in full_table.columns if col not in col_order]]
            st.markdown("## Full Table With All Scans")
            st.dataframe(full_table)

            full_download = full_table.to_csv(sep='\t', index=False)
            b64 = base64.b64encode(full_download.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="full_table.tsv">Download TSV table</a>'
            st.markdown(href, unsafe_allow_html=True)

            # Summary for full table
            st.markdown("#### Summary for Full Table")
            total_full_matches = full_table["#Scan#"].nunique()
            st.write(f"Total number of scans in the full table: {total_full_matches}")
            query_summary_full = full_table.groupby("query_validation")[
                "#Scan#"
            ].nunique()

            st.write("Number of scans that matched each query in the full table:")
            st.dataframe(query_summary_full)

        with tab3:
            # Display the executed queries at the end
            st.markdown("## Executed Queries")
            st.text_area(
                "All queries:", value="\n\n".join(executed_queries), height=300
            )
            queries_tsv = "\n".join([
                f"{e}\t{f}" for e, f in [i.split(":", 1) for i in executed_queries]
            ])
            b64 = base64.b64encode(queries_tsv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="executed_queries.tsv">Download data as TSV</a>'
            st.markdown(href, unsafe_allow_html=True)

        with tab4:
            # Display citations
            st.markdown("## Citations")
            for key, citation in citations.items():
                st.markdown(f"**{key}:** {citation}")
