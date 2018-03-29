""" Class to hold configuration parameters for the NEAT algorithm. """

class Config(object):

    # phenotype config
    input_nodes         = None
    output_nodes        = None
    hidden_nodes        = None
    fully_connected     = None
    max_weight          = None
    min_weight          = None
    feedforward         = None
    weight_stdev        = None
    min_out_weight      = None
    max_out_weight      = None

    # GA config
    pop_size                = None
    max_fitness_threshold   = None
    prob_addconn            = None
    prob_addnode            = None
    prob_mutatebias         = None
    bias_mutation_power     = None
    prob_mutate_weight      = None
    prob_uni_mut_weight     = None
    weight_mutation_power   = None
    prob_togglelink         = None
    elitism                 = None

    prob_crossover = None

    # genotype compatibility
    compatibility_threshold = None
    compatibility_change    = None
    excess_coeficient       = None
    disjoint_coeficient     = None
    weight_coeficient       = None

    # species
    species_size        = None
    survival_threshold  = None
    old_threshold       = None
    youth_threshold     = None
    old_penalty         = None    
    youth_boost         = None    
    max_stagnation      = None