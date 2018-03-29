"""
	Evolve ANN's to distinguish the logical OR.

	0,0: 0
	1,0: 1
	0,1: 1
	1,1: 1
"""

import math
import random

from ann_wrap import ANN, Basic_Evolve_ANN

pop_size = 50

population = [ANN(2,1,1,c_src=[0,1,2],c_trg=[2,2,3],c_wts=[-1.+2.*random.random() for j in range(3)]) for i in range(pop_size)]
best_ind = 0

for gen in xrange(1000):
	fitnesses = []
	
	# Evaluate the individuals
	for ind in population:
		err = 0.

		# 0,0 Case
		act = ind.activate([0,0])
		err += math.fabs(0.-act[0])

		# 1,0 Case
		act = ind.activate([1,0])
		err += math.fabs(1.-act[0])

		# 0,1 Case
		act = ind.activate([0,1])
		err += math.fabs(1.-act[0])

		# 1,1 Case
		act = ind.activate([1,1])
		err += math.fabs(0.-act[0])

		fitnesses.append(err)

	print("Min Error: "+str(min(fitnesses)))

	best_ind = population[fitnesses.index(min(fitnesses))]

	# Populate the next generation.
	new_pop = [ANN(ann_str=str(best_ind))]

	for i in xrange(pop_size-1):
		# Perform two way tournament selection.
		ind_1 = random.randint(0,pop_size-1)
		ind_2 = random.randint(0,pop_size-1)

		while ind_2 == ind_1:
			ind_2 = random.randint(0,pop_size-1)

		if fitnesses[ind_1] >= fitnesses[ind_2]:
			new_pop.append(ANN(ann_str=str(population[ind_1])))
		else:
			new_pop.append(ANN(ann_str=str(population[ind_2])))

		# Mutate the network.
		Basic_Evolve_ANN.mutate_weight(new_pop[-1])

	population = new_pop

# Validate the best individual

# 0,0 Case
act = ind.activate([0,0])
print("0,0: "+str(math.fabs(0.-act[0])))

# 1,0 Case
act = ind.activate([1,0])
print("1,0: "+str(math.fabs(1.-act[0])))

# 0,1 Case
act = ind.activate([0,1])
print("0,1: "+str(math.fabs(1.-act[0])))

# 1,1 Case
act = ind.activate([1,1])
print("1,1: "+str(math.fabs(0.-act[0])))

print("\n\n"+str(best_ind))