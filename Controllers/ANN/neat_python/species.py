""" Define the operators associated with species in NEAT. """

import random
from config import Config

class Species(object):
    _id = 0 # Global species identifier

    def __init__(self, base_individual, previous_id=None):
        """ Initialize a species.  There must be a base individual to start
            the species.
        """
        self._id = self.__get_new_id(previous_id)
        self._age = 0
        self._subpopulation = []
        self.add(base_individual)
        self.hasBest = False
        self.spawn_amount = 0
        self.no_improvement_age = 0

        self._last_avg_fitness = 0

        self.representant = base_individual

    members = property(lambda self: self._subpopulation)
    age = property(lambda self: self._age)
    id = property(lambda self: self._id)

    @classmethod
    def __get_new_id(cls, previous_id):
        """ Get an id for the species. """
        if not previous_id:
            cls._id += 1
            return cls._id
        else:
            return previous_id

    def add(self, individual):
        """ Add a new individual to the species """
        # Set the species ID
        individual.species_id = self._id
        
        # Add individual to the subpopulation
        self._subpopulation.append(individual)
        
        # Choose the representative individual for the species.
        self.representant = random.choice(self._subpopulation)

    def __iter__(self):
        """ Iterates over individuals """
        return iter(self._subpopulation)

    def __len__(self):
        """ Returns the total number of individuals in this species. """
        return len(self._subpopulation)

    def __str__(self):
        s  = "\n   Species %2d   size: %3d   age: %3d   spawn: %3d   " \
                %(self._id, len(self), self._age, self.spawn_amount)
        s += "\n   No improvement: %3d \t avg. fitness: %1.8f" \
                %(self.no_improvement_age, self._last_avg_fitness)
        return s

    def TournamentSelection(self, k=2):
        """ Tournament selection with size k (default k=2).
            Make sure the population has at least k individuals """
        random.shuffle(self._subpopulation)

        return max(self._subpopulation[:k])

    def average_fitness(self):
        """ Returns the raw average fitness for this species """
        sum = 0.0
        for g in self._subpopulation:
            sum += g.fitness

        try:
            current = sum/len(self)
        except ZeroDivisionError:
            print "Species %d, with length %d is empty! " % (self.__id, len(self))
        else:  # controls species no improvement age
            # if no_improvement_age > threshold, species will be removed
            if current > self._last_avg_fitness:
                self._last_avg_fitness = current
                self.no_improvement_age = 0
            else:
                self.no_improvement_age += 1

        return current

    def reproduce(self):
        """ Returns a list of 'spawn_amount' new individuals """

        offspring = [] # new offspring for this species
        self._age += 1  # increment species age

        # Ensure that there is never a species with zero spawn amount.
        assert self.spawn_amount > 0, "Species %d with zero spawn amount!" % (self._id)

        self._subpopulation.sort()     # sort species's members by their fitness
        self._subpopulation.reverse()  # best members first

        if Config.elitism:
            offspring.append(self._subpopulation[0])
            self.spawn_amount -= 1

        survivors = int(round(len(self)*Config.survival_threshold)) # keep a % of the best individuals

        if survivors > 0:
            self._subpopulation = self._subpopulation[:survivors]
        else:
            # ensure that we have at least one genome to reproduce
            self._subpopulation = self._subpopulation[:1]

        while(self.spawn_amount > 0):

            self.spawn_amount -= 1

            if len(self) > 1:
                # Selects two parents from the remaining individuals in the species and produces a 
                # single individual.  
                # Stanley selects at random, here we use tournament selection (although it is not
                # clear if has any advantages)
                parent1 = self.TournamentSelection()
                parent2 = self.TournamentSelection()

                # Check to make sure that the parents are from the same species.  (Shouldn't happen.)
                assert parent1.species_id == parent2.species_id, "Parents has different species id."
                
                child = parent1.crossover(parent2)
                offspring.append(child.mutate())
            else:
                # Only mutate an individual.
                parent1 = self._subpopulation[0]
                # TODO: temporary hack - the child needs a new id (not the father's)
                child = parent1.crossover(parent1)
                offspring.append(child.mutate())

        # reset species (new members will be added again when speciating)
        self._subpopulation = []

        # select a new random representant member
        self.representant = random.choice(offspring)

        return offspring
