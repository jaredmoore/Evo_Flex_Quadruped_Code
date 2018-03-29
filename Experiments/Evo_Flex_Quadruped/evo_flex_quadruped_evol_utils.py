"""
    Functions associated with the evolutionary process are stored here.
"""

import math
import multiprocessing as mpc
import random

from deap import algorithms
from deap import base
from deap import creator
from deap import tools

import flex_quadruped_utils
import evo_flex_quadruped_simulation

args = ""
lexicase_ordering = []
glob_fit_indicies = []

##########################################################################################
# Logging Methods

def writeFronts(filename,fronts):
    """ Write out the pareto fronts captured during evolution. """
    with open(filename,"w") as f:
        f.write("Generation,Ind,Fit_1,Fit_2,Fit_3\n")
        for gen,front in enumerate(fronts):
            for i,ind in enumerate(front):
                f.write(str(gen)+","+ind+"\n")

def writeHeaders(filename,experiment_type):
    """ Write out the headers for a logging file. """
    with open(filename,"w") as f:
        f.write("Gen,Ind,Fit_1,Fit_2,Fit_3,"+experiment_type().headers()+"\n")        

def writeGeneration(filename,generation,individuals):
    """ Write out the fitness information for a generation. """
    with open(filename,"a") as f:
        for i,ind in enumerate(individuals):
            f.write(str(generation)+","+str(i)+",")
            f.write(",".join(str(f) for f in ind.fitness.values))
            f.write(","+str(ind))
            f.write("\n")

def writeLexicaseOrdering(filename):
    """ Write out the ordering of the fitness metrics selected per generation with lexicase. """
    with open(filename,"w") as f:
        # Write Headers
        f.write("Generation")
        for i in range(len(lexicase_ordering[0])):
            f.write(",Obj_"+str(i))
        f.write("\n")

        for lo in lexicase_ordering:
            f.write(','.join(str(i) for i in lo)+"\n")

##########################################################################################

def evaluate_individual(individual):
    """ Wrapper to call Simulation which will evaluate an individual.  

    Args:
        individual: arguments to pass to the simulation

    Returns:
        fitness of an individual
    """

    # Set the parameters for the simulation.
    evo_flex_quadruped_simulation.eval_time = args.eval_time
    evo_flex_quadruped_simulation.run_num = args.run_num
    evo_flex_quadruped_simulation.output_path = args.output_path
    file_prefix = ""
    if args.debug_runtime:
        evo_flex_quadruped_simulation.file_prefix = file_prefix = "DEBUG_RUNTIME_EVO_QUAD_"+str(args.run_num)+"_"
    elif args.validator:
        evo_flex_quadruped_simulation.file_prefix = file_prefix = "Evo_Quad_Validation_"+str(args.run_num)+"_Gen_"+str(args.gens)+"_"
    simulation = evo_flex_quadruped_simulation.Simulation(log_frames=args.log_frames, run_num=args.run_num, eval_time=args.eval_time, dt=.02, n=4, file_prefix=file_prefix)
    return simulation.evaluate_individual(individual)

##########################################################################################

def roulette_selection(objs, obj_wts):
    """ Select a listing of objectives based on roulette selection. """
    obj_ordering = []

    tmp_objs = objs
    tmp_wts = obj_wts

    for i in range(len(objs)):
        sel_objs = [list(a) for a in zip(tmp_objs, tmp_wts)]

        # Shuffle the objectives
        random.shuffle(sel_objs)

        # Generate a random number between 0 and 1.
        ran_num = random.random()

        # Iterate through the objectives until we select the one we want.
        for j in range(len(sel_objs)):
            if sel_objs[j][1] > ran_num:
                obj_ordering.append(sel_objs[j][0])

                # Remove the objective and weight from future calculations.
                ind = tmp_objs.index(sel_objs[j][0])

                del tmp_objs[ind]
                del tmp_wts[ind]

                # Rebalance the weights for the next go around.
                tmp_wts = [k/sum(tmp_wts) for k in tmp_wts]
            else:
                ran_num -= sel_objs[j][1]

    return obj_ordering

def lexicase_selection(population,k,tournsize,shuffle=True,num_objectives=0,weighted_objectives=False,per_ind_shuffle=True):
    """ Implements the lexicase selection algorithm proposed by Spector.

    Args:
        population: population of individuals to select from
        k: how many individuals to select
        tournsize: tournament size for each selection
        shuffle: whether to randomly shuffle the indices
    Returns:
        An individual selected using the algorithm
    """
    selected_individuals = []

    for i in range(k):
        # Sample the tournsize individuals from the population for the comparison
        sel_inds = random.sample(population,tournsize)

        fit_indicies = []
        if per_ind_shuffle:
            # Get the length of fitnesses used in the experiment and shuffle the indices for comparing fitnesses
            fit_indicies = [i for i in range(len(sel_inds[0].fitness.weights))]

            # Weight the objectives.
            if weighted_objectives:
                obj_weights = [0.15,0.75,0.1]
                fit_indicies = roulette_selection(fit_indicies,obj_weights)
            elif shuffle:
                random.shuffle(fit_indicies)
            if num_objectives:
                fit_indicies = [i for i in fit_indicies[:num_objectives]]

            lexicase_ordering.append(fit_indicies)
        else:
            fit_indicies = glob_fit_indicies

        # Now that we have the indicies, perform the actual lexicase selection.
        # Using a threshold of .9 (tied if within .9)
        for fi in fit_indicies:
            # Figure out if this is a minimization or maximization problem.
            min_max = (-1*sel_inds[0].fitness.weights[fi])

            # Rank the individuals based on fitness performance for this metric.
            # Format: fit_value,index in sel_ind,rank
            fit_ranks = [[ind.fitness.values[fi],i,-1] for i,ind in enumerate(sel_inds)]
            fit_ranks = [[i[0],i[1],j] for j,i in enumerate(sorted(fit_ranks,key=lambda x: (min_max*x[0])))]

            # Check to see if we're within the threshold value.
            for i in range(1,len(fit_ranks)):
                if math.fabs(fit_ranks[i][0]-fit_ranks[0][0])/(fit_ranks[0][0]+0.0000001) < 0.1:
                    fit_ranks[i][2] = fit_ranks[0][2]

            # Check to see if we have ties.
            for i in range(1,len(fit_ranks)):
                if fit_ranks[0][2] == fit_ranks[i][2]:
                    tie = True
                    tie_index = i+1
                elif i == 1:
                    tie = False
                    break
                else:
                    tie_index = i
                    break
            if tie:
                sel_inds = [sel_inds[i[1]] for i in fit_ranks[:tie_index]]
            else:
                selected_individuals.append(sel_inds[fit_ranks[0][1]])
                tie = False
                break

        # If tie is True, we haven't selected an individual as we've reached a tie state.
        # Select randomly from the remaining individuals in that case.
        if tie:
            selected_individuals.append(random.choice(sel_inds))

    return selected_individuals

##########################################################################################

def shuffle_fit_indicies(individual):
    """ Shuffle the fitness indicies and record them in the lexicase log. """
    global glob_fit_indicies, lexicase_ordering

    fit_indicies = [i for i in range(len(individual.fitness.weights))]

    random.shuffle(fit_indicies)

    lexicase_ordering.append(fit_indicies)

    glob_fit_indicies = fit_indicies

def common_evolution_run(**kwargs):
    """ Base function for the main file to call.  

    Sets up the evolutionary environment and then passes off to the type of 
    evolutionary run that we want to conduct.
    
    Arguments:
        evol_type: type of evolutionary run ['norm_ga','lexicase']
        output_path: where to write the files to
        run_num: run number of the replicate
        pop_size: population size
    """
    # Seed only the evolutionary runs.
    random.seed(args.run_num)

    # Establish name of the output files and write appropriate headers.
    out_fit_file = kwargs['output_path']+str(kwargs['run_num'])+"_fitnesses.dat"
    writeHeaders(out_fit_file,kwargs['exp_class'])

    #creator.create("Fitness", base.Fitness, weights=(1.0,-1.0,1.0,1.0,-1.0,))
    creator.create("Fitness", base.Fitness, weights=(1.0,1.0,-1.0,))

    if kwargs['evol_type'] == 'norm_ga':
        creator.create("Individual", kwargs['exp_class'], fitness=creator.Fitness)
    elif kwargs['evol_type'] == 'lexicase':
        creator.create("Individual", kwargs['exp_class'], fitness=creator.Fitness)

    # Create the toolbox for setting up DEAP functionality.
    toolbox = base.Toolbox()

    # Define an individual for use in constructing the population.
    toolbox.register("individual", flex_quadruped_utils.initIndividual, creator.Individual)
    toolbox.register("mutate", flex_quadruped_utils.mutate)
    toolbox.register("mate", tools.cxTwoPoint)

    # Create a population as a list.
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # Register the evaluation function.
    toolbox.register("evaluate", evaluate_individual)

    if kwargs['evol_type'] == 'norm_ga':
        # Register the selection function.
        toolbox.register("select", lexicase_selection, tournsize=4, shuffle=False, num_objectives=1)
    elif kwargs['evol_type'] == 'lexicase':
        # Register the selection function.
        toolbox.register("select", lexicase_selection, tournsize=4, shuffle=True, weighted_objectives=False, per_ind_shuffle=True)

    # Multiprocessing component.
    cores = mpc.cpu_count()
    pool = mpc.Pool(processes=cores-2)
    toolbox.register("map", pool.map)

    # Crossover and mutation probability
    cxpb, mutpb = 0.5, 0.04

    # Set the mutation value for hopper utils
    flex_quadruped_utils.mutate_chance = mutpb

    # Setup the population.
    pop = toolbox.population(n=kwargs['pop_size'])

    # Run the first set of evaluations.
    fitnesses = toolbox.map(toolbox.evaluate, pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    # Log the progress of the population. (For Generation 0)
    writeGeneration(out_fit_file,0,pop)

    for g in range(1,args.gens):
        #if kwargs['evol_type'] == 'lexicase':
        #    shuffle_fit_indicies(pop[0])
        
        # Pull out the elite individual to save for later.
        #elite = tools.selBest(pop, k=1)

        #pop = toolbox.select(pop, k=len(pop)-1)
        pop = toolbox.select(pop, k=len(pop))
        pop = [toolbox.clone(ind) for ind in pop]

        # Request new id's for the population.
        for ind in pop:
            ind.get_new_id()

        for child1, child2 in zip(pop[::2], pop[1::2]):
            if random.random() < cxpb:
                # Must serialize and deserialize due to the type of object.
                child1_serialized, child2_serialized = toolbox.mate(child1.serialize(), child2.serialize())
                child1.deserialize(child1_serialized)
                child2.deserialize(child2_serialized)
                del child1.fitness.values, child2.fitness.values

        for mutant in pop:
            toolbox.mutate(mutant)
            del mutant.fitness.values
        
        invalids = [ind for ind in pop if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalids)
        for ind, fit in zip(invalids, fitnesses):
            ind.fitness.values = fit

        # Check to see if we have a new elite individual.
        #new_elite = tools.selBest(pop, k=1)
        #elite = tools.selBest([elite[0],new_elite[0]],k=1)

        # Add the elite individual back into the population.
        #pop = elite+pop

        print("Generation "+str(g))
        # Log the progress of the population.
        writeGeneration(out_fit_file,g,pop)

    #if kwargs['evol_type'] == 'lexicase':
    writeLexicaseOrdering(kwargs['output_path']+str(kwargs['run_num'])+"_lexicase_ordering_log.dat")

##########################################################################################    

def nsga_evolution_run(**kwargs):
    """ Base function for the main file to call.  

    Sets up the evolutionary environment and then passes off to the type of 
    evolutionary run that we want to conduct.
    
    Arguments:
        evol_type: type of evolutionary run ['norm_ga','lexicase']
        output_path: where to write the files to
        run_num: run number of the replicate
        pop_size: population size
    """
    # Seed only the evolutionary runs.
    random.seed(args.run_num)

    # Establish name of the output files and write appropriate headers.
    out_fit_file = kwargs['output_path']+str(kwargs['run_num'])+"_fitnesses.dat"
    out_fronts_file = kwargs['output_path']+str(kwargs['run_num'])+"_fronts.dat"
    writeHeaders(out_fit_file,kwargs['exp_class'])

    #creator.create("Fitness", base.Fitness, weights=(1.0,-1.0,1.0,1.0,-1.0,))
    creator.create("Fitness", base.Fitness, weights=(1.0,1.0,-1.0,))

    creator.create("Individual", kwargs['exp_class'], fitness=creator.Fitness)

    # Create the toolbox for setting up DEAP functionality.
    toolbox = base.Toolbox()

    # Define an individual for use in constructing the population.
    toolbox.register("individual", flex_quadruped_utils.initIndividual, creator.Individual)
    toolbox.register("mutate", flex_quadruped_utils.mutate)
    toolbox.register("mate", tools.cxTwoPoint)

    # Create a population as a list.
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # Register the evaluation function.
    toolbox.register("evaluate", evaluate_individual)

    toolbox.register("select", tools.selNSGA2)

    # Multiprocessing component.
    cores = mpc.cpu_count()
    pool = mpc.Pool(processes=cores-2)
    toolbox.register("map", pool.map)

    # Crossover and mutation probability
    cxpb, mutpb = 0.5, 0.04

    # Set the mutation value for quadruped utils
    flex_quadruped_utils.mutate_chance = mutpb

    # Setup the population.
    pop = toolbox.population(n=kwargs['pop_size'])

    # Run the first set of evaluations.
    invalid_ind = [ind for ind in pop if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit        

    # This is just to assign the crowding distance to the individuals
    # no actual selection is done
    pop = toolbox.select(pop, len(pop))

    # Log the progress of the population. (For Generation 0)
    writeGeneration(out_fit_file,0,pop)

    # Track the progress of NSGA
    fronts = []
    #fronts.append(','.join(str(i) for i in ind.fitness.values) for ind in pop)
    fronts.append(str(ind.id)+','+','.join(str(i) for i in ind.fitness.values) for ind in tools.sortLogNondominated(pop, args.pop_size, first_front_only=True))

    # Request new id's for the population.
    for ind in pop:
        ind.get_new_id()

    for g in range(1,args.gens):
        # Variate the population
        offspring = tools.selTournamentDCD(pop, len(pop))
        offspring = [toolbox.clone(ind) for ind in offspring]

        # Update the fronts information.
        #fronts.append(','.join(str(i) for i in ind.fitness.values) for ind in pop)
        fronts.append(str(ind.id)+','+','.join(str(i) for i in ind.fitness.values) for ind in tools.sortLogNondominated(pop, args.pop_size, first_front_only=True))

        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < cxpb:
                # Must serialize and deserialize due to the type of object.
                child1_serialized, child2_serialized = toolbox.mate(child1.serialize(), child2.serialize())
                child1.deserialize(child1_serialized)
                child2.deserialize(child2_serialized)
                del child1.fitness.values, child2.fitness.values

        # Mutate the population.
        for mutant in offspring:
            toolbox.mutate(mutant)
            del mutant.fitness.values

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Select the next generation population
        pop = toolbox.select(pop + offspring, kwargs['pop_size'])

        # Request new id's for the population.
        for ind in pop:
            ind.get_new_id()

        print("Generation "+str(g))
        # Log the progress of the population.
        writeGeneration(out_fit_file,g,pop)

    # Write out the fronts data.
    writeFronts(out_fronts_file,fronts)