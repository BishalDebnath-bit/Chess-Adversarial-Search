
import math
import chess


PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


def evaluate_board(board):
    """Evaluate a position from White's perspective."""
    if board.is_checkmate():
        return -100000 if board.turn == chess.WHITE else 100000

    if board.is_game_over(claim_draw=True):
        return 0

    score = 0

    for piece_type, value in PIECE_VALUES.items():
        score += value * (
            len(board.pieces(piece_type, chess.WHITE))
            - len(board.pieces(piece_type, chess.BLACK))
        )

    return score


def build_search_tree(board, depth=2, algorithm="alphabeta"):
    """
    Build an instrumented Minimax or Alpha-Beta search tree.
    Scores are from White's perspective.
    """

    tree = {
        "nodes": [],
        "edges": [],
        "visited": 0,
        "pruned": 0,
        "root_score": None,
    }

    next_id = 0

    def add_node(label, level, kind="position", score=None):
        nonlocal next_id

        node_id = next_id
        next_id += 1

        tree["nodes"].append({
            "id": node_id,
            "label": label,
            "level": level,
            "kind": kind,
            "score": score,
            "children": [],
        })

        return node_id

    def add_edge(parent, child, move_label=""):
        tree["edges"].append({
            "source": parent,
            "target": child,
            "move": move_label,
        })

        parent_node = next(
            node for node in tree["nodes"]
            if node["id"] == parent
        )
        parent_node["children"].append(child)

    def search(position, remaining, alpha, beta, parent, move_text):
        tree["visited"] += 1

        maximizing = position.turn == chess.WHITE
        node_id = add_node(
            move_text or "Starting position",
            depth - remaining,
        )

        if parent is not None:
            add_edge(parent, node_id, move_text)

        if remaining == 0 or position.is_game_over(claim_draw=True):
            score = evaluate_board(position)
            tree["nodes"][node_id]["score"] = score
            tree["nodes"][node_id]["label"] += f"\\nEval: {score}"
            return score, node_id

        best_score = -math.inf if maximizing else math.inf
        legal_moves = list(position.legal_moves)

        for index, move in enumerate(legal_moves):
            san = position.san(move)
            position.push(move)

            score, _ = search(
                position,
                remaining - 1,
                alpha,
                beta,
                node_id,
                san,
            )

            position.pop()

            if maximizing:
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
            else:
                best_score = min(best_score, score)
                beta = min(beta, best_score)

            if algorithm == "alphabeta" and alpha >= beta:
                remaining_moves = len(legal_moves) - index - 1

                if remaining_moves > 0:
                    tree["pruned"] += remaining_moves

                    marker = add_node(
                        f"PRUNED {remaining_moves} moves skipped",
                        depth - remaining,
                        kind="pruned",
                    )
                    add_edge(node_id, marker, "cutoff")

                break

        tree["nodes"][node_id]["score"] = best_score
        tree["nodes"][node_id]["label"] += (
            f"\\nBest eval: {best_score}"
        )

        return best_score, node_id

    root_score, root_id = search(
        board.copy(),
        depth,
        -math.inf,
        math.inf,
        None,
        "Root",
    )

    tree["root_score"] = root_score
    tree["root_id"] = root_id

    return tree
