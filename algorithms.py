
import chess
import math
import time

# Standard approximate chess piece values
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

# Counts the positions evaluated during each search
nodes_explored = 0


def evaluate_board(board):
    """
    Positive score = advantage for White
    Negative score = advantage for Black
    """

    if board.is_checkmate():
        return -100000 if board.turn == chess.WHITE else 100000

    if board.is_game_over(claim_draw=True):
        return 0

    score = 0

    for piece_type, value in PIECE_VALUES.items():
        white_pieces = len(
            board.pieces(piece_type, chess.WHITE)
        )
        black_pieces = len(
            board.pieces(piece_type, chess.BLACK)
        )

        score += value * (white_pieces - black_pieces)

    return score


def minimax(board, depth, maximizing_player):
    global nodes_explored
    nodes_explored += 1

    if depth == 0 or board.is_game_over(claim_draw=True):
        return evaluate_board(board)

    if maximizing_player:
        best_score = -math.inf

        for move in board.legal_moves:
            board.push(move)

            score = minimax(
                board, depth - 1, False
            )

            board.pop()
            best_score = max(best_score, score)

        return best_score

    else:
        best_score = math.inf

        for move in board.legal_moves:
            board.push(move)

            score = minimax(
                board, depth - 1, True
            )

            board.pop()
            best_score = min(best_score, score)

        return best_score


def alpha_beta(board, depth, alpha, beta, maximizing_player):
    global nodes_explored
    nodes_explored += 1

    if depth == 0 or board.is_game_over(claim_draw=True):
        return evaluate_board(board)

    if maximizing_player:
        best_score = -math.inf

        for move in board.legal_moves:
            board.push(move)

            score = alpha_beta(
                board, depth - 1,
                alpha, beta, False
            )

            board.pop()

            best_score = max(best_score, score)
            alpha = max(alpha, best_score)

            if beta <= alpha:
                break

        return best_score

    else:
        best_score = math.inf

        for move in board.legal_moves:
            board.push(move)

            score = alpha_beta(
                board, depth - 1,
                alpha, beta, True
            )

            board.pop()

            best_score = min(best_score, score)
            beta = min(beta, best_score)

            if beta <= alpha:
                break

        return best_score



def find_best_move(board, depth=2, algorithm="alphabeta"):
    global nodes_explored
    nodes_explored = 0

    start_time = time.perf_counter()

    best_move = None
    maximizing = board.turn == chess.WHITE
    best_score = -math.inf if maximizing else math.inf

    # Keep the bounds across root moves.
    alpha = -math.inf
    beta = math.inf

    for move in list(board.legal_moves):
        board.push(move)

        if algorithm == "minimax":
            score = minimax(
                board, depth - 1, not maximizing
            )

        elif algorithm == "alphabeta":
            score = alpha_beta(
                board, depth - 1,
                alpha, beta,
                not maximizing
            )

        else:
            board.pop()
            raise ValueError("Unknown algorithm")

        board.pop()

        if (
            best_move is None
            or (maximizing and score > best_score)
            or (not maximizing and score < best_score)
        ):
            best_score = score
            best_move = move

        # Update bounds for subsequent root moves.
        if algorithm == "alphabeta":
            if maximizing:
                alpha = max(alpha, best_score)
            else:
                beta = min(beta, best_score)

    elapsed = time.perf_counter() - start_time

    return {
        "move": best_move,
        "score": best_score if best_move else evaluate_board(board),
        "nodes": nodes_explored,
        "time": elapsed,
        "algorithm": algorithm
    }
