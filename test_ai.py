
import chess
from algorithms import find_best_move

# Test the same chess position at the same depth.
board = chess.Board()

print("CHESS ADVERSARIAL SEARCH: COMPARISON")
print("Position: Standard starting position")
print("Search depth: 2")
print()

results = {}

for algorithm in ["minimax", "alphabeta"]:
    result = find_best_move(
        board.copy(),
        depth=2,
        algorithm=algorithm
    )

    results[algorithm] = result

    print(f"Algorithm: {algorithm}")
    print(f"Best move: {result['move']}")
    print(f"Evaluation: {result['score']}")
    print(f"Nodes explored: {result['nodes']}")
    print(f"Execution time: {result['time']:.6f} seconds")
    print()

m = results["minimax"]
a = results["alphabeta"]

print("COMPARISON")
print("Same evaluation:", m["score"] == a["score"])
print("Same move:", m["move"] == a["move"])

if m["nodes"] > 0:
    reduction = (
        (m["nodes"] - a["nodes"]) / m["nodes"]
    ) * 100
    print(f"Node reduction: {reduction:.2f}%")
else:
    print("Node reduction: not available")
