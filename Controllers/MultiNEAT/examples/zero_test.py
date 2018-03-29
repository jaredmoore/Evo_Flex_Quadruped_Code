import MultiNEAT as NEAT
params = NEAT.Parameters()  

params.PopulationSize = 100

genome = NEAT.Genome(0, 3, 0, 2, False, NEAT.ActivationFunction.UNSIGNED_SIGMOID, NEAT.ActivationFunction.UNSIGNED_SIGMOID, 0, params)

pop = NEAT.Population(genome, params, True, 1.0)

def evaluate(genome):

    # this creates a neural network (phenotype) from the genome

    net = NEAT.NeuralNetwork()
    genome.BuildPhenotype(net)

    # let's input just one pattern to the net, activate it once and get the output

    net.Input( [ 1.0, 0.0, 1.0 ] )
    net.Activate()
    output = net.Output() 

    # the output can be used as any other Python iterable. For the purposes of the tutorial, 
    # we will consider the fitness of the individual to be the neural network that outputs constantly 
    # 0.0 from the first output (the second output is ignored)

    #fitness = 1.0 - output[0]
   
    fitness = 0
    if output[0] >= 0.5:
        output[0] = 1. - output[0] 
    fitness = 0.5 - (0.5 - output[0])

    return fitness, output[0]

for generation in range(100): # run for 100 generations

    outputs = []
    # retrieve a list of all genomes in the population
    genome_list = NEAT.GetGenomeList(pop)

    # apply the evaluation function to all genomes
    for genome in genome_list:
        fitness,output = evaluate(genome)
        genome.SetFitness(fitness)
        outputs.append(output)

    # at this point we may output some information regarding the progress of evolution, best fitness, etc.
    # it's also the place to put any code that tracks the progress and saves the best genome or the entire
    # population. We skip all of this in the tutorial. 
    fitnesses = [g.GetFitness() for g in genome_list]
    print(max(fitnesses),outputs[fitnesses.index(max(fitnesses))])

    # Write fitnesses out to a file with genome ID
    with open("/Users/JMoore/Desktop/test_fitnesses.dat", "a") as f:
        for i,(gen,fitness) in enumerate(zip(genome_list,fitnesses)):
            f.write(str(generation)+
                    ","+str(i)+
                    ","+str(gen.GetID())+
                    ","+str(gen.GetPID1())+
                    ","+str(gen.GetPID2())+
                    ","+str(fitness)+"\n")

    if generation == 99:
        print(genome_list[fitnesses.index(max(fitnesses))].GetPID1(),genome_list[fitnesses.index(max(fitnesses))].GetPID2()) 
        (genome_list[fitnesses.index(max(fitnesses))]).Save("/Users/JMoore/Desktop/test_genome.dat")
    
    if generation % 25 == 0:
        pop.Save("/Users/JMoore/Desktop/test_population_generation_"+str(generation)+".dat")

    # advance to the next generation
    pop.Epoch()
