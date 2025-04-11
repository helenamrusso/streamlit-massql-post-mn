import streamlit as st
import requests
import pandas as pd
from massql import msql_engine
from queries import *
import ast
import os
import glob

st.title("Post Molecular Networking MassQL")

# Input task ID
task_id = st.text_input("Enter GNPS2 Task ID", placeholder='Enter a GNPS2 task ID')

# Use selectbox to choose bile acid stage type
defined_query_mode = st.selectbox(
    "Select query mode",
    ["Bile acids (stage 1) queries", "Bile acids (stage 2) queries", "N-acyl lipids queries", "Manual entry",
    '(Compedium) Doubly charged compounds ([M+H]+ within 600-1200 m/z)',
    '(Compedium) Catecholate metallophores',
    '(Compedium) Novel Albicidin Derivatives via Pseudo Precursor Ion, Pseudo Neutral Loss, and Sequence Tag Scan',
    '(Compedium) Search for two product ions with specific m/z delta',
    '(Compedium) Find a protonated precursor by searching for the presence of M+Na',
    '(Compedium) Organophosphate Compounds in the Environment',
    '(Compedium) Detection of Fusaricidin Depsipeptides',
    '(Compedium) Glycerophosphocholine Lipids',
    '(Compedium) Metabolism of Antibiotic Trimethoprim',
    '(Compedium) Cannabidiol Degradation Products',
    '(Compedium) Quorum Signal Synthases from Predatory Myxobacteria',
    '(Compedium) Aminoglycosidic Compounds in Natural Products',
    '(Compedium) Gallic acid derivatives',
    '(Compedium) Cupriachelins',
    '(Compedium) biarylitide A - peptidegenomics',
    '(Compedium) Liver Metabolism of Xenobiotics - metabolic transformation of mitragynine',
    '(Compedium) Malonyl Glucose Conjugates',
    '(Compedium) Sulfatome',
    '(Compedium) glycosylated macrolides',
    '(Compedium) Piperamides',
    '(Compedium) Glycoalkaloids',
    '(Compedium) Homoserine Lactone',
    '(Compedium) Desferioxamine Building Blocks',
    '(Compedium) Acylcarnitines',
    '(Compedium) O-pentoglycosides (arabinose, rhamnose)',
    '(Compedium) Sulfur-containing Perfluorinated Compounds',
    '(Compedium) diphenyl cation and glucuronidation',
    '(Compedium) Polybrominated analogs',
    '(Compedium) Perfluoroalkyl and Polyfluoroalkyl Substances (PFAS) with Ion Mobility',
    '(Compedium) Identification of cyclic peptide analytes in plant metabolomes'
     ]
)

# Default editable table for manual entry
custom_queries_df = pd.DataFrame([
    {"name": "query1", "query": ""},
])

# Inicializar ALL_MASSQL_QUERIES antes de seu uso
ALL_MASSQL_QUERIES = {
    "Bile acids (stage 1) queries": bile_acid_queries_stage1,
    "Bile acids (stage 2) queries": bile_acid_queries_stage2,
    "N-acyl lipids queries": n_acyl_lipids_queries,
    "Manual entry": {},
    '(Compedium) Doubly charged compounds ([M+H]+ within 600-1200 m/z)': compedium_1,
    '(Compedium) Catecholate metallophores': compedium_2,
    '(Compedium) Novel Albicidin Derivatives via Pseudo Precursor Ion, Pseudo Neutral Loss, and Sequence Tag Scan': compedium_3,
    '(Compedium) Search for two product ions with specific m/z delta': compedium_4,
    '(Compedium) Find a protonated precursor by searching for the presence of M+Na': compedium_5,
    '(Compedium) Organophosphate Compounds in the Environment': compedium_6,
    '(Compedium) Detection of Fusaricidin Depsipeptides': compedium_7,
    '(Compedium) Glycerophosphocholine Lipids': compedium_8,
    '(Compedium) Metabolism of Antibiotic Trimethoprim': compedium_9,
    '(Compedium) Cannabidiol Degradation Products': compedium_10,
    '(Compedium) Quorum Signal Synthases from Predatory Myxobacteria': compedium_11,
    '(Compedium) Aminoglycosidic Compounds in Natural Products': compedium_12,
    '(Compedium) Gallic acid derivatives': compedium_13,
    '(Compedium) Cupriachelins': compedium_14,
    '(Compedium) biarylitide A - peptidegenomics': compedium_15,
    '(Compedium) Liver Metabolism of Xenobiotics - metabolic transformation of mitragynine': compedium_16,
    '(Compedium) Malonyl Glucose Conjugates': compedium_17,
    '(Compedium) Sulfatome': compedium_18,
    '(Compedium) glycosylated macrolides': compedium_19,
    '(Compedium) Piperamides': compedium_20,
    '(Compedium) Glycoalkaloids': compedium_21,
    '(Compedium) Homoserine Lactone': compedium_22,
    '(Compedium) Desferioxamine Building Blocks': compedium_23,
    '(Compedium) Acylcarnitines': compedium_24,
    '(Compedium) O-pentoglycosides (arabinose, rhamnose)': compedium_25,
    '(Compedium) Sulfur-containing Perfluorinated Compounds': compedium_26,
    '(Compedium) diphenyl cation and glucuronidation': compedium_27,
    '(Compedium) Polybrominated analogs': compedium_28,
    '(Compedium) Perfluoroalkyl and Polyfluoroalkyl Substances (PFAS) with Ion Mobility': compedium_29,
    '(Compedium) Identification of cyclic peptide analytes in plant metabolomes': compedium_30,
}

# Inicializar DataFrame para edição
if defined_query_mode == "Manual entry":
    st.markdown("### Custom MassQL Queries (table format)")
    st.markdown("Fill in the **name** and the corresponding **MassQL query** below:")
    editable_df = custom_queries_df
else:
    st.markdown(f"### Predefined Queries for: {defined_query_mode}")
    predefined_queries = ALL_MASSQL_QUERIES.get(defined_query_mode, {})
    editable_df = pd.DataFrame([
        {"name": query_name, "query": query}
        for query_name, query in predefined_queries.items()
    ])

# Exibir editor de tabela
edited_df = st.data_editor(editable_df, num_rows="dynamic", use_container_width=True)

# Atualizar consultas personalizadas com base nas edições
custom_queries = {
    row["name"]: row["query"]
    for _, row in edited_df.iterrows()
    if row["name"] and row["query"]
}

# Detectar modificações em consultas predefinidas
queries_modified = False
if defined_query_mode != "Manual entry":
    for _, row in edited_df.iterrows():
        original_query = predefined_queries.get(row["name"], "")
        if row["query"] != original_query:
            queries_modified = True
            break

    # Atualizar modo para "Manual entry" se houver modificações
    if queries_modified:
        st.warning("Queries modified. Updating dropdown menu to 'Manual entry'.")
        defined_query_mode = "Manual entry"

# Atualizar conjunto de consultas a ser usado
ALL_MASSQL_QUERIES = {
    "Bile acids (stage 1) queries": bile_acid_queries_stage1,
    "Bile acids (stage 2) queries": bile_acid_queries_stage2,
    "N-acyl lipids queries": n_acyl_lipids_queries,
    "Manual entry": custom_queries,
    '(Compedium) Doubly charged compounds ([M+H]+ within 600-1200 m/z)': compedium_1,
    '(Compedium) Catecholate metallophores': compedium_2,
    '(Compedium) Novel Albicidin Derivatives via Pseudo Precursor Ion, Pseudo Neutral Loss, and Sequence Tag Scan': compedium_3,
    '(Compedium) Search for two product ions with specific m/z delta': compedium_4,
    '(Compedium) Find a protonated precursor by searching for the presence of M+Na': compedium_5,
    '(Compedium) Organophosphate Compounds in the Environment': compedium_6,
    '(Compedium) Detection of Fusaricidin Depsipeptides': compedium_7,
    '(Compedium) Glycerophosphocholine Lipids': compedium_8,
    '(Compedium) Metabolism of Antibiotic Trimethoprim': compedium_9,
    '(Compedium) Cannabidiol Degradation Products': compedium_10,
    '(Compedium) Quorum Signal Synthases from Predatory Myxobacteria': compedium_11,
    '(Compedium) Aminoglycosidic Compounds in Natural Products': compedium_12,
    '(Compedium) Gallic acid derivatives': compedium_13,
    '(Compedium) Cupriachelins': compedium_14,
    '(Compedium) biarylitide A - peptidegenomics': compedium_15,
    '(Compedium) Liver Metabolism of Xenobiotics - metabolic transformation of mitragynine': compedium_16,
    '(Compedium) Malonyl Glucose Conjugates': compedium_17,
    '(Compedium) Sulfatome': compedium_18,
    '(Compedium) glycosylated macrolides': compedium_19,
    '(Compedium) Piperamides': compedium_20,
    '(Compedium) Glycoalkaloids': compedium_21,
    '(Compedium) Homoserine Lactone': compedium_22,
    '(Compedium) Desferioxamine Building Blocks': compedium_23,
    '(Compedium) Acylcarnitines': compedium_24,
    '(Compedium) O-pentoglycosides (arabinose, rhamnose)': compedium_25,
    '(Compedium) Sulfur-containing Perfluorinated Compounds': compedium_26,
    '(Compedium) diphenyl cation and glucuronidation': compedium_27,
    '(Compedium) Polybrominated analogs': compedium_28,
    '(Compedium) Perfluoroalkyl and Polyfluoroalkyl Substances (PFAS) with Ion Mobility': compedium_29,
    '(Compedium) Identification of cyclic peptide analytes in plant metabolomes': compedium_30,
}[defined_query_mode]

if st.button("Run Analysis"):
    # Initialize a list to store the queries that were run
    executed_queries = []

    with st.spinner("Downloading files and running queries..."):
        library_matches = pd.read_csv(
            f'https://gnps2.org/resultfile?task={task_id}&file=nf_output/library/merged_results_with_gnps.tsv', sep='\t')

        mgf_url = f'https://gnps2.org/result?task={task_id}&viewname=specms&resultdisplay_type=task'
        response = requests.get(mgf_url)

        os.makedirs('temp_mgf', exist_ok=True)
        mgf_path = 'temp_mgf/mgf_all.mgf'

        with open(mgf_path, 'wb') as fout:
            fout.write(response.content)

        ## Extract all scan numbers from the MGF file
        all_scans = []
        valid_scans = []
        with open(mgf_path, 'r') as mgf_file:
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
                # Check if the scan contains valid peak data (lines with two numeric values separated by whitespace)
                if any(
                    len(peak.split()) == 2 and all(part.replace('.', '', 1).isdigit() for part in peak.split())
                    for peak in current_scan
                ):
                    cleaned_mgf_lines.extend(current_scan)
                inside_scan = False
            elif inside_scan:
                current_scan.append(line)
            else:
                cleaned_mgf_lines.append(line)

        # Save the cleaned MGF file
        cleaned_mgf_path = 'temp_mgf/mgf_cleaned.mgf'
        with open(cleaned_mgf_path, 'w') as fout:
            fout.writelines(cleaned_mgf_lines)

        # Update the path to use the cleaned MGF file
        mgf_path = cleaned_mgf_path

        # Extract all scan numbers from the cleaned MGF file
        with open(mgf_path, 'r') as mgf_file:
            for line in mgf_file:
                if line.startswith("SCANS="):
                    all_scans.append(line.strip().split('=')[1])

    with st.spinner("Running MassQL queries...\nThis may take a while, please be patient!"):
        out_df = []
        for query_name, input_query in ALL_MASSQL_QUERIES.items():
            st.write(f"Running query: {query_name}")
            executed_queries.append(f"{query_name}: {input_query}")
            try:
                results_df = msql_engine.process_query(input_query, mgf_path)
            except KeyError:
                results_df = pd.DataFrame()

            if len(results_df) == 0:
                out_df.append({'query': query_name, 'scan_list': 'NA'})
            else:
                passed_scan_ls = results_df['scan'].values.tolist()
                passed_scan_ls = [int(x) for x in passed_scan_ls]
                out_df.append({'query': query_name, 'scan_list': passed_scan_ls})

        out_df = pd.DataFrame(out_df)
        out_df["scan_list"] = out_df["scan_list"].replace("NA", "[]")
        out_df['scan_list'] = out_df['scan_list'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        out_df = out_df.explode('scan_list')
        out_df = out_df.rename(columns={'scan_list': '#Scan#', 'query': 'query_validation'})

    with st.spinner("Merging and displaying results..."):
        out_df['#Scan#'] = out_df['#Scan#'].astype(str)
        library_matches['#Scan#'] = library_matches['#Scan#'].astype(str)

        # Allow multiple queries to be associated with the same scan
        library_final = pd.merge(library_matches, out_df, on='#Scan#', how='left')

        # Dynamically generate fallback_label based on the selected query mode
        fallback_label = f"Did not pass any query from {defined_query_mode}"

        library_final['query_validation'] = library_final['query_validation'].fillna(fallback_label)

        col_order = ['query_validation', '#Scan#', 'Compound_Name', 'SpectrumID', 'SpectrumFile', 'LibraryName', 'MQScore',
           'TIC_Query', 'RT_Query', 'MZErrorPPM', 'SharedPeaks', 'MassDiff',
           'SpecMZ', 'SpecCharge', 'FileScanUniqueID', 'NumberHits',
           'Ion_Source', 'Instrument', 'Compound_Source', 'PI',
           'Data_Collector', 'Adduct', 'Precursor_MZ', 'ExactMass', 'Charge',
           'CAS_Number', 'Pubmed_ID', 'Smiles', 'INCHI', 'INCHI_AUX',
           'Library_Class', 'IonMode', 'Organism', 'LibMZ', 'UpdateWorkflowName',
           'LibraryQualityString', 'tags', 'molecular_formula', 'InChIKey',
           'InChIKey-Planar', 'superclass', 'class', 'subclass',
           'npclassifier_superclass', 'npclassifier_class', 'npclassifier_pathway',
           'library_usi']

        library_final = library_final[col_order]
        library_final = library_final.groupby('#Scan#', as_index=False).agg({
            'query_validation': lambda x: ', '.join(set(x)),
            **{col: 'first' for col in library_final.columns if col not in ['#Scan#', 'query_validation']}
        })

        st.success("Analysis complete!")
        st.markdown("## Table With Library Matches Only")
        st.dataframe(library_final)

        # Summary for library table
        st.markdown("#### Summary for Library Table")
        total_library_matches = library_final['#Scan#'].nunique()
        st.write(f"Total number of scans that matched with the library: {total_library_matches}")
        query_summary_library = library_final.groupby('query_validation')['#Scan#'].nunique()
        st.write("Number of scans that matched each query:")
        st.dataframe(query_summary_library)

        # Download buttons for both tables
        st.download_button(
            label="Download Results TSV",
            data=library_final.to_csv(sep='\t', index=False).encode('utf-8'),
            file_name='library_final.tsv',
            mime='text/tab-separated-values'
        )

        # Create a full table with all scans
        all_scans_df = pd.DataFrame({'#Scan#': all_scans})
        all_scans_df['#Scan#'] = all_scans_df['#Scan#'].astype(str)

        full_table = pd.merge(all_scans_df, library_final, on='#Scan#', how='left')
        full_table['query_validation'] = full_table['query_validation'].fillna(fallback_label)

        # Allow multiple queries per scan in the full table
        full_table = full_table.groupby(['#Scan#', 'query_validation'], as_index=False).first()

        st.markdown("## Full Table With All Scans")
        st.dataframe(full_table)

        # Summary for full table
        st.markdown("#### Summary for Full Table")
        total_full_matches = full_table['#Scan#'].nunique()
        st.write(f"Total number of scans in the full table: {total_full_matches}")
        query_summary_full = full_table.groupby('query_validation')['#Scan#'].nunique()
        st.write("Number of scans that matched each query in the full table:")
        st.dataframe(query_summary_full)

        st.download_button(
            label="Download Full Table TSV",
            data=full_table.to_csv(sep='\t', index=False).encode('utf-8'),
            file_name='full_table.tsv',
            mime='text/tab-separated-values'
        )

        # Display the executed queries at the end
        st.markdown("## Executed Queries")
        st.text_area('All queries:', value='\n\n'.join(executed_queries), height=300)

        feather_files = glob.glob("temp_mgf/*.feather")
        for file in feather_files:
            try:
                os.remove(file)
            except Exception as e:
                st.warning(f"Could not delete {file}: {e}")
