import os
import sys

genomes = []
with open("best_individuals_genomes.dat","r") as f:
	for line in f:
		split_line = line.split(",")
		genomes.append({
			'tnum':split_line[0],
			'rep':split_line[1],
			'gen':split_line[2],
			'ind':split_line[3],
			'f1':split_line[4],
			'genome':",".join(str(i).strip() for i in split_line[5:])
		})

for g in genomes:
	print("Expected Fitness: "+g['f1'])
	print(g['tnum'],g['rep'],g['gen'],g['ind'])
	sys.stdout.flush()
	os.system("python evo_flex_quadruped.py --provide_genome --run_num="+g['rep']+" --exp_num="+g['tnum']+" --validator --eval_time=10 --gens="+g['gen']+" --genome="+g['genome'])