import streamlit as st
import requests
import pandas as pd
from massql import msql_engine
import ast
import os
import glob

st.title("Validation of matches from the GNPS-BILE-ACID-MODIFICATIONS library using MassQL")

# Input task ID
task_id = st.text_input("Enter an FBMN GNPS2 Task ID", placeholder='task ID')

if st.button("Run Analysis"):
    with st.spinner("Downloading and filtering MGF file..."):
        # Load library matches
        library_matches = pd.read_csv(
            f'https://gnps2.org/resultfile?task={task_id}&file=nf_output/library/merged_results_with_gnps.tsv', sep='\t'
        )

        library_matches_BA = library_matches[library_matches['LibraryName'] == 'GNPS-BILE-ACID-MODIFICATIONS.mgf']
        features_candidates = library_matches_BA['#Scan#'].astype(str).unique().tolist()

        # Download MGF file
        mgf_url = f'https://gnps2.org/result?task={task_id}&viewname=specms&resultdisplay_type=task'
        response = requests.get(mgf_url)

        os.makedirs('temp_mgf', exist_ok=True)
        mgf_path = 'temp_mgf/mgf_all.mgf'
        filtered_mgf_path = 'temp_mgf/mgf_filtered.mgf'

        with open(mgf_path, 'wb') as fout:
            fout.write(response.content)

        # Filter MGF file
        with open(mgf_path, 'r') as fin, open(filtered_mgf_path, 'w') as fout:
            keep = False
            temp = []
            for line in fin:
                if not (line[0].isdigit() or line.startswith("END IONS")):
                    temp.append(line)
                    if line.startswith('SCANS'):
                        ID = line.strip().split('=')[1]
                        keep = ID in features_candidates
                        continue
                else:
                    if keep:
                        for item in temp:
                            fout.write(item)
                        temp = []
                        fout.write(line)
                        if line.startswith("END IONS"):
                            keep = False
                    else:
                        temp = []

    ALL_MASSQL_QUERIES = {
        'nonhydroxy_stage1': 'QUERY scaninfo(MS2DATA) WHERE MS2PROD=343.30:TOLERANCEMZ=0.01:INTENSITYPERCENT=5 AND MS2PROD=325.29:TOLERANCEMZ=0.01:INTENSITYPERCENT=5',
        'monohydroxy_stage1': 'QUERY scaninfo(MS2DATA) WHERE MS2PROD=341.28:TOLERANCEMZ=0.01:INTENSITYPERCENT=5 AND MS2PROD=323.27:TOLERANCEMZ=0.01:INTENSITYPERCENT=5',
        'dihydroxy_stage1': 'QUERY scaninfo(MS2DATA) WHERE MS2PROD=339.27:TOLERANCEMZ=0.01:INTENSITYPERCENT=5 AND MS2PROD=321.26:TOLERANCEMZ=0.01:INTENSITYPERCENT=5',
        'trihydroxy_stage1': 'QUERY scaninfo(MS2DATA) WHERE MS2PROD=337.25:TOLERANCEMZ=0.01:INTENSITYPERCENT=5 AND MS2PROD=319.24:TOLERANCEMZ=0.01:INTENSITYPERCENT=5',
        'tetrahydroxy_stage1': 'QUERY scaninfo(MS2DATA) WHERE MS2PROD=335.24:TOLERANCEMZ=0.01:INTENSITYPERCENT=5 AND MS2PROD=317.23:TOLERANCEMZ=0.01:INTENSITYPERCENT=5',
        'pentahydroxy_stage1': 'QUERY scaninfo(MS2DATA) WHERE MS2PROD=333.22:TOLERANCEMZ=0.01:INTENSITYPERCENT=5 AND MS2PROD=315.21:TOLERANCEMZ=0.01:INTENSITYPERCENT=5'
    }

    with st.spinner("Running MassQL queries..."):
        out_df = []
        for query_name, input_query in ALL_MASSQL_QUERIES.items():
            results_df = msql_engine.process_query(input_query, filtered_mgf_path)
            if len(results_df) == 0:
                out_df.append({'query': query_name, 'scan_list': 'NA'})
            else:
                passed_scan_ls = results_df['scan'].values.tolist()
                passed_scan_ls = [int(x) for x in passed_scan_ls]
                out_df.append({'query': query_name, 'scan_list': passed_scan_ls})

        out_df = pd.DataFrame(out_df)
        # out_df = out_df.dropna(subset=["scan_list"])
        out_df["scan_list"] = out_df["scan_list"].replace("NA", "[]")
        out_df['scan_list'] = out_df['scan_list'].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) else x
        )
        out_df = out_df.explode('scan_list')
        out_df = out_df.rename(columns={'scan_list': '#Scan#', 'query': 'query_validation'})

    with st.spinner("Merging and displaying results..."):
        library_final = pd.merge(library_matches_BA, out_df, on='#Scan#', how='left')
        library_final['query_validation'] = library_final['query_validation'].fillna('Did not pass any BA query (stage1)')
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
        st.success("Analysis complete!")
        st.dataframe(library_final)

        # Summary
        total_rows = len(library_final)
        no_pass_rows = (library_final['query_validation'] == 'Did not pass any BA query (stage1)').sum()
        pass_rows = (library_final['query_validation'] != 'Did not pass any BA query (stage1)').sum()
        st.markdown(f"**Total entries:** {total_rows}")
        st.markdown(f"**Entries that pass any BA query (stage1):** {pass_rows}")
        st.markdown(f"**Entries that did not pass any BA query (stage1):** {no_pass_rows}")

        st.download_button(
            label="Download Results TSV",
            data=library_final.to_csv(sep='\t', index=False).encode('utf-8'),
            file_name='library_final.tsv',
            mime='text/tab-separated-values'
        )

        # Cleanup feather files
        feather_files = glob.glob("temp_mgf/*.feather")
        for file in feather_files:
            try:
                os.remove(file)
                st.info(f"Deleted feather file: {file}")
            except Exception as e:
                st.warning(f"Could not delete {file}: {e}")
