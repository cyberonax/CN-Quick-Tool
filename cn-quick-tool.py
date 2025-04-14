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
    
    st.markdown("This tool simplifies returning information from your list of pasted Nation/Ruler Names.")
    
    # Auto-download Nation Statistics data on app load.
    if "df" not in st.session_state:
        with st.spinner("Loading data..."):
            df = load_data()
        if df is not None:
            st.session_state.df = df
        else:
            st.error("Failed to load data.")
    
    # -----------------------
    # COLLAPSIBLE SECTION: Ruler Search Interface
    # -----------------------
    with st.expander("Ruler Search Interface", expanded=True):
        st.subheader("Enter Nation or Ruler Names (one per line)")
        names_input = st.text_area("Paste the names here", height=150)
        
        if st.button("Search", key="ruler_search"):
            if not names_input.strip():
                st.info("No names entered. Please paste one or more names.")
            else:
                # Primary lookup: build a list from non-blank input lines for the main table.
                filters = [name.strip() for name in names_input.splitlines() if name.strip()]
                lower_filters = [f.lower() for f in filters]
                df = st.session_state.df.copy()
                mask = df["Ruler Name"].str.lower().isin(lower_filters) | df["Nation Name"].str.lower().isin(lower_filters)
                result_df = df[mask].copy()
                
                if result_df.empty:
                    st.info("No matching entries found. Check your input for spelling or extra spaces.")
                else:
                    # Calculate additional columns for the main output.
                    result_df["Resource 1+2"] = result_df.apply(get_resource_1_2, axis=1)
                    result_df["Nation Drill Link"] = (
                        "https://www.cybernations.net/nation_drill_display.asp?Nation_ID=" +
                        result_df["Nation ID"].astype(str)
                    )
                    result_df["Created_dt"] = pd.to_datetime(result_df["Created"], errors='coerce')
                    result_df["Days Old"] = (pd.Timestamp.now() - result_df["Created_dt"]).dt.days
                    
                    # Reorder columns: Nation ID, Ruler Name, Resource 1+2, Alliance, Team, Days Old, Nation Drill Link.
                    display_df = result_df[["Nation ID", "Ruler Name", "Resource 1+2", "Alliance", "Team", "Days Old", "Nation Drill Link"]]
                    st.dataframe(display_df)
                    
                    # Provide a CSV download option.
                    csv = display_df.to_csv(index=False)
                    st.download_button("Download Results as CSV", csv, file_name="ruler_search_results.csv", mime="text/csv")
                    
                    # -----------------------
                    # NEW: Alternative Format Output as a Table with Copy Button
                    # -----------------------
                    st.markdown("### Alternative Format Output")
                    st.markdown(
                        """
                        This table preserves the original grouping and blank lines as entered.
                        For each non-empty line:
                        
                        - If a match is found (using case–insensitive exact matching against Ruler or Nation Name), the following columns are displayed:
                          - Ruler Name  
                          - Resource 1+2  
                          - Alliance  
                          - Team  
                          - Days Old  
                          - Nation Drill Link
                        
                        - If no match is found, the input text is repeated in every column.
                        Blank lines are preserved as empty rows.
                        """
                    )
                    # Process the raw input lines preserving blank lines.
                    raw_lines = names_input.splitlines()
                    alt_rows = []
                    for line in raw_lines:
                        if line.strip() == "":
                            # Preserve blank row.
                            alt_rows.append({
                                "Ruler Name": "",
                                "Resource 1+2": "",
                                "Alliance": "",
                                "Team": "",
                                "Days Old": "",
                                "Nation Drill Link": ""
                            })
                            continue
                        lookup_name = line.strip()
                        temp_df = st.session_state.df.copy()
                        mask = temp_df["Ruler Name"].str.lower() == lookup_name.lower()
                        if not mask.any():
                            mask = temp_df["Nation Name"].str.lower() == lookup_name.lower()
                        if mask.any():
                            row = temp_df[mask].iloc[0]
                            ruler = row["Ruler Name"]
                            res = get_resource_1_2(row)
                            alliance = row["Alliance"]
                            team = row["Team"]
                            created_dt = pd.to_datetime(row["Created"], errors='coerce')
                            days_old = (pd.Timestamp.now() - created_dt).days if pd.notnull(created_dt) else ""
                            nation_drill = "https://www.cybernations.net/nation_drill_display.asp?Nation_ID=" + str(row["Nation ID"])
                            alt_rows.append({
                                "Ruler Name": ruler,
                                "Resource 1+2": res,
                                "Alliance": alliance,
                                "Team": team,
                                "Days Old": days_old,
                                "Nation Drill Link": nation_drill
                            })
                        else:
                            # For unrecognized names, repeat the input text in every column.
                            alt_rows.append({
                                "Ruler Name": lookup_name,
                                "Resource 1+2": lookup_name,
                                "Alliance": lookup_name,
                                "Team": lookup_name,
                                "Days Old": lookup_name,
                                "Nation Drill Link": lookup_name
                            })
                    alt_df = pd.DataFrame(alt_rows, columns=["Ruler Name", "Resource 1+2", "Alliance", "Team", "Days Old", "Nation Drill Link"])
                    
                    # Convert the alternative DataFrame to an HTML table.
                    alt_html_table = alt_df.to_html(index=False)
                    # Embed the table into HTML that includes a copy-to-clipboard button.
                    alt_html = f"""
                    <html>
                    <head>
                      <meta charset="utf-8">
                      <style>
                        table, th, td {{
                          border: 1px solid black;
                          border-collapse: collapse;
                          padding: 5px;
                        }}
                        button {{
                          margin-top: 10px;
                        }}
                      </style>
                    </head>
                    <body>
                      <div id="alt-table">
                        {alt_html_table}
                      </div>
                      <button onclick="copyAltTable()">Copy Table to Clipboard</button>
                      <script>
                      function copyAltTable(){{
                        var range = document.createRange();
                        var element = document.getElementById("alt-table");
                        range.selectNode(element);
                        window.getSelection().removeAllRanges();
                        window.getSelection().addRange(range);
                        try {{
                          document.execCommand('copy');
                          alert("Table copied to clipboard!");
                        }} catch(err) {{
                          alert("Unable to copy the table.");
                        }}
                        window.getSelection().removeAllRanges();
                      }}
                      </script>
                    </body>
                    </html>
                    """
                    # Render the HTML using components.html
                    components.html(alt_html, height=500)
    
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
                names_list = [name.strip() for name in re.split(r"[,\n]+", names_input) if name.strip()]
                output1 = "\n".join(names_list)
                output2 = "\n".join([f'"{name}",' for name in names_list])
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
            temp_df = st.session_state.df.copy()
            alliance_options = sorted(temp_df["Alliance"].dropna().unique().tolist())
            default_index = alliance_options.index("Freehold of The Wolves") if "Freehold of The Wolves" in alliance_options else 0
        else:
            alliance_options = ["Freehold of The Wolves"]
            default_index = 0

        alliance_selected = st.selectbox("Select Alliance", options=alliance_options, index=default_index, key="alliance_select")
        if st.button("Search", key="alliance_generate"):
            st.session_state.alliance_expanded = True
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
                    result_not_in_list = alliance_df[~mask].copy()
                    result_in_list = alliance_df[mask].copy()
                else:
                    result_not_in_list = pd.DataFrame()
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
            st.session_state.trade_circle_expanded = True
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
        # NEW SUBSECTION: Convert Trade Circle ID to Ruler Names
        # -----------------------
        st.markdown("#### Convert Trade Circle ID to Ruler Names")
        trade_circle_id_input = st.text_input("Enter a Trade Circle ID (e.g., 1001.1003.1007)", key="trade_circle_id_convert")
        if st.button("Convert", key="trade_convert"):
            if trade_circle_id_input:
                nation_id_list = [tid.strip() for tid in trade_circle_id_input.split('.') if tid.strip()]
                ruler_names = []
                not_found = []
                if "df" in st.session_state:
                    data_df = st.session_state.df.copy()
                    for nid in nation_id_list:
                        match = data_df[data_df["Nation ID"].astype(str) == nid]
                        if not match.empty:
                            ruler_names.append(match.iloc[0]["Ruler Name"])
                        else:
                            not_found.append(nid)
                    if ruler_names:
                        sorted_names = sorted(ruler_names, key=lambda x: x.lower())
                        st.markdown("**Ruler Names for the provided Trade Circle ID (alphabetical order):**")
                        st.text("\n".join(sorted_names))
                    if not_found:
                        st.warning(f"Nation IDs not found in data: {', '.join(not_found)}")
                else:
                    st.info("Nation Statistics data not loaded yet. Please download the data first.")
            else:
                st.info("Please enter a Trade Circle ID to convert.")
    
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
        if "df" in st.session_state:
            cc_df = st.session_state.df.copy()
            alliance_options = sorted(cc_df["Alliance"].dropna().unique().tolist())
            default_index = alliance_options.index("Freehold of The Wolves") if "Freehold of The Wolves" in alliance_options else 0
        else:
            alliance_options = ["Freehold of The Wolves"]
            default_index = 0

        alliance_selected_cc = st.selectbox("Select Alliance", options=alliance_options, index=default_index, key="alliance_select_cc")
        if st.button("Generate", key="cc_generate", on_click=keep_cc_open):
            st.session_state.cc_expanded = True
            if "df" in st.session_state:
                cc_df = st.session_state.df.copy()
                cc_df = cc_df[cc_df["Alliance"] == alliance_selected_cc]
                rulers_list = cc_df["Ruler Name"].dropna().tolist()
                rulers_list = [ruler.strip() for ruler in rulers_list if ruler.strip()]
                rulers_list = sorted(rulers_list, key=str.lower)
                groups = [rulers_list[i:i+26] for i in range(0, len(rulers_list), 26)]
                
                # Arrange boxes in 3 columns.
                columns = st.columns(3)
                for idx, group in enumerate(groups):
                    block_text = "\n".join(group)
                    unique_id = f"cc_textarea_{idx}"
                    html_block = f"""
                    <div style="margin-bottom: 20px;">
                      <textarea id="{unique_id}" style="width:100%; height:150px; background-color: black; color: white;" readonly="readonly">{block_text}</textarea>
                      <br>
                      <button onclick="navigator.clipboard.writeText(document.getElementById('{unique_id}').value)" style="margin-top:5px;">Copy</button>
                    </div>
                    """
                    col_index = idx % 3
                    with columns[col_index]:
                        components.html(html_block, height=200)
            else:
                st.info("Nation Statistics data not loaded yet. Please download the data first.")

if __name__ == "__main__":
    main()
