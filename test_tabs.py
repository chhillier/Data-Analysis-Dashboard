# test_tabs.py
import streamlit as st

st.title("Minimal Tab Test")

tab1, tab2 = st.tabs(["Tab A", "Tab B"])

with tab1:
    st.header("This is Tab A (Default)")
    st.write("Content for Tab A.")
    if st.button("Button in Tab A", key="btn_A"):
        st.write("Tab A button clicked!")

with tab2:
    st.header("This is Tab B")
    st.write("Content for Tab B.")
    if st.button("Test Button in Tab B", key="btn_B"):
        st.write("Tab B button clicked!")
        st.success("Tab B button action complete.")