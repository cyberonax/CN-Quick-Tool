import streamlit as st
import pandas as pd
import requests
import zipfile
import io
from datetime import datetime, timedelta

# -----------------------
# DOWNLOAD & DATA LOADING FUNCTIONS
# -----------------------
def download_and_extract_zip(url):
    """Download a zip file from the given URL and extract its first file as a DataFrame."""
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        # Hide error messages by not printing them
        return None

    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            file_list = z.namelist()
            if not file_list:
                return None
            file_name = file_list[0]
            with z.open(file_name) as file:
                # Adjust delimiter and encoding as needed
                df = pd.read_csv(file, delimiter="|", encoding="ISO-8859-1")
                return df
    except Exception:
        return None

def load_data():
    """Try downloading data using a list of dates and URL patterns without showing debug messages."""
    today = datetime.now()
    base_url = "https://www.cybernations.net/assets/CyberNations_SE_Nation_Stats_"
    dates_to_try = [today, today - timedelta(days=1), today + timedelta(days=1)]
    
    for dt in dates_to_try:
        date_str = f"{dt.month}{dt.day}{dt.year}"
        url1 = base_url + date_str + "510001.zip"
        url2 = base_url + date_str + "510002.zip"
        
        df = download_and_extract_zip(url1)
        if df is None:
            df = download_and_extract_zip(url2)
        if df is not None:
            st.success(f"Data loaded successfully from date: {date_str}")
            return df
    return None

# -----------------------
# MAIN APP
# -----------------------
def main():
    st.set_page_config(layout="wide")
    st.title("Cyber Nations | Nation Ruler Tool")
    
    # Button to download and load the nation statistics data.
    if st.button("Download Nation Statistics"):
        with st.spinner("Loading data..."):
            df = load_data()
        if df is not None:
            st.session_state.df = df
        else:
            st.error("Failed to load data.")
    
    # If data has been loaded, show the ruler search interface.
    if "df" in st.session_state:
        df = st.session_state.df.copy()
        
        st.subheader("Enter Ruler Names (one per line)")
        ruler_names_input = st.text_area("Paste the ruler names here", height=150)
        
        if st.button("Search"):
            # Split the text input by newlines and remove any excess whitespace.
            rulers = [name.strip() for name in ruler_names_input.splitlines() if name.strip()]
            if not rulers:
                st.info("No ruler names entered. Please paste one or more ruler names.")
            else:
                # Convert both the input ruler names and DataFrame "Ruler Name" column to lowercase for case-insensitive comparison.
                lower_rulers = [r.lower() for r in rulers]
                result_df = df[df["Ruler Name"].str.lower().isin(lower_rulers)].copy()
                
                if result_df.empty:
                    st.info("No matching ruler names found. Check your input for spelling or extra spaces.")
                else:
                    # Construct the Nation Drill Link by combining the base URL with Nation ID.
                    result_df["Nation Drill Link"] = (
                        "https://www.cybernations.net/nation_drill_display.asp?Nation_ID=" +
                        result_df["Nation ID"].astype(str)
                    )
                    # Select just the columns we need.
                    display_df = result_df[["Ruler Name", "Alliance", "Team", "Nation Drill Link"]]
                    
                    # Display the results in a table.
                    st.dataframe(display_df)
                    
                    # Provide a CSV download option.
                    csv = display_df.to_csv(index=False)
                    st.download_button("Download Results as CSV", csv, file_name="ruler_search_results.csv", mime="text/csv")

if __name__ == "__main__":
    main()
