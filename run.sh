#!/bin/sh

for run in 40 80 100
do 
	head -$run runs.txt | tail -40 | parallel python3 run.py
	echo "Finished runs: $run"
done
