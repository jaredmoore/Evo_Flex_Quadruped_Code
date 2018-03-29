""" Define a population in NEAT. """

import math
import random

from config import Config
import genome
import species

class Population(object):

    def __init__(self):

        # total population size
        self._popsize = Config.pop_size
        # currently living species
        self._species = []
        # species history
        self._species_log = []

        # Statistics
        self._avg_fitness = []
        self._best_fitness = []

        self._create_genomes()
        self._generation = -1

    stats = property(lambda self: (self._best_fitness, self._avg_fitness))
    species_log = property(lambda self: self._species_log)

    def __repr__(self):
        s = "Population size: %d" %self._popsize
        s += "\nTotal species: %d" %len(self._species)
        return s

    def __len__(self):
        return len(self._population)

    def __iter__(self):
        return iter(self._population)

    def __getitem__(self, key):
        return self._population[key]

    def get_genomes(self):
        """ Get a list of the genomes in the population. """

        return self._population

    def _create_genomes(self):
        """ Create the population of individuals. """

        self._population = []
        for i in xrange(self._popsize):
            g = genome.Genome.create_fully_connected()
            if Config.hidden_nodes > 0:
                g.add_hidden_nodes(Config.hidden_nodes)
            self._population.append(g)

    def _speciate(self, report):
        """ Group genomes into species by similarity """
        # Speciate the population
        for individual in self:
            found = False
            for s in self._species:
                if individual.distance(s.representant) < Config.compatibility_threshold:
                    s.add(individual)
                    found = True
                    break

            if not found: # create a new species for this lone chromosome
                self._species.append(species.Species(individual))

        # python technical note:
        # we need a "working copy" list when removing elements while looping
        # otherwise we might end up having sync issues
        for s in self._species[:]:
            # this happens when no genomes are compatible with the species
            if len(s) == 0:
                if report:
                    print "Removing species %d for being empty" % s.id
                # remove empty species
                self._species.remove(s)

        self._set_compatibility_threshold()

    def _set_compatibility_threshold(self):
        """ Controls compatibility threshold """
        if len(self._species) > Config.species_size:
            Config.compatibility_threshold += Config.compatibility_change
        elif len(self._species) < Config.species_size:
            if Config.compatibility_threshold > Config.compatibility_change:
                Config.compatibility_threshold -= Config.compatibility_change
            else:
                print 'Compatibility threshold cannot be changed (minimum value has been reached)'

    def average_fitness(self):
        """ Returns the average raw fitness of population """
        sum = 0.0
        for g in self:
            sum += g.fitness

        return sum/len(self)

    def stdeviation(self):
        """ Returns the population standard deviation """
        # first compute the average
        u = self.average_fitness()
        error = 0.0

        try:
            # now compute the distance from average
            for g in self:
                error += (u - g.fitness)**2
        except OverflowError:
            #TODO: catch OverflowError: (34, 'Numerical result out of range')
            print "Overflow - printing population status"
            print "error = %f \t average = %f" %(error, u)
            print "Population fitness:"
            print [g.fitness for g in self]

        return math.sqrt(error/len(self))

    def _compute_spawn_levels(self):
        """ Compute each species' spawn amount (Stanley, p. 40) """

        # 1. Boost if young and penalize if old
        species_stats = []
        for s in self._species:
            if s.age < Config.youth_threshold:
                species_stats.append(s.average_fitness()*Config.youth_boost)
            elif s.age > Config.old_threshold:
                species_stats.append(s.average_fitness()*Config.old_penalty)
            else:
                species_stats.append(s.average_fitness())

        # 2. Share fitness (only usefull for computing spawn amounts)
        # More info: http://tech.groups.yahoo.com/group/neat/message/2203
        # Sharing the fitness is only meaningful here
        # we don't really have to change each individual's raw fitness
        total_average = 0.0
        for s in species_stats:
                total_average += s

         # 3. Compute spawn
        for i, s in enumerate(self._species):
            s.spawn_amount = int(round((species_stats[i]*self._popsize/total_average))) if int(round((species_stats[i]*self._popsize/total_average))) > 0 else 0

    def _tournament_selection(self, k=2):
        """ Tournament selection with size k (default k=2).
            Make sure the population has at least k individuals """
        random.shuffle(self._population)

        return max(self._population[:k])

    def _log_species(self):
        """ Logging species data for visualizing speciation """
        higher = max([s.id for s in self._species])
        temp = []
        for i in xrange(1, higher+1):
            found_specie = False
            for s in self._species:
                if i == s.id:
                    temp.append(len(s))
                    found_specie = True
                    break
            if not found_specie:
                temp.append(0)
        self._species_log.append(temp)

    def _population_diversity(self):
        """ Calculates the diversity of population: total average weights,
            number of connections, nodes """

        num_nodes = 0
        num_conns = 0
        avg_weights = 0.0

        for g in self:
            num_nodes += len(g.node_genes)
            num_conns += len(g.conn_genes)
            for cg in g.conn_genes:
                avg_weights += cg.weight

        total = len(self)
        return (num_nodes/total, num_conns/total, avg_weights/total)

    def epoch(self, report=True):
        """ Runs NEAT's genetic algorithm for an epoch.

            Assumes that the individuals have already been evaluated and have
            their fitnesses set externally.

            Keyword arguments:
            report -- show stats at each epoch (default True)
        """
        self._generation += 1

        if report: print '\n ****** Running generation %d ****** \n' % self._generation

        # Speciates the population
        self._speciate(report)

        # Current generation's best chromosome
        self._best_fitness.append(max(self._population))
        
        # Current population's average fitness
        self._avg_fitness.append(self.average_fitness())

        # Remove stagnated species and its members (except if it has the best chromosome)
        for s in self._species[:]:
            if s.no_improvement_age > Config.max_stagnation and len(self._species) > 1:
                if not s.hasBest:
                    if report:
                        print "\n   Species %2d (with %2d individuals) is stagnated: removing it" \
                                %(s.id, len(s))
                    # removing species
                    self._species.remove(s)
                    
                    # removing all the species' members
                    for g in self._population[:]:
                        if g.species_id == s.id:
                            self._population.remove(g)

        # Remove "super-stagnated" species (even if it has the best chromosome)
        # It is not clear if it really avoids local minima
        for s in self._species[:]:
            if s.no_improvement_age > 2*Config.max_stagnation and len(self._species) > 1:
                if report:
                    print "\n   Species %2d (with %2d individuals) is super-stagnated: removing it" \
                            %(s.id, len(s))
                # removing species
                self._species.remove(s)
                
                # removing all the species' members
                for g in self.__population[:]:
                    if g.species_id == s.id:
                        self.__population.remove(g)

        # Compute spawn levels for each remaining species
        self._compute_spawn_levels()

        # Removing species with spawn amount = 0
        for s in self._species[:]:
            # This rarely happens
            if s.spawn_amount == 0:
                if report:
                    print '   Species %2d age %2s removed: produced no offspring' %(s.id, s.age)
                for g in self._population[:]:
                    if g.species_id == s.id:
                        self._population.remove(g)
                self._species.remove(s)

        # Logging speciation stats
        # self._log_species()

        if report:
            #print 'Poluation size: %d \t Divirsity: %s' %(len(self), self.__population_diversity())
            print 'Population\'s average fitness: %3.5f stdev: %3.5f' %(self._avg_fitness[-1], self.stdeviation())
            #print 'Best fitness: %2.12s - size: %s - species %s - id %s' \
            #    %(best.fitness, best.size(), best.species_id, best.id)

            # print some "debugging" information
            print 'Species length: %d totalizing %d individuals' \
                    %(len(self._species), sum([len(s) for s in self._species]))
            print 'Species ID       : %s' % [s.id for s in self._species]
            print 'Each species size: %s' % [len(s) for s in self._species]
            print 'Amount to spawn  : %s' % [s.spawn_amount for s in self._species]
            print 'Species age      : %s' % [s.age for s in self._species]
            print 'Species no improv: %s' % [s.no_improvement_age for s in self._species] # species no improvement age

            
        # -------------------------- Producing new offspring -------------------------- #
        new_population = [] # next generation's population

        # Spawning new population
        for s in self._species:
            new_population.extend(s.reproduce())

        # ----------------------------#
        # Controls under or overflow  #
        # ----------------------------#
        fill = (self._popsize) - len(new_population)
        if fill < 0: # overflow
            if report: print '   Removing %d excess individual(s) from the new population' %-fill
            # TODO: This is dangerous! I can't remove a species' representant!
            new_population = new_population[:fill] # Removing the last added members

        if fill > 0: # underflow
            if report: print '   Producing %d more individual(s) to fill up the new population' %fill

            while fill > 0:
                # Selects a random chromosome from population
                parent1 = random.choice(self._population)
                # Search for a mate within the same species
                found = False
                for c in self:
                    # what if c is parent1 itself?
                    if c.species_id == parent1.species_id:
                        child = parent1.crossover(c)
                        new_population.append(child.mutate())
                        found = True
                        break
                if not found:
                    # If no mate was found, just mutate it
                    new_population.append(parent1.mutate())
                fill -= 1

        assert self._popsize == len(new_population), 'Different population sizes!'
        # Updates current population
        self._population = new_population[:]
