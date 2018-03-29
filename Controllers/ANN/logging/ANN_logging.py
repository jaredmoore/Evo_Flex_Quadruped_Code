"""
    Provide a set of methods to write out population statistics about the ANN to a file.
"""

import os

def write_population_statistics_headers(filename):
    """ Write out the headers for population_statistics file. """
    with open(filename, "w") as f:
        f.write("Generation,Individual,Fitness\n")

def write_population_statistics_headers_multi_trials(filename,num_trials=5):
    """ Write out the headers for population_statistics file. """
    with open(filename, "w") as f:
        f.write("Generation,Individual,Fitness")
        for i in range(num_trials):
            f.write(",fit_"+str(i))
        f.write("\n")

def write_population_statistics(filename, genomes, fitnesses, generation):
    """ Write out the population statistics to a file. 
    
    Args:
        genomes: list of genomes from a MultiNEAT population
        fitnesses: list of fitness values from a MultiNEAT population
        generation: what generation it is
    """
    with open(filename, "a") as f:
        for i,(gen,fitness) in enumerate(zip(genomes,fitnesses)):
            f.write(str(generation)+
                    ","+str(i)+
                    ","+str(fitness)+"\n")

def write_population_statistics_multi_trials(filename, genomes, fitnesses, generation):
    """ Write out the population statistics to a file. 
    
    Args:
        genomes: list of genomes from a MultiNEAT population
        fitnesses: list of fitness values from a MultiNEAT population
        generation: what generation it is
    """
    with open(filename, "a") as f:
        for i,(gen,fitness) in enumerate(zip(genomes,fitnesses)):
            f.write(str(generation)+
                    ","+str(i)+
                    ","+str(fitness[0]))
            for elem in fitness[1]:
                f.write(","+str(elem))
            f.write("\n")

def write_population_statistics_multi_component(filename, genomes, fitnesses, generation):
    """ Write out the population statistics to a file with a multi-component fitness function. 
    
    Args:
        genomes: list of genomes from a MultiNEAT population
        fitnesses: list of fitness values from a MultiNEAT population
        generation: what generation it is
    """
    with open(filename, "a") as f:
        for i,(gen,fitness) in enumerate(zip(genomes,fitnesses)):
            f.write(str(generation)+
                    ","+str(i)+
                    ","+str(gen.GetID())+
                    ","+str(gen.GetPID1())+
                    ","+str(gen.GetPID2()))
            for elem in fitnesses:
                f.write(","+str(elem))
            f.write("\n")

def write_best_individual(filename,genome):
    """ Save a genome to a file. """
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    with open(filename, 'w') as f:
        f.write(str(genome))
