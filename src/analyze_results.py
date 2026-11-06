#!/usr/bin/env python3
"""Reads ../data/*.csv, writes the graphs to ../graphs and the ratio tables to
../results/results_summary.md.   Usage (from src/):  python3 analyze_results.py
Requires: pandas, matplotlib"""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
GRAPHS = os.path.join(HERE, "..", "graphs")
RESULTS = os.path.join(HERE, "..", "results")
os.makedirs(GRAPHS, exist_ok=True)
os.makedirs(RESULTS, exist_ok=True)

C_ADJ, C_PAD, C_A, C_B, C_C = "#d1495b", "#00798c", "#30638e", "#edae49", "#66a182"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 130})

fs = pd.read_csv(os.path.join(DATA, "false_sharing_results.csv"))
ns = pd.read_csv(os.path.join(DATA, "numa_sweep_results.csv"))
sim = pd.read_csv(os.path.join(DATA, "simulator_totals.csv"))


def t(placement, layout, threads):
    r = fs[(fs.placement == placement) & (fs.layout == layout) & (fs.threads == threads)]
    return float(r.time_s.iloc[0])


# 1. Simulator: bus transactions (log scale)
fig, ax = plt.subplots(figsize=(6.4, 3.8))
protos = ["MSI", "MESI", "MOESI"]
w = 0.36
for k, (lay, col) in enumerate([("adjacent", C_ADJ), ("padded", C_PAD)]):
    vals = [int(sim[(sim.layout == lay) & (sim.protocol == p)].bus_transactions.iloc[0]) for p in protos]
    bars = ax.bar([i + (k - 0.5) * w for i in range(3)], vals, w, label=lay, color=col)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.12, str(v), ha="center", fontsize=8)
ax.set_yscale("log"); ax.set_ylim(1, 20000)
ax.set_xticks(range(3)); ax.set_xticklabels(protos)
ax.set_ylabel("Bus transactions (log scale)")
ax.set_title("Simulator: bus transactions, 1000 iterations (4000 memory ops)")
ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(GRAPHS, "01_simulator_bus_transactions.png")); plt.close(fig)

# 2. Simulator: where the extra cost goes (adjacent layout)
fig, ax = plt.subplots(figsize=(6.4, 3.8))
cols = [("writeback", "Write-backs to memory", C_ADJ), ("c2c", "Cache-to-cache transfers", C_A),
        ("silent_E_to_M", "Silent E->M writes", C_C)]
w = 0.26
for k, (c, lab, col) in enumerate(cols):
    vals = [int(sim[(sim.layout == "adjacent") & (sim.protocol == p)][c].iloc[0]) for p in protos]
    bars = ax.bar([i + (k - 1) * w for i in range(3)], vals, w, label=lab, color=col)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 40, str(v), ha="center", fontsize=8)
ax.set_xticks(range(3)); ax.set_xticklabels(protos)
ax.set_ylabel("Count (1000 iterations)")
ax.set_title("Simulator, adjacent layout: write-backs vs cache-to-cache")
ax.set_ylim(0, 4600); ax.legend(fontsize=8); fig.tight_layout()
fig.savefig(os.path.join(GRAPHS, "02_simulator_writeback_vs_c2c.png")); plt.close(fig)

# 3. Execution time vs threads (default placement)
fig, ax = plt.subplots(figsize=(6.4, 3.8))
th = [1, 2, 4]
for lay, col in [("adjacent", C_ADJ), ("padded", C_PAD)]:
    ax.plot(th, [t("default", lay, n) for n in th], marker="o", label=lay, color=col)
ax.set_xticks(th); ax.set_xlabel("Threads"); ax.set_ylabel("Time (s)")
ax.set_title("False sharing: time vs threads (default placement)")
ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(GRAPHS, "03_false_sharing_time_vs_threads.png")); plt.close(fig)

# 4. Speed-up vs threads (default placement) with ideal line
fig, ax = plt.subplots(figsize=(6.4, 3.8))
for lay, col in [("adjacent", C_ADJ), ("padded", C_PAD)]:
    base = t("default", lay, 1)
    ax.plot(th, [base / t("default", lay, n) for n in th], marker="o", label=lay, color=col)
ax.plot(th, th, "k--", alpha=0.5, label="ideal")
ax.set_xticks(th); ax.set_xlabel("Threads"); ax.set_ylabel("Speed-up vs 1 thread")
ax.set_title("Scalability (default placement)")
ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(GRAPHS, "04_scalability_speedup.png")); plt.close(fig)

# 5. Adjacent / padded ratio per thread count and placement
fig, ax = plt.subplots(figsize=(6.4, 3.8))
w = 0.26
for k, (pl, col) in enumerate([("default", C_A), ("local", C_B), ("remote", C_C)]):
    vals = [t(pl, "adjacent", n) / t(pl, "padded", n) for n in th]
    bars = ax.bar([i + (k - 1) * w for i in range(3)], vals, w, label=pl, color=col)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center", fontsize=8)
ax.axhline(1, color="k", lw=0.8)
ax.set_xticks(range(3)); ax.set_xticklabels([f"{n} thread{'s' if n > 1 else ''}" for n in th])
ax.set_ylabel("adjacent time / padded time")
ax.set_title("Cost of false sharing (ratio > 1 = adjacent slower)")
ax.set_ylim(0.9, 1.45); ax.legend(title="Run"); fig.tight_layout()
fig.savefig(os.path.join(GRAPHS, "05_false_sharing_ratio.png")); plt.close(fig)

# 6. NUMA: local vs remote memory sweep
fig, ax = plt.subplots(figsize=(6.4, 3.8))
w = 0.36
for k, (pl, col) in enumerate([("local", C_A), ("remote", C_B)]):
    vals = [float(ns[(ns.placement == pl) & (ns.threads == n)].time_s.iloc[0]) for n in (1, 2)]
    bars = ax.bar([i + (k - 0.5) * w for i in range(2)], vals, w, label=f"{pl} memory", color=col)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.002, f"{v:.4f}", ha="center", fontsize=8)
ax.set_xticks(range(2)); ax.set_xticklabels(["1 thread", "2 threads"])
ax.set_ylabel("Time (s)"); ax.set_ylim(0, 0.13)
ax.set_title("NUMA: 512 MB sweep, local vs remote memory")
ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(GRAPHS, "06_numa_local_vs_remote.png")); plt.close(fig)

# 7. False sharing across NUMA placements (2 and 4 threads)
fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.6), sharey=True)
for ax, n in zip(axes, (2, 4)):
    w = 0.36
    for k, (lay, col) in enumerate([("adjacent", C_ADJ), ("padded", C_PAD)]):
        vals = [t(pl, lay, n) for pl in ("default", "local", "remote")]
        ax.bar([i + (k - 0.5) * w for i in range(3)], vals, w, label=lay, color=col)
    ax.set_xticks(range(3)); ax.set_xticklabels(["default", "local", "remote"])
    ax.set_title(f"{n} threads")
axes[0].set_ylabel("Time (s)"); axes[0].legend()
fig.suptitle("False-sharing time under different NUMA placements")
fig.tight_layout(); fig.savefig(os.path.join(GRAPHS, "07_false_sharing_by_placement.png")); plt.close(fig)

# ---- results_summary.md ----
L = []
L.append("# Results summary (generated by src/analyze_results.py)\n")
L.append("## Table 1 - false sharing, 100,000,000 increments (time in s)\n")
L.append("| Run | Threads | Adjacent | Padded | Adjacent / Padded | Speed-up adjacent | Speed-up padded |")
L.append("|---|---|---|---|---|---|---|")
for pl in ("default", "local", "remote"):
    for n in th:
        a, p = t(pl, "adjacent", n), t(pl, "padded", n)
        L.append(f"| {pl} | {n} | {a:.4f} | {p:.4f} | {a/p:.2f} | {t(pl,'adjacent',1)/a:.2f} | {t(pl,'padded',1)/p:.2f} |")
L.append("\nAll 18 runs gave Final Count = 100000000 (Correct).\n")
L.append("## Table 2 - 512 MB memory sweep, 4 passes (time in s)\n")
L.append("| Threads | Default | Local (--membind=0) | Remote (--membind=1) | Remote / Local |")
L.append("|---|---|---|---|---|")
def s(pl, n): return float(ns[(ns.placement == pl) & (ns.threads == n)].time_s.iloc[0])
for n in (1, 2):
    L.append(f"| {n} | {s('default',n):.4f} | {s('local',n):.4f} | {s('remote',n):.4f} | {s('remote',n)/s('local',n):.2f} |")
L.append("\n## Section 9.3 - results to record\n")
L.append("| Run | Time (s) |\n|---|---|")
L.append("| adjacent, 2 threads (Program 2) | 0.0185 |")
L.append("| padded, 2 threads (Program 2) | 0.0151 |")
for pl, lab in (("local", "LOCAL (--membind=0)"), ("remote", "REMOTE (--membind=1)")):
    for n in (1, 2):
        L.append(f"| Table 2, memory {lab}, {n} thread{'s' if n>1 else ''} | {s(pl,n):.4f} |")
L.append("| adjacent, one thread on each node (optional) | not run |")
L.append("\n**Ratios**\n")
L.append(f"- adjacent / padded, Program 2 (2 threads): 0.0185 / 0.0151 = **{0.0185/0.0151:.2f}**")
L.append(f"- adjacent / padded, compare_numa default (2 threads): **{t('default','adjacent',2)/t('default','padded',2):.2f}**")
L.append(f"- remote / local, Program 3 (2 threads, 2-node VM): 0.0978 / 0.0977 = **{0.0978/0.0977:.2f}**")
L.append(f"- remote / local, Table 2 (1 thread): **{s('remote',1)/s('local',1):.2f}**, (2 threads): **{s('remote',2)/s('local',2):.2f}**")
with open(os.path.join(RESULTS, "results_summary.md"), "w") as f:
    f.write("\n".join(L) + "\n")
print("done")
