import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import zipfile
import io
import re
from datetime import datetime, timedelta

# -----------------------
# HELPER FUNCTION: Combine Resource 1 and Resource 2
# -----------------------
def get_resource_1_2(row):
    """
    Combine the values from "Resource 1" and "Resource 2" into a single string.
    If either resource is missing, show only the available one.
    """
    r1 = row.get("Resource 1", "")
    r2 = row.get("Resource 2", "")
    r1 = str(r1).strip() if pd.notnull(r1) else ""
    r2 = str(r2).strip() if pd.notnull(r2) else ""
    if r1 and r2:
        return f"{r1}, {r2}"
    elif r1:
        return r1
    elif r2:
        return r2
    return ""

# -----------------------
# DOWNLOAD & DATA LOADING FUNCTIONS
# -----------------------
def download_and_extract_zip(url):
    """Download a zip file from the given URL and extract its first file as a DataFrame."""
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
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

# Callback functions to set the flag for keeping sections open.
def keep_cse_open():
    st.session_state.cse_expanded = True

def keep_alliance_open():
    st.session_state.alliance_expanded = True

def keep_trade_open():
    st.session_state.trade_circle_expanded = True

def keep_cc_open():
    st.session_state.cc_expanded = True

# -----------------------
# MAIN APP
# -----------------------
def main():
    # Initialize session state flags for controlling expander open state
    if "alliance_expanded" not in st.session_state:
        st.session_state.alliance_expanded = False
    if "trade_circle_expanded" not in st.session_state:
        st.session_state.trade_circle_expanded = False
    if "cse_expanded" not in st.session_state:
        st.session_state.cse_expanded = False
    if "cc_expanded" not in st.session_state:
        st.session_state.cc_expanded = False

    st.set_page_config(layout="wide")
    st.title("Cyber Nations | Nation Ruler Search | Quick Tool")
    
    # Brief description under the main title
    st.markdown("This tool helps you simplify returning information from your list of pasted Nation/Ruler Names. Click 'Download Nation Statistics' to proceed.")
    
    # Section: Download Nation Statistics
    if st.button("Download Nation Statistics"):
        with st.spinner("Loading data..."):
            df = load_data()
        if df is not None:
            st.session_state.df = df
        else:
            st.error("Failed to load data.")
    
    # Section: Ruler Search Interface
    if "df" in st.session_state:
        df = st.session_state.df.copy()
        
        st.subheader("Enter Nation or Ruler Names (one per line)")
        names_input = st.text_area("Paste the names here", height=150)
        
        if st.button("Search"):
            # Convert input to a list (ignoring extra whitespace and empty lines)
            filters = [name.strip() for name in names_input.splitlines() if name.strip()]
            if not filters:
                st.info("No names entered. Please paste one or more names.")
            else:
                # Convert filters to lowercase for a case-insensitive search.
                lower_filters = [f.lower() for f in filters]
                # Create a mask where either the Ruler Name or Nation Name column matches any input.
                mask = df["Ruler Name"].str.lower().isin(lower_filters) | df["Nation Name"].str.lower().isin(lower_filters)
                result_df = df[mask].copy()
                
                if result_df.empty:
                    st.info("No matching entries found. Check your input for spelling or extra spaces.")
                else:
                    # Calculate the Resource 1+2 column.
                    result_df["Resource 1+2"] = result_df.apply(get_resource_1_2, axis=1)
                    # Build the Nation Drill Link.
                    result_df["Nation Drill Link"] = (
                        "https://www.cybernations.net/nation_drill_display.asp?Nation_ID=" +
                        result_df["Nation ID"].astype(str)
                    )
                    # Reorder columns: Nation ID first.
                    display_df = result_df[["Nation ID", "Ruler Name", "Resource 1+2", "Alliance", "Team", "Nation Drill Link"]]
                    
                    st.dataframe(display_df)
                    
                    # Provide a CSV download option.
                    csv = display_df.to_csv(index=False)
                    st.download_button("Download Results as CSV", csv, file_name="ruler_search_results.csv", mime="text/csv")
    
    st.markdown("---")
    
    # -----------------------
    # COLLAPSIBLE SECTION: Process Comma-Separated Names
    # -----------------------
    with st.expander("Comma-Separated Name Processor", expanded=st.session_state.cse_expanded):
        st.markdown(
            """
            Paste a list of names, numbers, or other text below (separated by commas or new lines).

            - **Output 1:** Shows the names on separate lines.
            - **Output 2:** Shows each name wrapped in quotes with a trailing comma.
            - **Output 3:** Shows the names joined by a comma.
            """
        )
        names_input = st.text_area("Enter text", height=100, key="cse_text", on_change=keep_cse_open)
        if st.button("Generate", key="cse_generate"):
            st.session_state.cse_expanded = True  # Ensure this section stays open.
            if names_input:
                # Split the input on commas or newlines using regex.
                names_list = [name.strip() for name in re.split(r"[,\n]+", names_input) if name.strip()]
                # Output 1: Each name on its own separate line.
                output1 = "\n".join(names_list)
                # Output 2: Each name on its separate line, wrapped in quotes and appended with a comma.
                output2 = "\n".join([f'"{name}",' for name in names_list])
                # Output 3: Names joined with a comma and a space.
                output3 = ", ".join(names_list)
                
                st.text_area("Output 1 (each name on a separate line)", value=output1, height=150)
                st.text_area("Output 2 (quoted names with trailing comma)", value=output2, height=150)
                st.text_area("Output 3 (names joined by a comma)", value=output3, height=100)
    
    # -----------------------
    # COLLAPSIBLE SECTION: Alliance Member Exclusion/Inclusion Tool
    # -----------------------
    alliance_container = st.empty()
    alliance_expanded_flag = st.session_state.alliance_expanded
    with alliance_container.expander("Alliance Member Exclusion/Inclusion Tool", expanded=alliance_expanded_flag):
        st.markdown(
            """
            Enter a list of Nation or Ruler Names (one per line) below and select an alliance.
            This tool will display two tables:
            
            - **Nations in alliance not in your list:** Nations within the alliance that are missing from your input.
            - **Nations in alliance in your list:** Nations within the alliance that match your input.
            
            If no names are provided, both results will remain blank.
            """
        )
        names_alliance_input = st.text_area("Enter Nation or Ruler Names (one per line)", height=150, key="alliance_input", on_change=keep_alliance_open)
        if "df" in st.session_state:
            df = st.session_state.df.copy()
            alliance_options = sorted(df["Alliance"].dropna().unique().tolist())
            default_index = alliance_options.index("Freehold of The Wolves") if "Freehold of The Wolves" in alliance_options else 0
        else:
            alliance_options = ["Freehold of The Wolves"]
            default_index = 0

        alliance_selected = st.selectbox("Select Alliance", options=alliance_options, index=default_index, key="alliance_select")
        if st.button("Search", key="alliance_generate"):
            st.session_state.alliance_expanded = True  # Keep this section open after generation.
            if names_alliance_input:
                name_filters = [n.strip() for n in names_alliance_input.splitlines() if n.strip()]
                lower_filters = [n.lower() for n in name_filters]
            else:
                lower_filters = []
            
            if "df" in st.session_state:
                alliance_df = st.session_state.df.copy()
                alliance_df = alliance_df[alliance_df["Alliance"] == alliance_selected]
                if lower_filters:
                    mask = alliance_df["Ruler Name"].str.lower().isin(lower_filters) | alliance_df["Nation Name"].str.lower().isin(lower_filters)
                    result_not_in_list = alliance_df[~mask].copy()  # Nations in alliance not in the list
                    result_in_list = alliance_df[mask].copy()         # Nations in alliance in your list
                else:
                    result_not_in_list = pd.DataFrame()  # Blank result if no names provided.
                    result_in_list = pd.DataFrame()
                
                st.markdown("#### Nations in alliance not in your list:")
                st.dataframe(result_not_in_list)
                
                st.markdown("#### Nations in alliance in your list:")
                st.dataframe(result_in_list)
            else:
                st.info("Nation Statistics data not loaded yet. Please download the data first.")
    
    # -----------------------
    # COLLAPSIBLE SECTION: Trade Circle ID Generator
    # -----------------------
    trade_container = st.empty()
    trade_expanded_flag = st.session_state.trade_circle_expanded
    with trade_container.expander("Trade Circle ID Generator", expanded=trade_expanded_flag):
        st.markdown(
            """
            Paste a list of Nation or Ruler Names (one per line) below.
            This tool will generate a Trade Circle ID by concatenating the corresponding Nation IDs,
            ordered from smallest to largest and separated by periods.
            """
        )
        names_trade_input = st.text_area("Enter Nation or Ruler Names (one per line) for Trade Circle ID", height=150, key="trade_input", on_change=keep_trade_open)
        if st.button("Generate", key="trade_generate"):
            st.session_state.trade_circle_expanded = True  # Keep this section open after generation.
            if names_trade_input:
                name_list = [n.strip() for n in names_trade_input.splitlines() if n.strip()]
                lower_names = [n.lower() for n in name_list]
            else:
                lower_names = []
            
            if "df" in st.session_state:
                trade_df = st.session_state.df.copy()
                if lower_names:
                    mask = trade_df["Ruler Name"].str.lower().isin(lower_names) | trade_df["Nation Name"].str.lower().isin(lower_names)
                    matching_df = trade_df[mask].copy()
                    if not matching_df.empty:
                        try:
                            nation_ids = matching_df["Nation ID"].astype(int).tolist()
                        except:
                            nation_ids = matching_df["Nation ID"].tolist()
                        nation_ids_sorted = sorted(nation_ids)
                        trade_circle_id = ".".join(str(nid) for nid in nation_ids_sorted)
                        st.markdown("#### Trade Circle ID:")
                        st.code(trade_circle_id)
                    else:
                        st.info("No matching Nation or Ruler Names found in the data.")
                else:
                    st.info("Please enter one or more Nation or Ruler Names to generate a Trade Circle ID.")
            else:
                st.info("Nation Statistics data not loaded yet. Please download the data first.")
    
    # -----------------------
    # COLLAPSIBLE SECTION: Carbon Copy Rulers Tool
    # -----------------------
    with st.expander("Carbon Copy Rulers Tool", expanded=st.session_state.cc_expanded):
        st.markdown(
            """
            Select an alliance to retrieve its list of Nation Rulers.
            
            The ruler names are displayed one per line and grouped into blocks of 26 names.
            Each block is presented in its own text box with a copy-to-clipboard button.
            """
        )
        # Retrieve alliance options
        if "df" in st.session_state:
            df = st.session_state.df.copy()
            alliance_options = sorted(df["Alliance"].dropna().unique().tolist())
            default_index = alliance_options.index("Freehold of The Wolves") if "Freehold of The Wolves" in alliance_options else 0
        else:
            alliance_options = ["Freehold of The Wolves"]
            default_index = 0

        alliance_selected_cc = st.selectbox("Select Alliance", options=alliance_options, index=default_index, key="alliance_select_cc")
        if st.button("Generate", key="cc_generate", on_click=keep_cc_open):
            st.session_state.cc_expanded = True  # Ensure the section remains open after generation.
            if "df" in st.session_state:
                cc_df = st.session_state.df.copy()
                # Filter by the selected alliance
                cc_df = cc_df[cc_df["Alliance"] == alliance_selected_cc]
                # Retrieve the list of Ruler Names (non-empty) and sort them.
                rulers_list = cc_df["Ruler Name"].dropna().tolist()
                rulers_list = [ruler.strip() for ruler in rulers_list if ruler.strip()]
                rulers_list = sorted(rulers_list, key=str.lower)
                
                # Group the rulers into blocks of 26 names per block.
                groups = [rulers_list[i:i+26] for i in range(0, len(rulers_list), 26)]
                
                # Display each block in its own text box with a copy button using components.html
                for idx, group in enumerate(groups):
                    block_text = "\n".join(group)
                    unique_id = f"cc_textarea_{idx}"
                    html_block = f"""
                    <div style="margin-bottom: 20px;">
                      <textarea id="{unique_id}" style="width:100%; height:150px; background-color: #f0f0f0;" readonly="readonly">{block_text}</textarea>
                      <br>
                      <button onclick="navigator.clipboard.writeText(document.getElementById('{unique_id}').value)" style="margin-top:5px;">Copy</button>
                    </div>
                    """
                    components.html(html_block, height=200)
            else:
                st.info("Nation Statistics data not loaded yet. Please download the data first.")

if __name__ == "__main__":
    main()
