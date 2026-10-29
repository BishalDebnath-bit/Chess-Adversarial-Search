
import streamlit as st
from stchess import board

st.set_page_config(page_title="Drag Chess Test", layout="wide")

st.title("♟️ Drag-and-Drop Chessboard")
st.write("Try dragging a chess piece to another square.")

color = st.selectbox(
    "Board orientation",
    ["white", "black"]
)

result = board(color)

st.subheader("Component response")
st.write(result)
