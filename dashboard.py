
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Chess AI Benchmark Lab",
    page_icon="♟️",
    layout="wide",
)

st.title("♟️ Chess AI — Benchmark Laboratory")
st.caption("Performance analysis of Minimax vs Alpha-Beta Pruning")

file_path = Path("benchmark_results.csv")

if not file_path.exists():
    st.error("benchmark_results.csv not found. Run python benchmark.py first.")
    st.stop()

df = pd.read_csv(file_path)

required_columns = {
    "Position",
    "Depth",
    "Algorithm",
    "Median Time (s)",
    "Median Nodes",
    "Score",
    "Best Move",
}

if not required_columns.issubset(df.columns):
    st.error("Your CSV is missing required columns. Run the latest benchmark.py.")
    st.stop()

# ---------- Filters ----------
st.sidebar.header("Experiment Filters")

positions = st.sidebar.multiselect(
    "Chess positions",
    options=df["Position"].unique().tolist(),
    default=df["Position"].unique().tolist(),
)

depths = st.sidebar.multiselect(
    "Search depths",
    options=sorted(df["Depth"].unique().tolist()),
    default=sorted(df["Depth"].unique().tolist()),
)

filtered = df[
    df["Position"].isin(positions)
    & df["Depth"].isin(depths)
].copy()

if filtered.empty:
    st.warning("Select at least one position and one depth.")
    st.stop()

# ---------- Summary metrics ----------
minimax = filtered[filtered["Algorithm"] == "minimax"]
alphabeta = filtered[filtered["Algorithm"] == "alphabeta"]

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Experiments",
    len(filtered),
)

c2.metric(
    "Minimax median nodes",
    f"{minimax['Median Nodes'].median():,.0f}"
    if not minimax.empty else "N/A",
)

c3.metric(
    "Alpha-Beta median nodes",
    f"{alphabeta['Median Nodes'].median():,.0f}"
    if not alphabeta.empty else "N/A",
)

if not minimax.empty and not alphabeta.empty:
    c4.metric(
        "Alpha-Beta median time",
        f"{alphabeta['Median Time (s)'].median():.4f} s",
    )
else:
    c4.metric("Alpha-Beta median time", "N/A")

# ---------- Charts ----------
st.subheader("1. Search Nodes by Depth")

fig_nodes = px.bar(
    filtered,
    x="Depth",
    y="Median Nodes",
    color="Algorithm",
    barmode="group",
    facet_col="Position",
    title="Computational Work at Each Search Depth",
    labels={
        "Depth": "Search Depth",
        "Median Nodes": "Median Nodes Explored",
    },
)

st.plotly_chart(fig_nodes, use_container_width=True)

st.subheader("2. Execution Time by Depth")

fig_time = px.line(
    filtered,
    x="Depth",
    y="Median Time (s)",
    color="Algorithm",
    markers=True,
    facet_col="Position",
    title="Search Execution Time",
    labels={
        "Depth": "Search Depth",
        "Median Time (s)": "Median Time (seconds)",
    },
)

st.plotly_chart(fig_time, use_container_width=True)

# ---------- Engineering metrics ----------
st.subheader("3. Alpha-Beta Efficiency")

if {
    "Node Reduction (%)",
    "Speedup (x)",
    "Score Agreement",
}.issubset(df.columns):
    efficiency = filtered[filtered["Algorithm"] == "alphabeta"]

    st.dataframe(
        efficiency[
            [
                "Position",
                "Depth",
                "Node Reduction (%)",
                "Speedup (x)",
                "Score Agreement",
                "Best Move",
                "Score",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info(
        "Run the enhanced benchmark.py to generate pruning "
        "percentage, speedup and score-agreement metrics."
    )

# ---------- Raw data ----------
with st.expander("View all benchmark records"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)

st.download_button(
    "Download filtered results as CSV",
    data=filtered.to_csv(index=False),
    file_name="chess_ai_benchmark.csv",
    mime="text/csv",
)

st.caption(
    "Interpretation: lower node counts and execution times generally "
    "indicate less computational work. Compare algorithms at the same "
    "position and search depth."
)
