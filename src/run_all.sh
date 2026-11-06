#!/usr/bin/env bash
# Runs every part of the experiment (run from the src/ folder).
set -e
make
echo "=== NUMA topology ==="; numactl --hardware; lscpu -e
echo "=== Part A: protocol simulator ==="; python3 coherence_sim.py 1000
echo "=== Part B1: false sharing, 2 threads ==="
OMP_NUM_THREADS=2 ./false_sharing adjacent
OMP_NUM_THREADS=2 ./false_sharing padded
echo "=== Tables 1 and 2: default placement ==="; ./compare_numa
echo "=== Part B2: local memory ===";  numactl --cpunodebind=0 --membind=0 ./compare_numa
echo "=== Part B2: remote memory ==="; numactl --cpunodebind=0 --membind=1 ./compare_numa
