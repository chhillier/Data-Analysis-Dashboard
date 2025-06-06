# test_bug.py
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("Streamlit State Reload Test")
st.info("The goal is to see if clicking a button/checkbox below causes the whole page to do a hard reload (i.e., this info message disappears and reappears).")

# --- Test 1: The Button + Session State Pattern ---
st.header("Test 1: Button with Session State")

# Initialize state for this button
if 'show_summary_button' not in st.session_state:
    st.session_state.show_summary_button = False

# The button toggles the state
if st.button("Toggle Summary via Button"):
    st.session_state.show_summary_button = not st.session_state.get('show_summary_button', False)
    st.write("DEBUG: Button was clicked.")

# Conditionally display content based on the state
if st.session_state.show_summary_button:
    st.success("Button test content is now visible.")
    st.write("This content should appear/disappear without the whole page reloading.")


st.markdown("---")


# --- Test 2: The Direct Checkbox Pattern ---
st.header("Test 2: Checkbox")

# The checkbox's own state controls the content
if st.checkbox("Show Summary via Checkbox"):
    st.success("Checkbox test content is now visible.")
    st.write("This content should appear/disappear without the whole page reloading.")