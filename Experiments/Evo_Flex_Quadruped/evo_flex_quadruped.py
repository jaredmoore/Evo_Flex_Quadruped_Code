"""
    Evolve a quadruped robot that contains an ANN Controller.  This is meant to be a complement to the
    ANN/Mus Model work so we can compare ANN statistics.
"""

import argparse
import sys, os, random, time
import itertools
import math
import numpy
import time

import evo_flex_quadruped_evol_utils
import flex_quadruped_utils

def getValIndGenomeStr(fit_file,gen,ind):
    """ Get the validator individual specified by the arguments.

    Args:
        fit_file: file to parse for the genome
        gen: generation to check against
        ind: individual from the generation

    Returns:
        string containing the genome of an individual.
    """
    with open(fit_file,"r") as f:
        genome_index = 0 # Where does the genome start?
        for line in f:
            spl_line = line.split(",")
            if genome_index == 0:
                for s in spl_line:
                    if "Fit" in s or "Gen" in s or "Ind" in s:
                        genome_index += 1
                    else:
                        break

            if spl_line[0] == str(gen) and spl_line[1] == str(ind):
                return ','.join(i for i in spl_line[genome_index:])
    print("Individual not found for Generation: "+str(gen)+" Individual: "+str(ind))
    exit()

######################################################################

# Process inputs.
parser = argparse.ArgumentParser()
parser.add_argument("--validator", action="store_true", help="Validate current results.")
parser.add_argument("--gens", type=int, default=100, help="Number of generations to run evolution for.")
parser.add_argument("--pop_size", type=int, default=100, help="Population size for evolution.")
parser.add_argument("--eval_time", type=float, default=10., help="Simulation time for an individual.")
parser.add_argument("--run_num", type=int, default=0, help="Run Number")
parser.add_argument("--output_path", type=str, default="./", help="Output path")
parser.add_argument("--log_frames",action="store_true",help="Save the frames to a folder.")
parser.add_argument("--debug_runtime",action="store_true",help="Evaluate the run time of a simulation.")
parser.add_argument("--no_periodic",action="store_true",help="Whether we're including a periodic signal or not.")
parser.add_argument("--val_ind",type=int, default=0, help="Individual to validate from a generation.")
parser.add_argument("--lexicase",action="store_true",help="Whether to do normal or Lexicase selection.")
parser.add_argument("--nsga",action="store_true",help="Are we doing NSGA-II?")
parser.add_argument("--exp_num",type=int, default=0, help="What experiment to run.")
parser.add_argument("--provide_genome",action="store_true", help="Provide a genome for validation.")
parser.add_argument("--genome",type=str,help="Genome to validate.")
args = parser.parse_args()

# Select the experiment to run.
quadruped_classes = [
    flex_quadruped_utils.ControlForceSliderFlexEvolve, # Add Sliders to the Base Experiment - 0
    flex_quadruped_utils.ControlForceEvolve, # Base Experiment - 1 (Sliders fixed movement springiness)
    flex_quadruped_utils.ControlForceSpineFlexEvolve, # Spine flexibility, stiff sliders - 2
    flex_quadruped_utils.ControlForceSpineSliderFlexEvolve, # Spine and sliders flexible - 3
    flex_quadruped_utils.ControlForceSpineFlexNoSlidersEvolve, # Spine Flex and No Sliders - 4
    flex_quadruped_utils.ControlForceNoSlidersEvolve, # Base Experiment with no sliders - 5
    flex_quadruped_utils.ControlForceHingeLowerEvolve, # Evolve hinge joints on the lower legs - 6
    flex_quadruped_utils.ControlForceSpineFlexHingeLowerEvolve, # Evolve hinge joints and spine flexibility - 7
    flex_quadruped_utils.ControlForceHingeLowerActiveSpineEvolve # Evolve hinge joints and an actively controlled spine - 8
]

# Set arguments for the evo_quadruped_evol_utils
evo_flex_quadruped_evol_utils.args = args

# Seed only the evolutionary runs.
random.seed(args.run_num)

if args.debug_runtime:
    print(evo_flex_quadruped_evol_utils.evaluate_individual(quadruped_classes[args.exp_num]()))
elif args.validator:
    genome_str = ""
    if not args.provide_genome:
        fit_file = args.output_path+"/"+str(args.run_num)+"_fitnesses.dat"
        genome_str = getValIndGenomeStr(fit_file,args.gens,args.val_ind)
        print(genome_str)
    else:genome_str
        # = raw_input("Enter Genome Please:")
        genome_str = args.genome
    print(args.exp_num,args.run_num,args.gen,args.val_ind,evo_flex_quadruped_evol_utils.evaluate_individual(quadruped_classes[args.exp_num](genome=genome_str)))
else:
    if args.nsga:
        evo_flex_quadruped_evol_utils.nsga_evolution_run(
            output_path=args.output_path,
            run_num=args.run_num,
            pop_size=args.pop_size,
            exp_class=quadruped_classes[args.exp_num]
        )
    else:
        evol_type = 'norm_ga'
        if args.lexicase:
            evol_type = 'lexicase'
        
        evo_flex_quadruped_evol_utils.common_evolution_run(
            evol_type=evol_type,
            output_path=args.output_path,
            run_num=args.run_num,
            pop_size=args.pop_size,
            exp_class=quadruped_classes[args.exp_num]
            )