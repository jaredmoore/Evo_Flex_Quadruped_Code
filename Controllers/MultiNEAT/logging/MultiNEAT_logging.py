"""
    Provide a set of methods to write out population statistics about MultiNEAT to a file.
"""

import os

def write_population_statistics_headers(filename,optional_additions=""):
    """ Write out the headers for population_statistics file. """
    with open(filename, "w") as f:
        f.write("Generation,Individual,Genome_ID,Parent_ID1,Parent_ID2,Fitness")
        f.write(","+str(optional_additions))
        f.write("\n")

def write_population_statistics_headers_station_keeping(filename):
    """ Write out the headers for population_statistics file. """
    with open(filename, "w") as f:
        f.write("Generation,Individual,Genome_ID,Parent_ID1,Parent_ID2,Fitness,Dist_Comp,Var_Comp\n")

def write_population_statistics_headers_multi_trials(filename,num_trials=5,trial_names=[]):
    """ Write out the headers for population_statistics file. """
    with open(filename, "w") as f:
        f.write("Generation,Individual,Genome_ID,Parent_ID1,Parent_ID2,Fitness")
        for i in range(num_trials):
            if trial_names:
                f.write(","+trial_names[i])
            else:
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
        if genomes:
            for i,(gen,fitness) in enumerate(zip(genomes,fitnesses)):
                f.write(str(generation)+
                        ","+str(i)+
                        ","+str(gen.GetID())+
                        ","+str(gen.GetPID1())+
                        ","+str(gen.GetPID2())+
                        ","+str(fitness)+"\n")
        else:
            for i,fitness in enumerate(fitnesses):
                f.write(str(generation)+
                        ","+str(i)+
                        ","+str(-10)+
                        ","+str(-10)+
                        ","+str(-10)+
                        ","+str(fitness)+"\n")            

def write_population_statistics_station_keeping(filename, genomes, fitnesses, dist_comp, var_comp, generation):
    """ Write out the population statistics to a file. 
    
    Args:
        genomes: list of genomes from a MultiNEAT population
        fitnesses: list of fitness values from a MultiNEAT population
        dist_comp: list of distance component of fitness
        var_comp: list of the variance component of fitness
        generation: what generation it is
    """
    with open(filename, "a") as f:
        for i,(gen,fitness,d_comp,v_comp) in enumerate(zip(genomes,fitnesses,dist_comp,var_comp)):
            f.write(str(generation)+
                    ","+str(i)+
                    ","+str(gen.GetID())+
                    ","+str(gen.GetPID1())+
                    ","+str(gen.GetPID2())+
                    ","+str(fitness)+
                    ","+str(d_comp) +
                    ","+str(v_comp)+"\n")

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
                    ","+str(gen.GetID())+
                    ","+str(gen.GetPID1())+
                    ","+str(gen.GetPID2())+
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
            for elem in fitness:
                f.write(","+str(elem))
            f.write("\n")

def write_best_individual(filename,genome):
    """ Save a genome to a file. """
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    genome.Save(filename)
