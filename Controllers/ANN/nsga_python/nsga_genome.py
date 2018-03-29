"""
    Define the genome for a NEAT based ANN along with the two gene types: NodeGene and ConnectionGene.
"""

import math
import random
import sys

from nsga_config import NSGAConfig

class NSGAGenome(object):
    _id = 0 # Global genome identifier

    @classmethod
    def genome_from_file(cls,filename):
        """ Build a genome from a provided file. """
        new_genome = NSGAGenome(-1,-1)
        new_genome._input_nodes = 0
        new_genome._output_nodes = 0

        with open(filename,"r") as f:
            for i,line in enumerate(f):
                if i == 0:
                    assert line.split()[0] == "GenomeStart", "File does not conform to ANN!"
                else:
                    split_line = line.split()
                    if split_line[0] == "Node":
                        new_genome.add_node_gene(split_line[1],split_line[2])

                        # Adjust inputs and outputs accordingly.
                        if split_line[2] == "INPUT":
                            new_genome._input_nodes += 1
                        elif split_line[2] == "OUTPUT":
                            new_genome._output_nodes += 1
                    elif split_line[0] == "Link":
                        new_genome.add_connection_gene(split_line[1],split_line[2],split_line[3],split_line[4],split_line[5])
                    else:
                        break

        return new_genome

    @classmethod
    def __get_new_id(cls):
        cls._id += 1
        return cls._id

    def __init__(self, parent1_id, parent2_id):
        """ Initialize a genome specifying a neural network. """
        self._id = self.__get_new_id()
        self._input_nodes  = NSGAConfig.input_nodes
        self._output_nodes = NSGAConfig.output_nodes

        self._connection_genes = {} # dictionary of connection genes
        self._node_genes = []

        self.fitness = None
        self.species_id = None

        # Parent ID's track the genomes geneaology
        self.parent1_id = parent1_id
        self.parent2_id = parent2_id

    conn_genes = property(lambda self: self._connection_genes.values())
    node_genes = property(lambda self: self._node_genes)
    num_inp    = property(lambda self: self._input_nodes)
    num_out    = property(lambda self: self._output_nodes)
    id         = property(lambda self: self._id)

    def __cmp__(self, other):
        """ Compare genomes by their fitness. """
        return cmp(self.fitness, other.fitness)

    def __str__(self):
        s = "GenomeStart "+str(self._id)
        for ng in self._node_genes:
            s += "\n" + str(ng)

        # Sort the connections by innovation number.
        connections = [[conn._innov_number,conn] for key,conn in self._connection_genes.iteritems()]

        for conn in sorted(connections):
            s += "\n" + str(conn[1])
        # for key,conn in self._connection_genes.iteritems():
        #     s += "\n" + str(conn)
        s += "\nGenomeEnd\n"
        return s

    def get_new_id(self):
        """ Get a new id for the genome. """
        self._id = NSGAGenome.__get_new_id()

    def build_phenotype(self):
        """ Gather the information needed to define the phenotype of the ANN.

        Interfaces with ANN2 neural network.

        Returns:
            num_inp,num_hid,num_out,c_src,c_trg,c_wts,wt_range
        """

        c_src = []
        c_trg = []
        c_wts = []

        for key, conn_gene in self._connection_genes.iteritems():
            if conn_gene.enabled:
                c_src.append(int(key[0]))
                c_trg.append(int(key[1]))
                c_wts.append(float(conn_gene.weight))

        # Build the remap list to go from NEAT-style node ids to Tony-style node ids (inp,out,hid) -> (inp,hid,out)
        remap_key = {}
        for node in self._node_genes:
            if node.node_type == "INPUT":
                remap_key[int(node.id)] = int(node.id) # No Change
            elif node.node_type == "HIDDEN":
                remap_key[int(node.id)] = int(node.id) - self._input_nodes + 1 # Adjust down by # of inputs
            else:
                remap_key[int(node.id)] = int(node.id) + (len(self._node_genes)-self._input_nodes-self._output_nodes) # Adjust up by number of hidden nodes.

        # Loop through src and trg lists and change keys as needed.        
        for i in range(len(c_src)):
            c_src[i] = remap_key[c_src[i]]
            c_trg[i] = remap_key[c_trg[i]]

        return int(self._input_nodes),int(len(self._node_genes)-self._input_nodes-self._output_nodes),int(self._output_nodes),\
            c_src,c_trg,c_wts,\
            float(NSGAConfig.max_weight-NSGAConfig.min_weight), [float(NSGAConfig.min_out_weight),float(NSGAConfig.max_out_weight)]

    def set_fitness(self, fit):
        """ Set the fitness of a genome. 

        Args:
            fit: fitness to set the genome at
        """
        self.fitness = fit

    def mutate(self):
        """ Mutates the genome by adding structure or mutatating the connection weights. """
        if random.random() < NSGAConfig.prob_addnode:
            self._mutate_add_node()
        elif random.random() < NSGAConfig.prob_addconn:
            self._mutate_add_connection()
        else:
            for cg in self._connection_genes.values():
                cg.mutate() # mutate weights

        return self

    def _mutate_add_node(self):
        """ Mutate a connection in the ANN. """
        conn_to_split = random.choice(self._connection_genes.values())
        ng = NodeGene(len(self._node_genes) + 1, 'HIDDEN')
        self._node_genes.append(ng)
        new_conn1, new_conn2 = conn_to_split.split(ng.id)
        self._connection_genes[new_conn1.key] = new_conn1
        self._connection_genes[new_conn2.key] = new_conn2
        return (ng, conn_to_split)

    def _mutate_add_connection(self):
        # Only for recurrent networks
        total_possible_conns = (len(self._node_genes) - self._input_nodes) \
            * len(self._node_genes)
        remaining_conns = total_possible_conns - len(self._connection_genes)
        # Check if new connection can be added:
        if remaining_conns > 0:
            n = random.randint(0, remaining_conns - 1)
            count = 0
            # Count connections
            for in_node in self._node_genes:
                for out_node in self._node_genes[self._input_nodes:]:
                    if (in_node.id, out_node.id) not in self._connection_genes.keys():
                        # Free connection
                        if count == n: # Connection to create
                            weight = float("{0:.4f}".format(random.gauss(0, NSGAConfig.weight_stdev)))
                            cg = ConnectionGene(in_node.id, out_node.id, weight, True)
                            self._connection_genes[cg.key] = cg
                            return
                        else:
                            count += 1

    def crossover(self, other):
        """ Crosses over parents' genomes and returns a child. """

        # Parents must be the same species for meaningful crossover.
        assert self.species_id == other.species_id, 'Different parents species ID: %d vs %d' \
                                                         % (self.species_id, other.species_id)

        if self.fitness > other.fitness:
            parent1 = self
            parent2 = other
        elif self.fitness == other.fitness:
            # Choose parents based on length.
            if len(self.conn_genes) < len(other.conn_genes):
                parent1 = self
                parent2 = other
            else:
                parent1 = other
                parent2 = self  
        else:
            parent1 = other
            parent2 = self

        # creates a new child
        child = self.__class__(self.id, other.id)

        child._inherit_genes(parent1, parent2)

        child.species_id = parent1.species_id

        return child

    def _inherit_genes(child, parent1, parent2):
        """ Applies the crossover operator. """
        assert(parent1.fitness >= parent2.fitness)

        # Crossover connection genes
        for cg1 in parent1._connection_genes.values():
            try:
                cg2 = parent2._connection_genes[cg1.key]
            except KeyError:
                # Copy excess or disjoint genes from the fittest parent
                child._connection_genes[cg1.key] = cg1.copy()
            else:
                if cg2.is_same_innov(cg1): # Always true for *global* INs
                    # Homologous gene found
                    new_gene = cg1.get_child(cg2)
                else:
                    new_gene = cg1.copy()
                child._connection_genes[new_gene.key] = new_gene

        # Crossover node genes
        for i, ng1 in enumerate(parent1._node_genes):
            try:
                # matching node genes: randomly selects the neuron's bias and response
                child._node_genes.append(ng1.get_child(parent2._node_genes[i]))
            except IndexError:
                # copies extra genes from the fittest parent
                child._node_genes.append(ng1.copy())

    def distance(self, other):
        """ Returns the distance between this genome and the other. """
        if len(self._connection_genes) > len(other._connection_genes):
            chromo1 = self
            chromo2 = other
        else:
            chromo1 = other
            chromo2 = self

        weight_diff = 0
        matching = 0
        disjoint = 0
        excess = 0

        max_cg_chromo2 = max(chromo2._connection_genes.values())

        for cg1 in chromo1._connection_genes.values():
            try:
                cg2 = chromo2._connection_genes[cg1.key]
            except KeyError:
                if cg1 > max_cg_chromo2:
                    excess += 1
                else:
                    disjoint += 1
            else:
                # Homologous genes
                weight_diff += math.fabs(cg1.weight - cg2.weight)
                matching += 1

        disjoint += len(chromo2._connection_genes) - matching

        distance = NSGAConfig.excess_coeficient * excess + \
                   NSGAConfig.disjoint_coeficient * disjoint
        if matching > 0:
            distance += NSGAConfig.weight_coeficient * (weight_diff/matching)

        return distance

    def size(self):
        """ Defines genome 'complexity': number of hidden nodes plus
            number of enabled connections (bias is not considered)
        """
        # number of hidden nodes
        num_hidden = len(self._node_genes) - self._input_nodes - self._output_nodes
        # number of enabled connections
        conns_enabled = sum([1 for cg in self._connection_genes.values() if cg.enabled is True])

        return (num_hidden, conns_enabled)

    def size_node_count(self):
        """ Defines the genome complexity in terms of the number of hidden nodes in the network. """

        return len(self._node_genes) - self._input_nodes - self._output_nodes

    def size_link_count(self):
        """ Defines the genome complexity in terms of the number of enabled connections in the network. """

        return sum([1 for cg in self._connection_genes.values() if cg.enabled is True])

    def add_hidden_nodes(self, num_hidden):
        """ Add a hidden node(s) to the network.

        Args:
            num_hidden: Number of hidden nodes to add.
        """
        id = len(self._node_genes)+1
        for i in range(num_hidden):
            node_gene = NodeGene(id, nodetype = 'HIDDEN')
            self._node_genes.append(node_gene)
            id += 1
            # Connect all nodes to it
            for pre in self._node_genes:
                weight = float("{0:.4f}".format(random.gauss(0, NSGAConfig.weight_stdev)))
                cg = ConnectionGene(pre.id, node_gene.id, weight, True)
                self._connection_genes[cg.key] = cg
            # Connect it to all nodes except input nodes
            for post in self._node_genes[self._input_nodes:]:
                weight = float("{0:.4f}".format(random.gauss(0, NSGAConfig.weight_stdev)))
                cg = ConnectionGene(node_gene.id, post.id, weight, True)
                self._connection_genes[cg.key] = cg

    def add_node_gene(self, node_id, node_type):
        """ Add a node gene to the genome.  Used when reading from file.

        Args:
            node_id: id of the node
            node_type: type of the node
        """
        self._node_genes.append(NodeGene(node_id,node_type))

    def add_connection_gene(self,innov_num, src_node, dst_node, weight, enabled):
        """ Add a connection gene to the ANN.  Used when reading genome from file.

        Args:
            innov_num: innovation number of the connection
            src_node: node ID of the source
            dst_node: node ID of the destination
            weight: weight of the connection
            enabled: whether or not the connection is enabled
        """
        new_cg = ConnectionGene(in_node=int(src_node), out_node=int(dst_node), weight=float(weight), enabled=(True if enabled == "True" else False), innov_number = int(innov_num))
        self._connection_genes[new_cg.key] = new_cg

    @classmethod
    def create_unconnected(cls):
        """
        Factory method
        Creates a genome for an unconnected feedforward network with no hidden nodes.
        """
        c = cls(0, 0)
        id = 0
        # Create node genes
        for i in range(NSGAConfig.input_nodes):
            c._node_genes.append(NodeGene(id, 'INPUT'))
            id += 1
        #c._input_nodes += num_input
        for i in range(NSGAConfig.output_nodes):
            node_gene = NodeGene(id, nodetype = 'OUTPUT')
            c._node_genes.append(node_gene)
            id += 1
        assert id == len(c._node_genes)
        return c

    @classmethod
    def create_fully_connected(cls):
        """
        Factory method
        Creates a genome for a fully connected feedforward network with no hidden nodes.
        """
        c = cls.create_unconnected()
        for node_gene in c.node_genes:
            if node_gene.node_type != 'OUTPUT': continue

            # Connect it to all input nodes
            for input_node in c._node_genes[:NSGAConfig.input_nodes]:
                weight = float("{0:.4f}".format(random.gauss(0, NSGAConfig.weight_stdev)))

                cg = ConnectionGene(input_node.id, node_gene.id, weight, True)
                c._connection_genes[cg.key] = cg

        return c

class NodeGene(object):
    """ Gene for the nodes in an ANN. """

    def __init__(self, id, nodetype):
        """ """
        self._id = id
        self._type = nodetype

        assert(self._type in ('INPUT', 'OUTPUT', 'HIDDEN'))

    id = property(lambda self: self._id)
    node_type = property(lambda self: self._type)

    def __str__(self):
        """ Return a string representation of the node. """
        return "Node "+str(self._id)+" "+str(self._type)

    def copy(self):
        """ Copy the NodeGene. """
        return NodeGene(self._id,self._type)

    def get_child(self, other):
        """ Create a child from two parents.

        Used during crossover.  

        NOTE: Not used here unless we implement other properties of nodes.

        Args:
            other: other parent NodeGene

        Returns a copy of either self or the other parent based on random choice.
        """
        assert(self._id == other._id)

        ng = NodeGene(self._id, self._type)

        return ng

class ConnectionGene(object):
    """ Gene for defining connections between nodes in an ANN. """
    __global_innovation_number = 0 # Unique number for each innovation in the ANNs
    __innovations = {} # Dictionary of innovations for a given generation (Avoids duplicates)

    @classmethod
    def reset_innovations(cls):
        """ Reset the dictionary of innovations.

        Use this after a new generation has been processed.
        """
        cls.__innovations = {}

    @classmethod
    def __get_new_innov_number(cls):
        cls.__global_innovation_number += 1
        return cls.__global_innovation_number

    def __init__(self, in_node, out_node, weight, enabled, innov_number = None):
        """ """
        self._in = in_node
        self._out = out_node
        self._weight = weight
        self._enabled = enabled

        if not innov_number:
            try:
                # Ensure that we don't already have an innovation for the connection.
                self._innov_number = self.__innovations[self.key] 
            except KeyError:
                # Create a new innovation
                self._innov_number = self.__get_new_innov_number()
                self.__innovations[self.key] = self._innov_number
        else:
            self._innov_number = innov_number

    weight = property(lambda self: float("{0:.4f}".format(self._weight)))
    in_node = property(lambda self: self._in)
    out_node = property(lambda self: self._out)
    enabled = property(lambda self: self._enabled)
    key = property(lambda self: (self._in, self._out))

    def __str__(self):
        """ Return a string representation of the connection. """
        return "Link "+str(self._innov_number)+" "+str(self._in)+" "+str(self._out)+" "+str(self._weight)+" "+str(self._enabled)

    def __cmp__(self, not_self):
        """ Compare two ConnectionGenes """
        return cmp(self._innov_number, not_self._innov_number)

    def is_same_innov(self, not_self):
        return self._innov_number == not_self._innov_number 

    def copy(self):
        return ConnectionGene(self._in, self._out, self._weight,
                              self._enabled, self._innov_number)

    def mutate(self):
        """ Mutate the parameters of the ConnectionGene based on configuration parameters. """
        if random.random() < NSGAConfig.prob_mutate_weight:
            if random.random() < NSGAConfig.prob_uni_mut_weight:
                # Replace the weight uniformly
                self.__uniform_replace_weight()
            else:
                self.__mutate_weight()

        if random.random() <  NSGAConfig.prob_togglelink:
            self.enable()

    def enable(self):
        """ Enables a link. """
        self._enabled = True

    def __mutate_weight(self):
        self._weight += float("{0:.4f}".format(random.gauss(0,1)*NSGAConfig.weight_mutation_power))

        if self._weight > NSGAConfig.max_weight:
            self._weight = float("{0:.4f}".format(NSGAConfig.max_weight))
        elif self._weight < NSGAConfig.min_weight:
            self._weight = float("{0:.4f}".format(NSGAConfig.min_weight))

    def __uniform_replace_weight(self):
        self._weight = float("{0:.4f}".format(random.uniform(NSGAConfig.min_weight, NSGAConfig.max_weight)))

    def split(self, node_id):
        """ Split the connection and create two new ones.  

        Used during the add node process.

        Args:
            node_id: newly created node id that will go between the split connection
        """
        self._enabled = False
        new_conn_1 = ConnectionGene(self._in, node_id, 1.0, True)
        new_conn_2 = ConnectionGene(node_id, self._out, self._weight, True)
        return new_conn_1, new_conn_2

    def get_child(self, not_self):
        """ Create a child from two parents with the same innovation number.

        Used during crossover.

        Args:
            not_self: other parent ConnectionGene

        Returns a copy of either self or the other parent based on random choice.
        """
        return random.choice((self,not_self)).copy()
