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
            
            # Display each block in its own text box with a copy button.
            for idx, group in enumerate(groups):
                block_text = "\n".join(group)
                unique_id = f"cc_textarea_{idx}"
                html_block = f"""
                <div style="margin-bottom: 20px;">
                  <textarea id="{unique_id}" style="width:100%; height:150px; background-color: #d3d3d3;" readonly>{block_text}</textarea>
                  <br>
                  <button onclick="navigator.clipboard.writeText(document.getElementById('{unique_id}').value)" style="margin-top:5px;">Copy</button>
                </div>
                """
                components.html(html_block, height=200)
        else:
            st.info("Nation Statistics data not loaded yet. Please download the data first.")
