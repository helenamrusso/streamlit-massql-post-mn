import streamlit as st


def welcome_page():
    st.title("🔬 Post Molecular Networking MassQL")
    st.markdown("""
    ### 📖 Citations
    **MassQL and Compendium queries:**  
    Damiani, T., Jarmusch, A.K., Aron, A.T., Petras, D., et al. (2025).  
    **A universal language for finding mass spectrometry data patterns**  
    *Nature Methods*, 22(6), 1247–1254. doi: [10.1038/s41592-025-02660-z](https://doi.org/10.1038/s41592-025-02660-z)
    
    **Bile acid queries:**  
    Mohanty, I., Mannochio-Russo, H., Schweer, J.V., et al. (2024).  
    **The underappreciated diversity of bile acid modifications**  
   *Cell*, 187(7), 1801–1818.e20. doi: [10.1016/j.cell.2024.02.019](https://doi.org/10.1016/j.cell.2024.02.019)
    
    **N-acyl lipids queries:**  
    Mannochio-Russo, H., Charron-Lamoureux, V., van Faassen, M., et al. (2025).  
    **The microbiome diversifies long- to short-chain fatty acid-derived N-acyl lipids**  
    *Cell*, 188(15), 4154–4169.e19. doi: [10.1016/j.cell.2025.05.015](https://doi.org/10.1016/j.cell.2025.05.015)

    ### 🧭 Purpose
    This app is designed to **contextualize GNPS molecular networking results** using MassQL (Mass Spectrometry Query Language). It enables interpretation of spectral data by applying **predefined or custom queries** to identify specific molecular patterns and chemical features.

    ### 📘 How It Works
    1. **Enter a GNPS2 task ID from Feature-Based or Classical Molecular Networking**
    2. Select from curated query collections, edit them for your needs or create custom MassQL queries
    3. The app downloads your MGF files and executes the selected queries
    4. Results are matched against spectral library annotations
    5. Outputs are organized in interactive tables with summary statistics

    ### 🧩 Key Features
    - 🔍 **Curated Query Collections**: Pre-built queries for bile acids, N-acyl lipids, and metabolomics patterns
    - 🧠 **Custom Query Support**: Create and edit your own MassQL queries
    - 🧬 **Library Integration**: Automatically merge results with GNPS spectral library matches
    - 📊 **Interactive Results**: Sortable, filterable tables with downloadable outputs

    ### 🧪 Example Dataset
    To explore the functionality without inputting your own data, use the **"Load example"** checkbox in the sidebar.

    ### 🔗 Related Tools
    - [Multi-step MassQL](https://multistep-massql.gnps2.org/): advanced chained MassQL queries execution

    ---    
    """)
    st.info("""
    - This application is part of the GNPS downstream analysis ecosystem known as **MetaboApps**.
    - If you encounter any issues or have suggestions, please reach out to the app maintainers.
    - [Checkout other tools](https://wang-bioinformatics-lab.github.io/GNPS2_Documentation/toolindex/#gnps2-web-tools)
    """)