CC     = gcc
CFLAGS = -O2 -fopenmp

all: false_sharing numa_sweep compare_numa

false_sharing: false_sharing.c
	$(CC) $(CFLAGS) $< -o $@
numa_sweep: numa_sweep.c
	$(CC) $(CFLAGS) $< -o $@
compare_numa: compare_numa.c
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -f false_sharing numa_sweep compare_numa
