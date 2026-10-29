
import pandas as pd
import matplotlib.pyplot as plt

# Load actual benchmark results
df = pd.read_csv("benchmark_results.csv")

# Create one comparison for each chess position.
for position in df["Position"].unique():
    subset = df[df["Position"] == position]

    # Graph 1: Nodes explored
    nodes = subset.pivot(
        index="Depth",
        columns="Algorithm",
        values="Median Nodes",
    )

    ax = nodes.plot(
        kind="bar",
        figsize=(9, 5),
        rot=0,
    )
    ax.set_title(f"Search Nodes — {position}")
    ax.set_xlabel("Search Depth")
    ax.set_ylabel("Median Nodes Explored")
    ax.legend(title="Algorithm")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    safe_name = position.lower().replace(" ", "_")
    plt.savefig(f"{safe_name}_nodes.png", dpi=200)
    plt.show()
    plt.close()

    # Graph 2: Execution time
    times = subset.pivot(
        index="Depth",
        columns="Algorithm",
        values="Median Time (s)",
    )

    ax = times.plot(
        kind="bar",
        figsize=(9, 5),
        rot=0,
    )
    ax.set_title(f"Execution Time — {position}")
    ax.set_xlabel("Search Depth")
    ax.set_ylabel("Median Time (seconds)")
    ax.legend(title="Algorithm")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    plt.savefig(f"{safe_name}_time.png", dpi=200)
    plt.show()
    plt.close()

print("All benchmark graphs generated and saved.")
