import ast
import base64
import glob
import os
import urllib.parse

import pandas as pd
import streamlit as st
from massql import msql_engine
from streamlit.components.v1 import html

from queries import *
from utils import gnps2_get_libray_dataframe_wrapper, \
    get_git_short_rev, download_and_filter_mgf, insert_mgf_info, create_mirrorplot_link
from welcome import welcome_page

page_title = "Post MN MassQL"
git_hash = get_git_short_rev()
repo_link = "https://github.com/helenamrusso/streamlit-massql-post-mn"

# TODO: Bump version
app_version = "2025-08-12"

st.set_page_config(page_title=page_title, page_icon=":flashlight:", layout="wide",
                   menu_items={"About": (f"**App version**: {app_version} | "
                                         f"[**Git Hash**: {git_hash}]({repo_link}/commit/{git_hash})")})

# Add a tracking token
html('<script async defer data-website-id="74bc9983-13c4-4da0-89ae-b78209c13aaf" src="https://analytics.gnps2.org/umami.js"></script>', width=0, height=0)
html('<script defer src="https://analytics-api.gnps2.org/script.js" data-website-id="74665d88-3b9d-4812-b8fc-7f55ceb08f11"></script>', width=0, height=0)

citations = {
    "MassQL and Compendium queries": """Damiani, T., Jarmusch, A.K., Aron, A.T., Petras, D., et al. (2025).  A universal language for finding mass spectrometry data patterns. Nature Methods, 22(6), 1247–1254. https://doi.org/10.1038/s41592-025-02660-z""",
    "Bile acid queries": """Mohanty, I., Mannochio-Russo, H., Schweer, J.V., et al. (2024). The underappreciated diversity of bile acid modifications. Cell, 187(7), 1801–1818.e20. https://doi.org/10.1016/j.cell.2024.02.019""",
    "N-acyl lipids queries": """Mannochio-Russo, H., Charron-Lamoureux, V., van Faassen, M., et al. (2025).  The microbiome diversifies N-acyl lipid pools – including short-chain fatty acid-derived compounds. Cell, 188(15), 4154–4169.e19. https://doi.org/10.1016/j.cell.2025.05.015""",
}

# Initialize session state for results
if 'results_ready' not in st.session_state:
    st.session_state.results_ready = False
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

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

# Predefined example task ID
EXAMPLE_TASK_ID = "4e5f76ebc4c6481aba4461356f20bc35"

# Sidebar Configuration
with st.sidebar:
    st.title("🔧 Analysis Configuration")

    # Load example checkbox
    if not (load_example := st.checkbox("📋 Load Example Task", help="Load a predefined example task ID")):
        load_precomputed_demo = st.checkbox("📂 Load Precomputed Data", help="Load precomputed demo data for demonstration")
    else:
        load_precomputed_demo = False

    query_params = st.query_params
    if not load_precomputed_demo:
        # Input task ID with example functionality
        if load_example:
            task_id = st.text_input(
                "Enter GNPS2 Task ID",
                placeholder="Enter a GNPS2 task ID",
                value=EXAMPLE_TASK_ID,
            )
        else:
            task_id = st.text_input(
                "Enter GNPS2 Task ID",
                placeholder="Enter a GNPS2 task ID",
                value=query_params.get("task_id", ""),
            ).strip()

        # Multiselect to choose one or more queries or groups
        defined_query_modes = st.multiselect(
            f"Select queries ([add new query]({link}))",
            list(flattened_queries.keys()),
        )

        # Combine selected queries
        selected_query_dict = {}
        for mode in defined_query_modes:
            selected_query_dict.update(flattened_queries[mode])

        # Show query editor in sidebar if queries are selected
        custom_queries = {}
        run_button = False

        if selected_query_dict:
            st.markdown("### Query Editor")
            # Editable table for selected queries
            editable_df = pd.DataFrame(
                [{"name": name, "query": query} for name, query in selected_query_dict.items()]
            )

            with st.expander("Edit Queries", expanded=True):
                edited_df = st.data_editor(
                    editable_df,
                    num_rows="dynamic",
                    width='content',
                    height=300
                )


            # Update custom queries
            def get_custom_queries(df):
                return {
                    row["name"]: row["query"]
                    for _, row in df.iterrows()
                    if row["name"] and row["query"]
                }


            custom_queries = get_custom_queries(edited_df)
    else:
        st.info("- HNRC cohort samples of 10 cognitively impaired, 10 non impaired pacients, all from the HIV+ group\n" \
                "- **Executed Queries**: Bile acids (stage 1) queries\n" \
                "- [Go to FBMN job](https://gnps2.org/status?task=fa064fe728814f439a1cd3b72deffcd0)")
        
    run_button = st.button("Run Analysis", icon=":material/play_arrow:",type="primary", width='content')

    # Reset results button
    if st.session_state.results_ready:
        if st.button("New Analysis", icon=":material/replay:", width='content'):
            st.session_state.results_ready = False
            st.session_state.analysis_results = None
            st.cache_data.clear()
            st.rerun()

    st.subheader("Contributors")
    st.markdown(
        """
    - [Helena Russo PhD](https://sites.google.com/view/helenamrusso/home) - UC San Diego
    - [Wilhan Nunes PhD](https://scholar.google.com/citations?user=4cPVoeIAAAAJ) - UC San Diego
    - [Mingxun Wang PhD](https://www.cs.ucr.edu/~mingxunw/) - UC Riverside
    """
    )

    st.subheader("Documentations and Resources")
    st.markdown(
        """
    [Feature Based Molecular Networking](https://wang-bioinformatics-lab.github.io/GNPS2_Documentation/fbmn/)<br>
    [MassQL documentation](https://mwang87.github.io/MassQueryLanguage_Documentation/)
    """,
        unsafe_allow_html=True,
    )

# Main page content
if not st.session_state.results_ready:
    if not run_button:
        # Show welcome page
        welcome_page()
    elif load_precomputed_demo:
        # Load precomputed demo data
        st.session_state.analysis_results = pd.read_pickle("demo_data/demo_massql_post_mn.pkl")
        st.session_state.results_ready = True
        st.rerun()
    else:
        st.title("🔬 Post Molecular Networking MassQL")
        # Run analysis was clicked
        if not task_id:
            st.error("Please enter a GNPS2 Task ID in the sidebar.")
        elif not custom_queries:
            st.error("Please select at least one query in the sidebar.")
        else:
            # Initialize a list to store the queries that were run
            executed_queries = []

            with st.spinner("Downloading files and running queries..."):
                try:
                    library_matches = gnps2_get_libray_dataframe_wrapper(task_id)
                    cleaned_mgf_path, all_scans, pepmass_list = download_and_filter_mgf(task_id)
                    mgf_path = cleaned_mgf_path
                except Exception as e:
                    st.error(f"Error downloading files: {str(e)}")
                    st.stop()

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
                all_query_results_df = all_query_results_df.rename(
                    columns={"scan_list": "#Scan#", "query": "query_validation"})

            with st.spinner("Merging and displaying results..."):
                all_query_results_df["#Scan#"] = all_query_results_df["#Scan#"].astype(str)
                library_matches["#Scan#"] = library_matches["#Scan#"].astype(str)

                library_final = pd.merge(library_matches, all_query_results_df, on="#Scan#", how="left")
                fallback_label = "Did not pass any selected query"
                library_final["query_validation"] = library_final["query_validation"].fillna(fallback_label)
                create_mirrorplot_link(library_final, task_id)

                column_order = ["mirror_link", "query_validation", "Compound_Name"]
                library_final = library_final[
                    column_order + [col for col in library_final.columns if
                             col not in column_order]]

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

                # Create full table
                all_scans_df = pd.DataFrame({'#Scan#': all_scans})
                all_scans_df['#Scan#'] = all_scans_df['#Scan#'].astype(str)
                all_scans_df['pepmass'] = pepmass_list

                full_table = pd.merge(all_scans_df, all_query_results_df, on='#Scan#', how='left')
                full_table = pd.merge(full_table, library_matches, on='#Scan#', how='left')
                full_table['query_validation'] = full_table['query_validation'].fillna(fallback_label)
                create_mirrorplot_link(full_table, task_id)

                # Allow multiple queries per scan in the full table
                col_order = ['#Scan#', 'pepmass', 'mirror_link', 'query_validation', 'Compound_Name']
                full_table = full_table.groupby("#Scan#", as_index=False).agg(
                    {
                        "query_validation": lambda x: ", ".join(set(x)),
                        **{
                            col: "first"
                            for col in full_table.columns
                            if col not in col_order
                        },
                    }
                )

                # Clean up temporary files
                feather_files = glob.glob("temp_mgf/*.feather")
                for file in feather_files:
                    try:
                        os.remove(file)
                    except Exception as e:
                        st.warning(f"Could not delete {file}: {e}")

                # Store results in session state
                st.session_state.analysis_results = {
                    'library_final': library_final,
                    'full_table': full_table,
                    'executed_queries': executed_queries,
                    'task_id': task_id
                }
                st.session_state.results_ready = True
                # #save results to a pickle for faster reload during demo
                # pd.to_pickle(st.session_state.analysis_results, "demo_data/demo_massql_post_mn.pkl")

            st.success("Analysis complete!", icon="✅")
            st.rerun()

else:
    # Display results
    results = st.session_state.analysis_results
    library_final = results['library_final']
    full_table = results['full_table']
    executed_queries = results['executed_queries']
    task_id = results['task_id']

    st.title(f"⚖️ MassQL Results")

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
        st.dataframe(library_final, width='content', column_config={
            "mirror_link": st.column_config.LinkColumn("Mirror plot", width='small', display_text="View")})

        # Build a multi-line header: one item per line as "key<TAB>value"
        header_lines = [f"task_id\t{task_id}"]
        for eq in executed_queries:
            try:
                name, q = eq.split(":", 1)
                name = name.strip()
                # sanitize value: remove tabs/newlines to keep TSV integrity
                q = q.strip().replace('\t', ' ').replace('\n', ' ')
                header_lines.append(f"{name}\t{q}")
            except Exception:
                # If parsing fails, skip this entry
                continue

        header_text = "\n".join(header_lines) + "\n"
        library_download = header_text + "\n" + library_final.to_csv(sep='\t', index=False)
        b64 = base64.b64encode(library_download.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="library_matches.tsv">Download TSV table</a>'
        st.markdown(href, unsafe_allow_html=True)

        # Summary for library table
        st.markdown("#### Summary for Library Table")
        total_library_matches = library_final['#Scan#'].nunique()
        st.write(f"Total number of scans that matched with the library: {total_library_matches}")
        query_summary_library = library_final.groupby('query_validation')['#Scan#'].nunique().reset_index()

        st.write("Number of scans that matched each query:")
        st.dataframe(query_summary_library.rename(columns={"#Scan#": "Number of Scans"}), width='content',
                     column_config={
                         "mirror_link": st.column_config.LinkColumn("Mirror plot", width='small', display_text="View")}
                     )

    with tab2:
        st.markdown("## Full Table With All Scans")
        st.dataframe(full_table, width='content',
                     column_config={
                         "mirror_link": st.column_config.LinkColumn("Mirror plot", width='small', display_text="View")}
                     )

        # Prepend the same multi-line header to the full table TSV
        header_lines = [f"task_id\t{task_id}"]
        for eq in executed_queries:
            try:
                name, q = eq.split(":", 1)
                name = name.strip()
                q = q.strip().replace('\t', ' ').replace('\n', ' ')
                header_lines.append(f"{name}\t{q}")
            except Exception:
                continue

        header_text = "\n".join(header_lines) + "\n"
        full_download = header_text + "\n" + full_table.to_csv(sep='\t', index=False)
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
        st.dataframe(query_summary_full, width='content')

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

    st.subheader("Download MGF with validated scans")

    if st.button("Generate MGF with validated scans", type="primary", icon=":material/manufacturing:"):
        buf = insert_mgf_info(task_id, f'./temp_mgf/{task_id}_mgf_cleaned.mgf',
                              full_table[["#Scan#", "query_validation"]].astype(str))
        st.download_button(
            label="Download validated MGF",
            data=buf.getvalue(),
            file_name=f"{task_id}_validated_scans.mgf",
            mime="txt/plain",
            icon=":material/download:"
        )
