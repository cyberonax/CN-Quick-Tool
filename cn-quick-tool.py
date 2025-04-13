import streamlit as st
import pandas as pd
import requests
import zipfile
import io

# -----------------------
# HELPER FUNCTION TO DOWNLOAD & EXTRACT ZIP
# -----------------------
def download_and_extract_zip(url):
    """Downloads a zip file from the given URL and returns its first file as a DataFrame."""
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        st.error(f"Error downloading file from {url}: {e}")
        return None

    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            file_list = z.namelist()
            if not file_list:
                st.error("The zip file is empty.")
                return None
            file_name = file_list[0]
            with z.open(file_name) as file:
                df = pd.read_csv(file, delimiter="|", encoding="ISO-8859-1")
                return df
    except Exception as e:
        st.error(f"Error reading the CSV file: {e}")
        return None

# -----------------------
# MAIN STREAMLIT APP
# -----------------------
st.title("Ruler Info & Nation Drill Link Filter")
st.markdown(
    """
    This tool downloads nation statistics and extracts a list of all Ruler Names alongside their Alliance, 
    Team, and Nation Drill Link. The Nation Drill Link is built by combining the base URL with the Nation ID.
    
    **Base Nation Drill URL:**  
    `https://www.cybernations.net/nation_drill_display.asp?Nation_ID=`
    
    Paste one or more Ruler Names (each on a new line) into the text box below to filter the table.
    """
)

# You can change the following URL to the correct link for your download. For example, if using a dated file:
# base_url = "https://www.cybernations.net/assets/CyberNations_SE_Nation_Stats_"
# zip_url = base_url + "01012020.zip"
zip_url = "https://www.cybernations.net/assets/CyberNations_SE_Nation_Stats_EXAMPLE.zip"

if st.button("Download Nation Data"):
    with st.spinner("Downloading and processing data..."):
        df = download_and_extract_zip(zip_url)
        if df is not None:
            st.session_state.df = df
            st.success("Data downloaded successfully!")
        else:
            st.error("Failed to load data.")

# Proceed if data is available in the session state
if "df" in st.session_state:
    df = st.session_state.df.copy()

    # Ensure the Nation ID is a string so we can build the URL
    if "Nation ID" in df.columns:
        df["Nation ID"] = df["Nation ID"].astype(str)
    else:
        st.error("Column 'Nation ID' was not found in the data!")

    # Create the Nation Drill Link column
    base_drill_url = "https://www.cybernations.net/nation_drill_display.asp?Nation_ID="
    df["Nation Drill Link"] = base_drill_url + df["Nation ID"]

    # Select only the necessary columns to display
    display_cols = ["Ruler Name", "Alliance", "Team", "Nation Drill Link"]

    st.markdown("### All Nation Ruler Information")
    st.dataframe(df[display_cols], use_container_width=True)

    st.markdown("### Filter by Ruler Names")
    st.markdown("Paste one or more Ruler Names, one per line, in the text area below:")
    ruler_input = st.text_area("Ruler Names", height=150)

    if ruler_input:
        # Process the pasted text into a list (strip blank lines)
        ruler_list = [name.strip() for name in ruler_input.splitlines() if name.strip()]
        # You can use a case-insensitive matching approach:
        filtered_df = df[df["Ruler Name"].str.lower().isin([r.lower() for r in ruler_list])]

        if not filtered_df.empty:
            st.markdown("#### Filtered Results")
            st.dataframe(filtered_df[display_cols], use_container_width=True)
        else:
            st.info("No matching ruler names found in the data.")
