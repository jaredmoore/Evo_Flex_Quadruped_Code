""" Handle a population of ANNs for experimentation. """

import math
import random

from nsga_config import NSGAConfig
import nsga_genome

class NSGAPopulation(object):
    def __init__(self):

        # total population size
        self._popsize = NSGAConfig.pop_size

        self._create_genomes()

    stats = property(lambda self: (self._best_fitness, self._avg_fitness))

    def __repr__(self):
        s = "Population size: %d" %self._popsize
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
            g = genome.NSGAGenome.create_fully_connected()
            if NSGAConfig.hidden_nodes > 0:
                g.add_hidden_nodes(NSGAConfig.hidden_nodes)
            self._population.append(g)

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
