

import plotly.graph_objects as go
from search_tree import build_search_tree
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
import chess
from algorithms import find_best_move

st.set_page_config(
    page_title="Chess AI Lab",
    page_icon="♟️",
    layout="wide",
)

st.title("♟️ Chess AI Lab")
st.caption("Adversarial Search | Minimax vs Alpha-Beta Pruning")

# ---------- Session state ----------
if "board" not in st.session_state:
    st.session_state.board = chess.Board()

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "move_history_san" not in st.session_state:
    st.session_state.move_history_san = []

if "position_key" not in st.session_state:
    st.session_state.position_key = st.session_state.board.fen()

if "game_metrics" not in st.session_state:
    st.session_state.game_metrics = []

board = st.session_state.board

# ---------- Sidebar ----------
with st.sidebar:
    st.header("AI Settings")

    algorithm = st.selectbox(
        "Algorithm",
        ["alphabeta", "minimax"],
        format_func=lambda x: {
            "alphabeta": "Alpha-Beta Pruning",
            "minimax": "Minimax",
        }[x],
    )

    depth = st.slider("Search depth", 1, 3, 2)

    human_color = st.selectbox(
        "Play as",
        ["White", "Black"],
        key="human_color",
    )

    if st.button("New Game", use_container_width=True):
        st.session_state.board = chess.Board()
        st.session_state.last_result = None
        st.session_state.move_history_san = []
        st.session_state.game_metrics = []
        st.session_state.position_key = st.session_state.board.fen()
        st.rerun()

human_side = chess.WHITE if human_color == "White" else chess.BLACK
game_over = board.is_game_over(claim_draw=True)

# ---------- Draggable chessboard component ----------
chessboard_component = st.components.v2.component(
    name="chess_ai_drag_board",
    html='<div id="chess-board" aria-label="Interactive chessboard"></div>',
    css="""
    #chess-board {
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        width: min(100%, 560px);
        margin: auto;
        aspect-ratio: 1;
        border: 2px solid #49382b;
        user-select: none;
    }

    .square {
        display: flex;
        align-items: center;
        justify-content: center;
        aspect-ratio: 1;
        font-size: clamp(24px, 5vw, 54px);
        cursor: grab;
        line-height: 1;
        position: relative;
    }

    .light { background: #f0d9b5; }
    .dark { background: #b58863; }

    .square:focus {
        outline: 3px solid #16803c;
        outline-offset: -3px;
    }

    .piece {
        pointer-events: none;
        font-family: "DejaVu Sans", "Segoe UI Symbol", sans-serif;
    }

    .white-piece {
        color: #ffffff;
        text-shadow: 0 1px 2px #60452e, 0 0 2px #60452e;
    }

    .black-piece {
        color: #202020;
        text-shadow: 0 1px 1px #f0d9b5;
    }

    .selected-square {
        box-shadow: inset 0 0 0 4px #36a853;
    }

    .square.last-move {
        background-image: linear-gradient(
            rgba(54, 168, 83, 0.28),
            rgba(54, 168, 83, 0.28)
        );
    }
    """,
    js="""
    export default function(component) {
        const { parentElement, data, setTriggerValue } = component;
        const root = parentElement.querySelector("#chess-board");
        if (!root) return;

        const glyph = {
            K: "♔", Q: "♕", R: "♖",
            B: "♗", N: "♘", P: "♙",
            k: "♚", q: "♛", r: "♜",
            b: "♝", n: "♞", p: "♟"
        };

        const fen = data.fen || "";
        const orientation = data.orientation || "white";
        const position = fen.split(" ")[0].split("/");
        const squares = [];

        position.forEach(row => {
            const rank = [];
            for (const ch of row) {
                if (/^[1-8]$/.test(ch)) {
                    for (let i = 0; i < Number(ch); i++) {
                        rank.push("");
                    }
                } else {
                    rank.push(ch);
                }
            }
            squares.push(rank);
        });

        root.replaceChildren();

        const files = orientation === "white"
            ? [0,1,2,3,4,5,6,7]
            : [7,6,5,4,3,2,1,0];

        const ranks = orientation === "white"
            ? [0,1,2,3,4,5,6,7]
            : [7,6,5,4,3,2,1,0];

        function sendMove(from, to) {
            if (from && to && from !== to) {
                setTriggerValue("move", {
                    from: from,
                    to: to,
                    fen: fen
                });
            }
        }

        squares.forEach((row, rowIndex) => {
            files.forEach(fileIndex => {
                const rankIndex = ranks[rowIndex];
                const piece = row[fileIndex];

                const squareName =
                    String.fromCharCode(97 + fileIndex) +
                    String(8 - rankIndex);

                const cell = document.createElement("div");

                cell.className = "square " +
                    ((rankIndex + fileIndex) % 2 === 0
                        ? "light" : "dark");

                cell.dataset.square = squareName;
                cell.setAttribute("role", "button");
                cell.setAttribute("tabindex", "0");
                cell.setAttribute("aria-label", squareName);

                if (piece) {
                    const span = document.createElement("span");
                    span.className = "piece " +
                        (piece === piece.toUpperCase()
                            ? "white-piece" : "black-piece");

                    span.textContent = glyph[piece];
                    cell.appendChild(span);
                    cell.draggable = true;

                    cell.addEventListener("dragstart", event => {
                        event.dataTransfer.setData(
                            "text/plain", squareName
                        );
                        event.dataTransfer.effectAllowed = "move";
                    });
                }

                cell.addEventListener("dragover", event => {
                    event.preventDefault();
                    event.dataTransfer.dropEffect = "move";
                });

                cell.addEventListener("drop", event => {
                    event.preventDefault();
                    const from = event.dataTransfer.getData("text/plain");
                    sendMove(from, squareName);
                });

                cell.addEventListener("click", () => {
                    const previous = root.dataset.selected || "";

                    if (!previous) {
                        if (piece) {
                            root.dataset.selected = squareName;
                            cell.classList.add("selected-square");
                        }
                        return;
                    }

                    const previousCell = root.querySelector(
                        '[data-square="' + previous + '"]'
                    );

                    if (previousCell) {
                        previousCell.classList.remove("selected-square");
                    }

                    root.dataset.selected = "";

                    if (previous === squareName) return;

                    const previousPiece =
                        squares[8 - Number(previous[1])]
                            [previous.charCodeAt(0) - 97];

                    if (
                        piece &&
                        previousPiece &&
                        ((piece === piece.toUpperCase()) ===
                         (previousPiece === previousPiece.toUpperCase()))
                    ) {
                        root.dataset.selected = squareName;
                        cell.classList.add("selected-square");
                        return;
                    }

                    sendMove(previous, squareName);
                });

                cell.addEventListener("keydown", event => {
                    if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        cell.click();
                    }
                });

                root.appendChild(cell);
            });
        });

        return () => {};
    }
    """,
)

left, right = st.columns([1.15, 1])

# ---------- Board and move processing ----------
with left:
    st.subheader("Drag and drop your pieces")

    component_result = chessboard_component(
        data={
            "fen": board.fen(),
            "orientation": (
                "white" if human_side == chess.WHITE else "black"
            ),
        },
        on_move_change=lambda: None,
        key="chess_drag_component",
        width="stretch",
        height=570,
    )

    move_data = component_result.move

    if move_data and not game_over:
        try:
            # Reject stale browser events from an old position.
            submitted_fen = move_data.get("fen")

            if submitted_fen != board.fen():
                st.rerun()

            elif board.turn != human_side:
                st.warning("It is the AI's turn.")

            else:
                from_square = move_data["from"]
                to_square = move_data["to"]

                move = chess.Move.from_uci(from_square + to_square)

                piece = board.piece_at(move.from_square)

                # Automatically promote to a queen.
                if (
                    piece
                    and piece.piece_type == chess.PAWN
                    and chess.square_rank(move.to_square) in (0, 7)
                ):
                    move.promotion = chess.QUEEN

                # Human moves must be legal in the current position.
                if move not in board.legal_moves:
                    st.warning("Illegal move rejected.")
                else:
                    human_san = board.san(move)
                    board.push(move)

                    st.session_state.move_history_san.append(human_san)
                    st.session_state.last_result = None

                    # Verify position integrity.
                    if not board.is_valid():
                        st.error("Invalid position detected.")
                        st.stop()

                    # AI searches the exact current position.
                    if not board.is_game_over(claim_draw=True):
                        search_board = board.copy(stack=False)

                        result = find_best_move(
                            search_board,
                            depth=depth,
                            algorithm=algorithm,
                        )

                        ai_move = result.get("move")

                        # Never push an illegal AI move.
                        if (
                            ai_move is not None
                            and ai_move in board.legal_moves
                        ):
                            result["move_san"] = board.san(ai_move)
                            board.push(ai_move)
                            st.session_state.move_history_san.append(
                                result["move_san"]
                            )
                            st.session_state.last_result = result

                            # Record the real search result for this AI move.
                            st.session_state.game_metrics.append({
                                "AI Move #": len(st.session_state.game_metrics) + 1,
                                "Algorithm": result["algorithm"],
                                "Depth": depth,
                                "AI Move": result["move_san"],
                                "Nodes Explored": result["nodes"],
                                "Search Time (s)": result["time"],
                                "Evaluation": result["score"],
                            })

                            if not board.is_valid():
                                st.error("Invalid position after AI move.")
                                st.stop()
                        elif not board.is_game_over(claim_draw=True):
                            st.error(
                                "AI did not return a legal move. "
                                "The AI move was not applied."
                            )

                    st.session_state.position_key = board.fen()
                    st.rerun()

        except (ValueError, KeyError, TypeError):
            st.warning("Invalid move data received; move rejected.")

# ---------- Status and performance ----------
with right:
    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        st.success(f"Checkmate! {winner} wins.")
    elif board.is_stalemate():
        st.info("Draw by stalemate.")
    elif board.is_game_over(claim_draw=True):
        st.info(f"Game over: {board.result(claim_draw=True)}")
    else:
        st.write(
            "Your turn"
            if board.turn == human_side
            else "AI to move"
        )

        if board.is_check():
            st.warning("Check!")

    st.subheader("AI Performance")
    result = st.session_state.last_result

    if result:
        st.metric(
            "AI move",
            result.get("move_san", result["move"].uci()),
        )
        st.metric("Nodes explored", result["nodes"])
        st.metric("Search time", f'{result["time"]:.5f} s')
        st.metric("Evaluation", result["score"])
        st.caption(f'Algorithm: {result["algorithm"]}')
    else:
        st.info("AI statistics will appear after its move.")

    st.subheader("Move History")

    history = []
    san_moves = st.session_state.move_history_san

    for i in range(0, len(san_moves), 2):
        move_number = i // 2 + 1
        entry = f"{move_number}. {san_moves[i]}"

        if i + 1 < len(san_moves):
            entry += f" {san_moves[i + 1]}"

        history.append(entry)

    st.write(" ".join(history) if history else "No moves yet.")
    
# ---------- Live Algorithm Comparison ----------
st.divider()
st.header("🔬 Algorithm Performance Laboratory")

st.write(
    "Compare Minimax and Alpha-Beta Pruning on the "
    "same current chess position."
)

if st.button("Compare Both Algorithms", type="primary"):
    comparison_rows = []

    for algo in ["minimax", "alphabeta"]:
        result = find_best_move(
            board.copy(),
            depth=depth,
            algorithm=algo,
        )

        comparison_rows.append({
            "Algorithm": (
                "Minimax" if algo == "minimax"
                else "Alpha-Beta Pruning"
            ),
            "Nodes Explored": result["nodes"],
            "Execution Time (s)": result["time"],
            "Evaluation": result["score"],
            "Best Move": (
                board.san(result["move"])
                if result["move"] is not None
                else "No legal move"
            ),
        })

    comparison_df = pd.DataFrame(comparison_rows)
    st.session_state.comparison_df = comparison_df

if "comparison_df" in st.session_state:
    comparison_df = st.session_state.comparison_df

    c1, c2 = st.columns(2)

    for _, row in comparison_df.iterrows():
        if row["Algorithm"] == "Minimax":
            with c1:
                st.metric(
                    "Minimax nodes",
                    f'{row["Nodes Explored"]:,}',
                )
                st.metric(
                    "Minimax time",
                    f'{row["Execution Time (s)"]:.5f} s',
                )
        else:
            with c2:
                st.metric(
                    "Alpha-Beta nodes",
                    f'{row["Nodes Explored"]:,}',
                )
                st.metric(
                    "Alpha-Beta time",
                    f'{row["Execution Time (s)"]:.5f} s',
                )

    st.subheader("Search Work Comparison")

    fig = px.bar(
        comparison_df,
        x="Algorithm",
        y="Nodes Explored",
        color="Algorithm",
        title="Nodes Explored on the Same Position",
        text="Nodes Explored",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Execution Time Comparison")

    fig_time = px.bar(
        comparison_df,
        x="Algorithm",
        y="Execution Time (s)",
        color="Algorithm",
        title="Time Required to Find a Move",
        text="Execution Time (s)",
    )
    st.plotly_chart(fig_time, use_container_width=True)

    minimax_row = comparison_df[
        comparison_df["Algorithm"] == "Minimax"
    ].iloc[0]

    alpha_row = comparison_df[
        comparison_df["Algorithm"] == "Alpha-Beta Pruning"
    ].iloc[0]

    if minimax_row["Nodes Explored"] > 0:
        reduction = (
            1 - alpha_row["Nodes Explored"]
            / minimax_row["Nodes Explored"]
        ) * 100

        st.metric(
            "Node reduction with Alpha-Beta",
            f"{reduction:.2f}%",
        )

    st.dataframe(comparison_df, hide_index=True,
                 use_container_width=True)


# ---------- Historical Benchmark Dashboard ----------
st.divider()
st.header("📊 Historical Benchmark Results")

csv_path = Path("benchmark_results.csv")

if csv_path.exists():
    history_df = pd.read_csv(csv_path)

    required = {
        "Position", "Depth", "Algorithm",
        "Median Nodes", "Median Time (s)"
    }

    if required.issubset(history_df.columns):
        selected_positions = st.multiselect(
            "Filter chess positions",
            history_df["Position"].unique().tolist(),
            default=history_df["Position"].unique().tolist(),
            key="history_positions",
        )

        filtered_df = history_df[
            history_df["Position"].isin(selected_positions)
        ]

        if not filtered_df.empty:
            fig_nodes = px.bar(
                filtered_df,
                x="Depth",
                y="Median Nodes",
                color="Algorithm",
                barmode="group",
                facet_col="Position",
                title="Historical Search Nodes by Depth",
            )
            st.plotly_chart(fig_nodes, use_container_width=True)

            fig_time = px.line(
                filtered_df,
                x="Depth",
                y="Median Time (s)",
                color="Algorithm",
                markers=True,
                facet_col="Position",
                title="Historical Execution Time by Depth",
            )
            st.plotly_chart(fig_time, use_container_width=True)

            st.download_button(
                "Download benchmark data",
                data=filtered_df.to_csv(index=False),
                file_name="chess_ai_benchmarks.csv",
                mime="text/csv",
            )
        else:
            st.info("Select at least one position.")
    else:
        st.warning(
            "The CSV columns do not match. Run benchmark.py "
            "to regenerate the results."
        )
else:
    st.info(
        "Run python benchmark.py to populate historical "
        "benchmark graphs."
    )

    
# ---------- Search Tree Visualizer ----------
st.divider()
st.header("🌳 Search Tree Visualizer")

st.write(
    "Explore the nodes visited by Minimax or Alpha-Beta Pruning "
    "for the current chess position."
)

tree_algorithm = st.selectbox(
    "Tree algorithm",
    ["minimax", "alphabeta"],
    format_func=lambda x: {
        "minimax": "Minimax — Full Search",
        "alphabeta": "Alpha-Beta — Pruned Search",
    }[x],
    key="tree_algorithm",
)

tree_depth = st.select_slider(
    "Visualization depth",
    options=[1, 2, 3],
    value=2,
    key="tree_depth",
)

if st.button("Generate Search Tree", type="primary"):
    with st.spinner("Building the search tree..."):
        tree = build_search_tree(
            board.copy(),
            depth=tree_depth,
            algorithm=tree_algorithm,
        )

        st.session_state.search_tree = tree
        st.session_state.search_tree_algorithm = tree_algorithm
        st.session_state.search_tree_depth = tree_depth

if "search_tree" in st.session_state:
    tree = st.session_state.search_tree

    a, b, c = st.columns(3)

    a.metric("Visited Nodes", tree["visited"])
    b.metric("Pruned Moves", tree["pruned"])
    c.metric("Root Evaluation", tree["root_score"])

    # Compute a simple hierarchical layout.
    
    # ---------- Readable Search Tree Visualization ----------
    nodes = {node["id"]: node for node in tree["nodes"]}

    # Limit the displayed graph to the first few branches.
    # The full search and metrics above remain unchanged.
    max_display_nodes = 100
    visible_ids = {tree["root_id"]}
    visible_edges = []

    for edge in tree["edges"]:
        if (
            edge["source"] in visible_ids
            and len(visible_ids) < max_display_nodes
        ):
            visible_ids.add(edge["target"])
            visible_edges.append(edge)

    visible_nodes = [nodes[nid] for nid in visible_ids]

    # Arrange nodes by level, spreading each level horizontally.
    levels = {}
    for node in visible_nodes:
        levels.setdefault(node["level"], []).append(node)

    positions = {}
    for level, level_nodes in levels.items():
        level_nodes.sort(key=lambda n: n["id"])
        count = len(level_nodes)

        for index, node in enumerate(level_nodes):
            positions[node["id"]] = (
                index - (count - 1) / 2,
                -level,
            )

    # Build edges.
    edge_x, edge_y = [], []

    for edge in visible_edges:
        source = edge["source"]
        target = edge["target"]

        if source not in positions or target not in positions:
            continue

        x0, y0 = positions[source]
        x1, y1 = positions[target]

        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(color="#64748b", width=1),
        hoverinfo="skip",
        showlegend=False,
    ))

    node_x, node_y, colors, hover = [], [], [], []

    for node in visible_nodes:
        x, y = positions[node["id"]]
        node_x.append(x)
        node_y.append(y)

        if node["kind"] == "pruned":
            colors.append("#ef4444")
        elif node["id"] == tree["root_id"]:
            colors.append("#3b82f6")
        elif node["score"] is not None:
            colors.append("#22c55e")
        else:
            colors.append("#64748b")

        hover.append(
            f"Node ID: {node['id']}<br>"
            f"Move/position: {node['label']}<br>"
            f"Level: {node['level']}<br>"
            f"Evaluation: {node['score']}<br>"
            f"Type: {node['kind']}"
        )

    fig.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        marker=dict(
            size=11,
            color=colors,
            line=dict(width=1, color="#e2e8f0"),
        ),
        hovertext=hover,
        hoverinfo="text",
        showlegend=False,
    ))

    fig.update_layout(
        title=(
            f"{st.session_state.search_tree_algorithm.title()} "
            f"Search Tree — Depth "
            f"{st.session_state.search_tree_depth}"
        ),
        xaxis=dict(visible=False),
        yaxis=dict(
            title="Search Level",
            tickmode="linear",
            dtick=1,
        ),
        height=600,
        margin=dict(l=30, r=30, t=60, b=30),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        f"Showing {len(visible_nodes)} of {len(tree['nodes'])} "
        "recorded nodes. Hover over a node for its move and score. "
        "Blue = root, green = evaluated node, red = pruned marker, "
        "gray = intermediate search node."
    )

# ---------- Live Game Analytics ----------
st.divider()
st.header("📈 Live Game Analytics")
st.caption(
    "These charts use actual search measurements recorded when the AI "
    "made each move in this game. They do not update from human moves alone."
)

metrics = st.session_state.game_metrics

if metrics:
    live_df = pd.DataFrame(metrics)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AI Moves Recorded", len(live_df))
    c2.metric("Total Nodes Explored", f'{live_df["Nodes Explored"].sum():,}')
    c3.metric("Total Search Time", f'{live_df["Search Time (s)"].sum():.4f} s')
    c4.metric("Average Search Time", f'{live_df["Search Time (s)"].mean():.4f} s')

    st.subheader("Nodes Explored per AI Move")
    fig_live_nodes = px.bar(
        live_df,
        x="AI Move #",
        y="Nodes Explored",
        color="Algorithm",
        hover_data=["AI Move", "Depth", "Evaluation"],
        title="Search Work During This Game",
    )
    st.plotly_chart(fig_live_nodes, use_container_width=True)

    st.subheader("Search Time per AI Move")
    fig_live_time = px.line(
        live_df,
        x="AI Move #",
        y="Search Time (s)",
        color="Algorithm",
        markers=True,
        hover_data=["AI Move", "Depth", "Nodes Explored"],
        title="AI Decision Latency",
    )
    st.plotly_chart(fig_live_time, use_container_width=True)

    st.subheader("Evaluation Across AI Moves")
    fig_live_eval = px.line(
        live_df,
        x="AI Move #",
        y="Evaluation",
        markers=True,
        hover_data=["AI Move", "Algorithm", "Depth"],
        title="Material Evaluation (White's perspective)",
    )
    st.plotly_chart(fig_live_eval, use_container_width=True)

    with st.expander("View recorded live measurements"):
        st.dataframe(live_df, use_container_width=True, hide_index=True)

    st.download_button(
        "Download this game's analytics",
        data=live_df.to_csv(index=False),
        file_name="live_game_analytics.csv",
        mime="text/csv",
    )
else:
    st.info(
        "No AI move has been recorded yet. Make a legal move and let the AI "
        "respond; its search measurements will appear here."
    )

