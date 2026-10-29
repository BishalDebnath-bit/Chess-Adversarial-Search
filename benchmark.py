
import time
import statistics
import chess
import pandas as pd

from algorithms import find_best_move


# Fixed positions so both algorithms get the same test cases.
TEST_POSITIONS = {
    "Starting Position": chess.Board(),

    "Opening Position": chess.Board(
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    ),

    "Middlegame Position": chess.Board(
        "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8"
    ),
}


def run_benchmark(depths=(1, 2, 3), repetitions=3):
    results = []

    for position_name, original_board in TEST_POSITIONS.items():
        for depth in depths:
            for algorithm in ("minimax", "alphabeta"):
                times = []
                node_counts = []
                scores = []
                moves = []

                for _ in range(repetitions):
                    board = original_board.copy()

                    start = time.perf_counter()

                    result = find_best_move(
                        board,
                        depth=depth,
                        algorithm=algorithm,
                    )

                    elapsed = time.perf_counter() - start

                    times.append(elapsed)
                    node_counts.append(result["nodes"])
                    scores.append(result["score"])
                    moves.append(
                        result["move"].uci()
                        if result["move"] is not None
                        else None
                    )

                results.append({
                    "Position": position_name,
                    "Depth": depth,
                    "Algorithm": algorithm,
                    "Median Time (s)": statistics.median(times),
                    "Median Nodes": statistics.median(node_counts),
                    "Nodes/Second": (
                        statistics.median(node_counts)
                        / statistics.median(times)
                        if statistics.median(times) > 0
                        else 0
                    ),
                    "Score": scores[-1],
                    "Best Move": moves[-1],
                    "Move Consistent": len(set(moves)) == 1,
                })

    return pd.DataFrame(results)


if __name__ == "__main__":
    print("Running chess AI benchmark...")
    print("Please wait; deeper searches take longer.\n")

    results_df = run_benchmark()

    results_df.to_csv("benchmark_results.csv", index=False)

    print(results_df.to_string(index=False))
    print("\nResults saved to benchmark_results.csv")
