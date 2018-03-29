""" File to encapsulate a quadruped individual for use in DEAP. 

I'm employing a composition pattern so BaseEvolve provides the interface to evolution while 
individual <Type>Components define the genome for particular instances of an individual.

"""

import math
import os
import random
import warnings

mutate_chance = 0.04

############################################################################################################
# Utility Methods

def format_float(value):
    """ Return a formatted float value capable of being printed. """
    return float("{0:.6f}".format(float(value)))


def mutate_value(value,low_lim,upp_lim):
    """ Mutate a value by a gaussian within the bounds.  

    Args:
        value: initial value of the parameter.
        upp_lim: upper limit of the parameter
        low_lim: lower limit of the parameter
    """
    value = format_float(random.gauss(value, (upp_lim-low_lim)*0.1)) # Mutate in the range of 10% SD of the value
    if(value > upp_lim):
        value = upp_lim
    elif(value < low_lim):
        value = low_lim
    return value


def initIndividual(ind_class):
    return ind_class()


def mutate(individual):
    """ Call the mutation method of the appropriate class. 

    Note: Wrapped to function with DEAP.
    """    
    individual.mutate(mut_prob=mutate_chance)

############################################################################################################
# Universal robot constants.

class UniversalConstants(object):
    _MAX_FORCE_LIMIT = 300
    _FORCE_MUT_RESOLUTION = 1
    _MAX_JOINT_VEL_LIMIT = 80000

    
############################################################################################################
# Individual Components of the Genome.

class ControlComponent(UniversalConstants):
    """ Parameters associated with the control of a quadruped. """
    _num_genes = 10

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        if genome=="":
            self.osc_freq = format_float(random.random()*2.0)
            self.limb_offsets = [
                format_float(random.randint(0,15)/8.), # Front Left Leg
                format_float(random.randint(0,15)/8.), # Front Right Leg
                format_float(random.randint(0,15)/8.), # Rear Left Leg
                format_float(random.randint(0,15)/8.), # Rear Right Leg
            ]
            self.joint_offsets = [
                format_float(random.randint(0,15)/8.), # Front Hips - 0 ---> 0
                format_float(random.randint(0,15)/8.), # Front Knee - 1 ---> 1
                format_float(random.randint(0,15)/8.), # Rear Hip - 3 ---> 2
                format_float(random.randint(0,15)/8.), # Rear Knee - 4 ---> 3 
            ]
            self.max_joint_vel = format_float(random.randint(20,(self._MAX_JOINT_VEL_LIMIT/1000))*1000.) #180000 -> Original value
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        robot.osc_freq = self.osc_freq
        robot.limb_offsets = self.limb_offsets

        for i, jo in enumerate(self.joint_offsets):
            robot.joint_offsets[i] = jo
        robot.max_joint_vel = self.max_joint_vel

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",Osc_Freq,FLL_Off,FRL_Off,RLL_Off,RRL_Off,FH_Off,FK_Off,RH_Off,RK_Off,Max_Joint_Vel"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str  = ','+str(self.osc_freq)+","+(','.join(str(i) for i in self.limb_offsets))+','+(','.join(str(i) for i in self.joint_offsets))
        out_str += ','+str(self.max_joint_vel)
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        self.osc_freq = float(genome[0])
        self.limb_offsets = [float(genome[i]) for i in range(1,5)]
        self.joint_offsets = [float(genome[i]) for i in range(5,9)]
        self.max_joint_vel = float(genome[9])

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        if random.random() < mut_prob:
            self.osc_freq = mutate_value(self.osc_freq,0.0,2.0)
            
        for i in range(len(self.limb_offsets)):
            if random.random() < mut_prob:
                self.limb_offsets[i] = float("{0:.6f}".format(round(mutate_value(self.limb_offsets[i],0.,15.))/8.))
        
        for i in range(len(self.joint_offsets)):
            if random.random() < mut_prob:
                self.joint_offsets[i] = float("{0:.6f}".format(round(mutate_value(self.joint_offsets[i],0.,15.))/8.))
        
        if random.random() < mut_prob:
            self.max_joint_vel = round(mutate_value(self.max_joint_vel,20,(self._MAX_JOINT_VEL_LIMIT/1000)))*1000. # TODO: Mutate in whole number steps instead?

class LowHingeControlComponent(UniversalConstants):
    """ Parameters associated with the control of the lowest limb hinges in a quadruped. 
        Only needs to add joint offsets as the others are evolved in control component.
    """
    _num_genes = 2

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        if genome=="":
            
            self.low_joint_offsets = [
                format_float(random.randint(0,15)/8.), # Front Ankle
                format_float(random.randint(0,15)/8.), # Rear Ankle
            ]
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        robot.joint_offsets[4] = self.low_joint_offsets[0]
        robot.joint_offsets[5] = self.low_joint_offsets[1]
        robot.make_hinge_lower()

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",FA_Off,RA_Off"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str  = ','+(','.join(str(i) for i in self.low_joint_offsets))
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        self.low_joint_offsets = [float(genome[i]) for i in range(0,2)]

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        for i in range(len(self.low_joint_offsets)):
            if random.random() < mut_prob:
                self.low_joint_offsets[i] = float("{0:.6f}".format(round(mutate_value(self.low_joint_offsets[i],0.,15.))/8.))

class ActiveSpineControlComponent(UniversalConstants):
    """ Parameters associated with the control of the spine in a quadruped when it is actively controlled. 
        Two genes for rear and front spine.
    """
    _num_genes = 2

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        if genome=="":
            
            self.spine_joint_offsets = [
                format_float(random.randint(0,15)/8.), # Rear Spine
                format_float(random.randint(0,15)/8.), # Front Spine
            ]
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        robot.spine_offsets[0] = self.spine_joint_offsets[0]
        robot.spine_offsets[1] = self.spine_joint_offsets[1]
        robot.make_actuated_spine()

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",RSp_Off,FSp_Off"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str  = ','+(','.join(str(i) for i in self.spine_joint_offsets))
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        self.spine_joint_offsets = [float(genome[i]) for i in range(0,2)]

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        for i in range(len(self.spine_joint_offsets)):
            if random.random() < mut_prob:
                self.spine_joint_offsets[i] = float("{0:.6f}".format(round(mutate_value(self.spine_joint_offsets[i],0.,15.))/8.))                

class ForcesComponent(UniversalConstants):
    """ Parameters associated with the maximum forces used to move the joints. """
    _num_genes = 10

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        if genome=="":
            self.max_forces = [
                [random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)]),random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)])], # Back Joints 
                [random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)]),random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)])], # Front Hip
                [random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)]),random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)])], # Rear Hip
                [random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)]),random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)])], # Front Knee
                [random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)]),random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)])], # Rear Knee
            ]
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        for i,mf in enumerate(self.max_forces):
            robot.max_forces[i] = mf
        
        # Removed to get rid of an index out of range error.
        #robot.max_forces = self.max_forces

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",BJ_MF_1,BJ_MF_2,FH_MF_1,FH_MF_2,RH_MF_1,RH_MF_2,FK_MF_1,FK_MF_2,RK_MF_1,"
        head_str += "RK_MF_2"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str = ','+','.join(str(i[0])+','+str(i[1]) for i in self.max_forces)
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        self.max_forces = [[int(float(genome[i])),int(float(genome[i+1]))] for i in range(0,len(genome),2)]

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        for i in range(len(self.max_forces)):
            for j in range(len(self.max_forces[i])):
                if random.random() < mut_prob:
                    self.max_forces[i][j] = round(mutate_value(self.max_forces[i][j],0,self._MAX_FORCE_LIMIT)) # TODO: Continue to mutate in steps of 20?

class LowerHingeForcesComponent(UniversalConstants):
    """ Parameters associated with the maximum forces used to move the joints. """
    _num_genes = 4

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        if genome=="":
            self.low_hinge_max_forces = [
                [random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)]),random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)])], # Front Ankle
                [random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)]),random.choice([i for i in range(0,self._MAX_FORCE_LIMIT,self._FORCE_MUT_RESOLUTION)])] # Rear Ankle
            ]
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        robot.max_forces[5] = self.low_hinge_max_forces[0]
        robot.max_forces[6] = self.low_hinge_max_forces[1]
        robot.make_hinge_lower()

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",FA_MF_1,FA_MF_2,RA_MF_1,RA_MF_2"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str = ','+','.join(str(i[0])+','+str(i[1]) for i in self.low_hinge_max_forces)
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        self.low_hinge_max_forces = [[int(float(genome[i])),int(float(genome[i+1]))] for i in range(0,len(genome),2)]

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        for i in range(len(self.low_hinge_max_forces)):
            for j in range(len(self.low_hinge_max_forces[i])):
                if random.random() < mut_prob:
                    self.low_hinge_max_forces[i][j] = round(mutate_value(self.low_hinge_max_forces[i][j],0,self._MAX_FORCE_LIMIT)) # TODO: Continue to mutate in steps of 20?

class JointRangeComponent(UniversalConstants):
    """ Parameters associated with the joint ranges of each leg. """
    _num_genes = 8

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        self.limits = [
            [math.radians(-90),math.radians(90)],  # Front Upper - 0
            [math.radians(-90),math.radians(90)],  # Rear Upper - 1
            [math.radians(-90),math.radians(90)],  # Front Mid - 2
            [math.radians(-90),math.radians(90)]  # Rear Mid - 3 
        ]

        if genome=="":
            self.joint_ranges = [
                [random.random() * self.limits[0][0],random.random() * self.limits[0][1]],  # Front Upper - 0
                [random.random() * self.limits[1][0],random.random() * self.limits[1][1]],  # Rear Upper - 1
                [random.random() * self.limits[2][0],random.random() * self.limits[2][1]],  # Front Mid - 2
                [random.random() * self.limits[3][0],random.random() * self.limits[3][1]]  # Rear Mid - 3
            ]
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        robot.joint_ranges[2][0] = self.joint_ranges[0]  # Front Upper
        robot.joint_ranges[3][0] = self.joint_ranges[1]  # Rear Upper
        robot.joint_ranges[4][0] = self.joint_ranges[2]  # Front Mid
        robot.joint_ranges[5][0] = self.joint_ranges[3]  # Rear Mid

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",FU_Low_Lim,FU_High_Lim,RU_Low_Lim,RU_High_Lim,FM_Low_Lim,FM_High_Lim,RM_Low_Lim,RM_High_Lim"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str  = ','+(','.join(str(i[0])+","+str(i[1]) for i in self.joint_ranges))
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        self.joint_ranges = [
            [float(genome[0]),float(genome[1])],  # Front Upper
            [float(genome[2]),float(genome[3])],  # Rear Upper
            [float(genome[4]),float(genome[5])],  # Front Mid
            [float(genome[6]),float(genome[7])]  # Rear Mid
        ]

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        if random.random() < mut_prob:
            for i in range(self.genome_length()):
                if i % 2 == 0:
                    self.joint_ranges[int(i/2)][0] = mutate_value(self.joint_ranges[int(i/2)][0],self.limits[int(i/2)][0],0)
                else:
                    self.joint_ranges[int(i/2)][1] = mutate_value(self.joint_ranges[int(i/2)][1],0,self.limits[int(i/2)][1])

class LowJointRangeComponent(UniversalConstants):
    """ Parameters associated with the joint ranges of each lower leg joint segment. 
        For use when replacing the sliders with the hinge.
    """
    _num_genes = 4

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        self.low_joint_limits = [
            [math.radians(-90),math.radians(90)],  # Front Lower - 0
            [math.radians(-90),math.radians(90)]   # Rear Lower - 1
        ]

        if genome=="":
            self.low_joint_ranges = [
                [random.random() * self.low_joint_limits[0][0],random.random() * self.low_joint_limits[0][1]],  # Front Lower - 0
                [random.random() * self.low_joint_limits[1][0],random.random() * self.low_joint_limits[1][1]]   # Rear Lower - 1
            ]
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        robot.joint_ranges[6][0] = self.low_joint_ranges[0]  # Front Lower
        robot.joint_ranges[7][0] = self.low_joint_ranges[1]  # Rear Lower

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",FL_Low_Lim,FL_High_Lim,RL_Low_Lim,RL_High_Lim"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str  = ','+(','.join(str(i[0])+","+str(i[1]) for i in self.low_joint_ranges))
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        self.low_joint_ranges = [
            [float(genome[0]),float(genome[1])],  # Front Lower
            [float(genome[2]),float(genome[3])]  # Rear Lower
        ]

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        if random.random() < mut_prob:
            for i in range(self.genome_length()):
                if i % 2 == 0:
                    self.low_joint_ranges[int(i/2)][0] = mutate_value(self.low_joint_ranges[int(i/2)][0],self.low_joint_limits[int(i/2)][0],0)
                else:
                    self.low_joint_ranges[int(i/2)][1] = mutate_value(self.low_joint_ranges[int(i/2)][1],0,self.low_joint_limits[int(i/2)][1])                    

class SpineJointRangeComponent(UniversalConstants):
    """ Parameters associated with the joint ranges of the two spine joints.  Both share the same value. """
    _num_genes = 4

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        self.limits = [
            [math.radians(-60),math.radians(60)],  # Spine
        ]

        if genome=="":
            self.spine_joint_ranges = [
                [random.random() * self.limits[0][0],random.random() * self.limits[0][1]],  # Spine Up/Down - 0
                [random.random() * self.limits[0][0],random.random() * self.limits[0][1]]  # Spine Side/Side - 1
            ]
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        robot.joint_ranges[0][0] = self.spine_joint_ranges[0]  # Spine Rear-Mid
        robot.joint_ranges[1][0] = self.spine_joint_ranges[0]  # Spine Mid-Front
        robot.joint_ranges[0][1] = self.spine_joint_ranges[1]  # Spine Rear-Mid
        robot.joint_ranges[1][1] = self.spine_joint_ranges[1]  # Spine Mid-Front

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",Sp_Vert_Low_Lim,Sp_Vert_Upp_Lim,Sp_Horiz_Low_Lim,Sp_Horiz_Upp_Lim"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str  = ','+(','.join(str(i[0])+","+str(i[1]) for i in self.spine_joint_ranges))
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        self.spine_joint_ranges = [
            [float(genome[0]),float(genome[1])],    # Spine Up/Down
            [float(genome[2]),float(genome[3])]     # Spine Side/Side
        ]

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        if random.random() < mut_prob:
            for i in range(self.genome_length()):
                if i % 2 == 0:
                    self.joint_ranges[int(i/2)][0] = mutate_value(self.spine_joint_ranges[int(i/2)][0],self.limits[int(i/2)][0],0)
                else:
                    self.joint_ranges[int(i/2)][1] = mutate_value(self.spine_joint_ranges[int(i/2)][1],0,self.limits[int(i/2)][1])                    

class SpineFlexibilityComponent(UniversalConstants):
    """ Parameters associated with the flexibility of the two spine joints.  Both share the same value. """
    _num_genes = 4

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        self.limits = [
            [0.4,1.0], # ERP
            [0.0001,0.15], # CFM
        ]

        if genome=="":
            self.spine_erp = [
                random.random() * (self.limits[0][1] - self.limits[0][0]) + self.limits[0][0], # Spine Up/Down
                random.random() * (self.limits[0][1] - self.limits[0][0]) + self.limits[0][0]  # Spine Side/Side
            ]

            self.spine_cfm = [
                random.random() * (self.limits[1][1] - self.limits[1][0]) + self.limits[1][0], # Spine Up/Down
                random.random() * (self.limits[1][1] - self.limits[1][0]) + self.limits[1][0]  # Spine Side/Side            ]
            ]
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        robot.erp[0][0] = self.spine_erp[0]  # Spine Up/Down
        robot.erp[0][1] = self.spine_erp[1]  # Spine Side/Side
        robot.cfm[0][0] = self.spine_cfm[0]  # Spine Up/Down
        robot.cfm[1][1] = self.spine_cfm[1]  # Spine Side/Side

        robot.flex_spine = True

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",Sp_Vert_ERP,Sp_Horiz_ERP,Sp_Vert_CFM,Sp_Horiz_CFM"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str  = ','+(','.join(str(i) for i in self.spine_erp))
        out_str  += ','+(','.join(str(i) for i in self.spine_cfm))
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        self.spine_erp = [float(genome[0]),float(genome[1])]
        self.spine_cfm = [float(genome[2]),float(genome[3])]

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        if random.random() < mut_prob:
            self.spine_erp[0] = mutate_value(self.spine_erp[0],self.limits[0][0],self.limits[0][1])
        
        if random.random() < mut_prob:
            self.spine_erp[1] = mutate_value(self.spine_erp[1],self.limits[0][0],self.limits[0][1])

        if random.random() < mut_prob:
            self.spine_cfm[0] = mutate_value(self.spine_cfm[0],self.limits[1][0],self.limits[1][1])
        
        if random.random() < mut_prob:
            self.spine_cfm[1] = mutate_value(self.spine_cfm[1],self.limits[1][0],self.limits[1][1])                                        

class JointSliderRangeComponent(UniversalConstants):
    """ Parameters associated with the range of the sliding joints on the lower limbs. """
    _num_genes = 2

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        # Can range from total sliding (length of component, to none.)
        self.limits = [
            -1.0,0.0,
        ]

        if genome=="":
            self.slider_ranges = [
                random.random() * self.limits[0],  # Front Slider
                random.random() * self.limits[0],  # Rear Slider
            ]
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        robot.slider_ranges[0] = self.slider_ranges[0] # Front Slider
        robot.slider_ranges[1] = self.slider_ranges[1] # Rear Slider

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",F_S_Low_Lim,R_S_Low_Lim"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str  = ','+(','.join(str(i[0])+","+str(i[1]) for i in self.slider_ranges))
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        self.slider_ranges = [
            float(genome[0]),  # Front Slider
            float(genome[1]),  # Rear Slider
        ]

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        if random.random() < mut_prob:
            for i in range(self.genome_length()):
                self.slider_ranges[i] = mutate_value(self.slider_ranges[i],self.limits[0],self.limits[1])                    

class JointSliderFlexibilityComponent(UniversalConstants):
    """ Parameters associated with the flexibility of the sliding joints. """
    _num_genes = 4

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        # Can range from total sliding (length of component, to none.)
        self.limits = [
            [0.5,1.0], # ERP
            [0.0001,0.15], # CFM
        ]

        if genome=="":
            self.slider_erp = [
                random.random() * (self.limits[0][1] - self.limits[0][0]) + self.limits[0][0], # Front Slider
                random.random() * (self.limits[0][1] - self.limits[0][0]) + self.limits[0][0]  # Rear Slider
            ]

            self.slider_cfm = [
                random.random() * (self.limits[1][1] - self.limits[1][0]) + self.limits[1][0], # Front Slider
                random.random() * (self.limits[1][1] - self.limits[1][0]) + self.limits[1][0]  # Rear Slider
            ]
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """

        robot.slider_erp[0] = self.slider_erp[0] # Front Slider
        robot.slider_erp[1] = self.slider_erp[1] # Rear Slider

        robot.slider_cfm[0] = self.slider_cfm[0] # Front Slider
        robot.slider_cfm[1] = self.slider_cfm[1] # Rear Slider

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",F_S_ERP,R_S_ERP,F_S_CFM,R_S_CFM"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str  = ','+str(self.slider_erp[0])+","+str(self.slider_erp[1])
        out_str  += ','+str(self.slider_cfm[0])+","+str(self.slider_cfm[1])
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        self.slider_erp = [
            float(genome[0]),  # Front Slider
            float(genome[1]),  # Rear Slider
        ]

        self.slider_cfm = [
            float(genome[2]),  # Front Slider
            float(genome[3]),  # Rear Slider
        ]

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        if random.random() < mut_prob:
            self.slider_erp[0] = mutate_value(self.slider_erp[0],self.limits[0][0],self.limits[0][1])
        
        if random.random() < mut_prob:
            self.slider_erp[1] = mutate_value(self.slider_erp[1],self.limits[0][0],self.limits[0][1])

        if random.random() < mut_prob:
            self.slider_cfm[0] = mutate_value(self.slider_cfm[0],self.limits[1][0],self.limits[1][1])
        
        if random.random() < mut_prob:
            self.slider_cfm[1] = mutate_value(self.slider_cfm[1],self.limits[1][0],self.limits[1][1])

class JointZOrientationComponent(UniversalConstants):
    """ Parameters associated with the initial rotation of the legs around the z axis. """
    _num_genes = 4

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        self.limits = [
            [-90,90],  # Front Upper Legs
            [-90,90],  # Rear Upper Legs
            [-90,90],  # Front Mid Legs
            [-90,90]   # Rear Mid Legs
        ]

        if genome=="":
            self.rotations = [
                random.randint(-90,90),  # Front Upper Legs
                random.randint(-90,90),  # Rear Upper Legs
                random.randint(-90,90),  # Front Mid Legs
                random.randint(-90,90)   # Rear Mid Legs
            ]
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        robot.body_rotations[0][1] = self.rotations[0] # Front Upper Legs
        robot.body_rotations[1][1] = self.rotations[1] # Rear Upper Legs
        robot.body_rotations[2][1] = self.rotations[2] # Front Mid Legs
        robot.body_rotations[3][1] = self.rotations[3] # Rear Mid Legs

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",FUL_IRot,RUL_IRot,FML_IRot,RML_IRot"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str  = ','+(','.join(str(i) for i in self.rotations))
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        self.rotations = [
            int(genome[0]), # Front Upper Legs
            int(genome[1]), # Rear Upper Legs
            int(genome[2]), # Front Mid Legs
            int(genome[3]), # Rear Mid Legs
        ]

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        if random.random() < mut_prob:
            for i in range(len(self.rotations)):
                self.rotations[i] = round(mutate_value(self.rotations[i],self.limits[i][0],self.limits[i][1]))

class LimbLengthComponent(UniversalConstants):
    """ Parameters associated with the length of the leg segments. """
    _num_genes = 6

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        if genome=="":
            self.lengths = [
                format_float(0.25+(random.random()*0.75)),  # Front Upper Legs
                format_float(0.25+(random.random()*0.75)),  # Rear Upper Legs
                format_float(0.25+(random.random()*0.75)),  # Front Mid Legs
                format_float(0.25+(random.random()*0.75)),  # Rear Mid Legs
                format_float(0.25+(random.random()*0.75)),  # Front Lower Legs
                format_float(0.25+(random.random()*0.75)),  # Rear Lower Legs
            ]
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        robot.body_dimensions[2][0] = self.lengths[0] # Front Upper Legs
        robot.body_dimensions[3][0] = self.lengths[1] # Rear Upper Legs
        robot.body_dimensions[4][0] = self.lengths[2] # Front Mid Legs
        robot.body_dimensions[5][0] = self.lengths[3] # Rear Mid Legs
        robot.body_dimensions[6][0] = self.lengths[4] # Front Lower Legs
        robot.body_dimensions[7][0] = self.lengths[5] # Rear Lower Legs

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",FUL_Len,RUL_Len,FML_Len,RML_Len,FLL_Len,RLL_Len"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str  = ','+(','.join(str(i) for i in self.lengths))
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')

        self.lengths = [
            format_float(genome[0]), # Front Upper Legs
            format_float(genome[1]), # Rear Upper Legs
            format_float(genome[2]), # Front Mid Legs
            format_float(genome[3]), # Rear Mid Legs
            format_float(genome[4]), # Front Lower Legs
            format_float(genome[5]), # Rear Lower Legs
        ]

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        if random.random() < mut_prob:
            for i in range(len(self.lengths)):
                self.lengths[i] = format_float(0.25+(random.random()*0.75))

class ShiftOscillatorComponent(UniversalConstants):
    """ Parameters associated with shifting the oscillating signal for driving locomotion. """
    _num_genes = 1

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        self.delta_lims = [-10.0,1.0]

        if genome=="":
            self.delta = format_float(self.delta_lims[0]+(random.random()*(self.delta_lims[1]-self.delta_lims[0])))
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        robot.delta = self.delta

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",Delta"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str  = ','+str(self.delta)
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        self.delta = format_float(genome[0])

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        if random.random() < mut_prob:
            self.delta = format_float(mutate_value(self.delta,self.delta_lims[0],self.delta_lims[1]))

class ShiftOscillatorPerJointComponent(UniversalConstants):
    """ Shift oscillation per joint. """
    _num_genes = 4

    def __init__(self,genome=""):
        """ Initialize the genome with a set of values. """

        self.delta_lims = [-10.0,1.0]
        self.deltas = [0,0,0,0,0,0]

        if genome=="":
            self.deltas = [
                format_float(self.delta_lims[0]+(random.random()*(self.delta_lims[1]-self.delta_lims[0]))), # Front Upper Legs
                format_float(self.delta_lims[0]+(random.random()*(self.delta_lims[1]-self.delta_lims[0]))), # Rear Upper Legs
                format_float(self.delta_lims[0]+(random.random()*(self.delta_lims[1]-self.delta_lims[0]))), # Front Mid Legs
                format_float(self.delta_lims[0]+(random.random()*(self.delta_lims[1]-self.delta_lims[0]))), # Rear Mid Legs
                #format_float(self.delta_lims[0]+(random.random()*(self.delta_lims[1]-self.delta_lims[0]))), # Front Lower Legs
                #format_float(self.delta_lims[0]+(random.random()*(self.delta_lims[1]-self.delta_lims[0]))), # Rear Lower Legs
            ]
        else:
            self.setGenomeValues(genome)

    def map_genome(self,robot):
        """ Map the genome values for the component to the robot object.

        Args:
            robot: Class containing the actual values that are passed to the simulation.
        """
        robot.deltas = self.deltas

    @classmethod
    def headers(cls):
        """ Return a comma separated string of the parameters associated with an individual. """
        head_str  = ",FHD,RHD,FKD,RKD"
        return head_str

    @classmethod
    def genome_length(cls):
        """ Return the number of genes in the class. """
        return cls._num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        out_str  = ','+(','.join(str(i) for i in self.deltas))
        return out_str

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """

        if type(genome) == str:
            genome = genome.split(',')
        for i in range(len(genome)):
            self.deltas[i] = format_float(genome[i])

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        for i in range(len(self.deltas)):
            if random.random() < mut_prob:
                self.deltas[i] = format_float(mutate_value(self.deltas[i],self.delta_lims[0],self.delta_lims[1]))

############################################################################################################

class BaseQuadrupedContainer(UniversalConstants):
    """ An abstract quadruped genome containing all configurable parameters. """
    _id = 0 # Global genome identifier

    @classmethod
    def __get_new_id(cls):
        cls._id += 1
        return cls._id

    def __init__(self,debug=False):
        """ Initialize a default configuration of the robot. """

        self._id = self.__get_new_id()

        # Control parameters
        self.osc_freq = 1.0
        self.limb_offsets = [
            0./8., # Right Rear Leg
            4./8., # Left Rear Leg
            0./8., # Right Front Leg
            0./8., # Left Front Leg
        ]
        self.joint_offsets = [
            0./8., # Front Hips - 0
            4./8., # Front Knee - 1
            0./8., # Rear Hip - 2
            0./8., # Rear Knee - 3 
            0./8., # Front Ankle - 4
            0./8., # Rear Ankle - 5
        ]

        self.spine_offsets = [
            0./8., # Rear Spine - 0
            0./8., # Front Spine - 1
        ]

        self.joint_ranges = [
            # Fore/Aft, Side-to-Side (Low,High)
            [[0,0],[0,0]],                                  # Spine Rear - Mid Connection - 0
            [[0,0],[0,0]],                                  # Spine Mid - Front Connection - 1
            [[math.radians(-90),math.radians(90)],[0,0]],   # Front Upper - 2
            [[math.radians(-90),math.radians(90)],[0,0]],   # Rear Upper - 3
            [[math.radians(-90),math.radians(90)],[0,0]],   # Front Mid - 4
            [[math.radians(-90),math.radians(90)],[0,0]],   # Rear Mid - 5
            [[math.radians(-90),math.radians(90)],[0,0]],   # Front Lower - 6
            [[math.radians(-90),math.radians(90)],[0,0]],   # Rear Lower - 7
        ]

        self.slider_ranges = [
            -0.15, # Front Slider
            -0.15  # Rear Slider
        ]        

        self.slider_erp = [0.8, 0.8] # Front Slider, Rear Slider
        self.slider_cfm = [0.1, 0.1] # Front Slider, Rear Slider

        # # For the control treatment, limit the slider movement.
        # self.stiff_slider = False

        self.max_forces = [
            [self._MAX_FORCE_LIMIT,self._MAX_FORCE_LIMIT], # Back - 0
            [self._MAX_FORCE_LIMIT,self._MAX_FORCE_LIMIT], # Front Upper - 1
            [self._MAX_FORCE_LIMIT,self._MAX_FORCE_LIMIT], # Rear Upper - 2
            [self._MAX_FORCE_LIMIT,self._MAX_FORCE_LIMIT], # Front Mid - 3
            [self._MAX_FORCE_LIMIT,self._MAX_FORCE_LIMIT], # Rear Mid - 4 
            [self._MAX_FORCE_LIMIT,self._MAX_FORCE_LIMIT], # Front Low - 5
            [self._MAX_FORCE_LIMIT,self._MAX_FORCE_LIMIT], # Rear Low - 6
        ]

        self.max_joint_vel = self._MAX_JOINT_VEL_LIMIT

        # Flexibility parameters
        self.erp = [
            [0.5,0.5], # Back 
            [0.5,0.5], # Front Upper
            [0.5,0.5], # Rear Upper
            [0.5,0.5], # Front Mid
            [0.5,0.5], # Rear Mid
            [0.5,0.5], # Front Lower
            [0.5,0.5], # Rear Lower
        ]

        self.cfm = [
            [0.0001,0.0001], # Back  
            [0.0001,0.0001], # Front Upper
            [0.0001,0.0001], # Rear Upper
            [0.0001,0.0001], # Front Mid
            [0.0001,0.0001], # Rear Mid
            [0.0001,0.0001], # Front Lower
            [0.0001,0.0001], # Rear Lower
        ]

        # Make stiff sliders to remove them from the robot.
        self.stiff_slider = False
        self.slider_erp = [
            0.5, # Front Slider
            0.5  # Rear Slider
        ]

        self.slider_cfm = [
            0.0001, # Front Slider
            0.0001  # Rear Slider
        ]

        # Make the lowers into hinge joints.
        self.hinge_lower = False

        # Make a flexible spine
        self.flex_spine = False

        # Make an actuated spine
        self.actuated_spine = False

        # Original Masses from ECAL 2013 Work
        self.body_masses = [
            10./3., # Rear Torso Segment  -  0
            10./3., # Mid Torso Segment   -  1
            10./3., # Front Torso Segment -  2
            2.0,    # Front Upper Legs    -  3
            2.0,    # Rear Upper Legs     -  4
            1.0,    # Front Mid Legs      -  5
            1.0,    # Rear Mid Legs       -  6
            0.5,    # Front Lower Legs    -  7
            0.5,    # Rear Lower Legs     -  8
        ]

        # Base the simple dimensions off a base factor for scaling.
        self.bf = 1.0
        self.body_dimensions = [
            [1.0*self.bf,.5*self.bf,1.25*self.bf], # Torso Rear segment      - 0
            [1.0*self.bf,.5*self.bf,1.25*self.bf], # Torso Mid segment       - 1
            [1.0*self.bf,.5*self.bf,1.25*self.bf], # Torso Front segment     - 1
            [0.5*self.bf,0.1*self.bf], # Front Upper Legs (Length, Radius)  - 2
            [0.5*self.bf,0.1*self.bf], # Rear Upper Legs (Length, Radius)   - 3
            [0.75*self.bf,0.05*self.bf], # Front Mid Legs (Length, Radius)   - 4
            [0.75*self.bf,0.05*self.bf], # Rear Mid Legs (Length, Radius)    - 5
            [0.25*self.bf,0.1*self.bf], # Front Low Legs (Length, Radius)   - 6
            [0.25*self.bf,0.1*self.bf], # Rear Low Legs (Length, Radius)    - 7
        ]

        self.body_rotations = [
            [90,0,0],      # Front Upper Legs
            [90,0,0],     # Rear Upper Legs
            [0,0,0],      # Front Mid Legs
            [0,0,0],       # Rear Mid Legs
            [0,0,0],   # Front Lower Legs
            [0,0,0],    # Rear Lower Legs
        ]

    id = property(lambda self: self._id)

    def get_new_id(self):
        """ Get a new id for the genome. """
        self._id = BaseQuadrupedContainer.__get_new_id()

    def make_stiff_slider(self):
        """ Make the slider joints stiff. """
        self.stiff_slider = True
        self.slider_ranges = [
            0.0, # Front Slider
            0.0  # Rear Slider
        ]
        self.slider_erp = [0.99, 0.99] # Front Slider, Rear Slider
        self.slider_cfm = [0.001, 0.001] # Front Slider, Rear Slider

    def make_hinge_lower(self):
        """ Make the lower joints a hinge. """
        self.hinge_lower = True

    def make_actuated_spine(self):
        """ Make the spine actuated. """
        self.actuated_spine = True
        self.joint_ranges[0] = [[math.radians(-45),math.radians(45)],[0,0]] # Spine Rear - Mid Connection - 0
        self.joint_ranges[1] = [[math.radians(-45),math.radians(45)],[0,0]] # Spine Mid - Front Connection - 1

class BaseEvolve(BaseQuadrupedContainer):
    """ Base class to provide a set of methods that work on individual genomic components. """

    def __init__(self,components=[],genome=""):
        """ Initialize the class with a list of components in the genome. 

        Args:
            components: list of genomic components
            genome: if validating use the genome
        """
        # Ensure that components is a list and not a single object.
        assert isinstance(components,list), "The genome components are not a list."

        super(BaseEvolve,self).__init__()

        self.components = []
        if genome:
            genome = genome.split(",")
            offsets = [0]
            for c in components:
                offsets.append(c.genome_length()+offsets[-1])
                self.components.append(c(genome=genome[offsets[-2]:offsets[-1]]))
        else:
            for c in components:
                self.components.append(c())

        # Get the number of genes in the genome.
        self.__num_genes = sum(c.genome_length() for c in self.components)

        self.map_genome()

    def map_genome(self):
        """ Map the genome values to the robot itself. """
        for c in self.components:
            c.map_genome(self)

    def __eq__(self,other):
        """ Override the equality operator. """
        return True if self.serialize() == other.serialize() else False

    def headers(self):
        """ Return a comma separated string of the parameters associated with an individual. """
        h = ""
        for c in self.components:
            h += c.headers()
        h = h[1:] # Remove the first comma.
        return h

    def genome_length(self):
        """ Return the number of genes in the class. """
        return self.__num_genes

    def __str__(self):
        """ Define the to string method for the class. """
        s = ""
        for c in self.components:
            s += str(c)
        s = s[1:] # Remove the first comma.
        return s        

    def serialize(self):
        """ Return a list representation of the genome for crossover. """
        return [float(i) for i in (str(self)).split(',')]

    def deserialize(self,genome):
        """ Set the genome to values provided in the genome. """
        self.setGenomeValues(genome)

    def setGenomeValues(self,genome):
        """ Set the genome values associated with an individual. 

        Args:
            genome: string containing the various genome parameters.
        """
        if type(genome) == str:
            genome = genome.split(',')

        offset = 0
        for c in self.components:
            c.setGenomeValues(genome[offset:offset+c.genome_length()])
            offset += c.genome_length()

        self.map_genome()

    def mutate(self, mut_prob=0.04):
        """ Mutate an individual. 

        Args:
            mut_prob: mutation probability per element in the genome.
        """

        for c in self.components:
            c.mutate(mut_prob=mut_prob)

        # Map the values back to the robot.
        self.map_genome()

class ControlForceEvolve(BaseEvolve):
    """ Evolve the control and force parameters associated with an individual. """

    def __init__(self,genome=""):
        # Split the genome up as needed to validate.
        components = [ControlComponent, ForcesComponent]

        super(ControlForceEvolve,self).__init__(components=components,genome=genome)

class ControlForceNoSlidersEvolve(BaseEvolve):
    """ Evolve the control and force parameters associated with an individual. """

    def __init__(self,genome=""):
        # Split the genome up as needed to validate.
        components = [ControlComponent, ForcesComponent]

        super(ControlForceNoSlidersEvolve,self).__init__(components=components,genome=genome)        

        self.make_stiff_slider()

        self.map_genome()

class ControlForceSliderFlexEvolve(BaseEvolve):
    """ Evolve the control and force parameters associated with an individual. Evolve just the slider flexibility. """

    def __init__(self,genome=""):
        # Split the genome up as needed to validate.
        components = [ControlComponent, ForcesComponent, JointSliderFlexibilityComponent]

        super(ControlForceSliderFlexEvolve,self).__init__(components=components,genome=genome)        

class ControlForceSpineFlexEvolve(BaseEvolve):
    """ Evolve the control and force parameters associated with an individual. """

    def __init__(self,genome=""):
        # Split the genome up as needed to validate.
        components = [ControlComponent, ForcesComponent, SpineFlexibilityComponent]

        super(ControlForceSpineFlexEvolve,self).__init__(components=components,genome=genome)

class ControlForceSpineFlexNoSlidersEvolve(BaseEvolve):
    """ Evolve the control and force parameters associated with an individual. """

    def __init__(self,genome=""):
        # Split the genome up as needed to validate.
        components = [ControlComponent, ForcesComponent, SpineFlexibilityComponent]

        super(ControlForceSpineFlexNoSlidersEvolve,self).__init__(components=components,genome=genome)

        self.make_stiff_slider()

        self.map_genome()

class ControlForceSpineSliderFlexEvolve(BaseEvolve):
    """ Evolve the control and force parameters associated with an individual. """

    def __init__(self,genome=""):
        # Split the genome up as needed to validate.
        components = [ControlComponent, ForcesComponent, SpineFlexibilityComponent, JointSliderFlexibilityComponent]

        super(ControlForceSpineSliderFlexEvolve,self).__init__(components=components,genome=genome)

class ControlForceHingeLowerEvolve(BaseEvolve):
    """ Evolve the control and force parameters associated with an individual. """

    def __init__(self,genome=""):
        # Split the genome up as needed to validate.
        components = [ControlComponent, ForcesComponent, LowerHingeForcesComponent, LowHingeControlComponent]

        super(ControlForceHingeLowerEvolve,self).__init__(components=components,genome=genome)

        # TODO: Add call to hinge lower
        self.make_hinge_lower()

        self.map_genome()

class ControlForceSpineFlexHingeLowerEvolve(BaseEvolve):
    """ Evolve the control and force parameters associated with an individual. """

    def __init__(self,genome=""):
        # Split the genome up as needed to validate.
        components = [ControlComponent, ForcesComponent, SpineFlexibilityComponent, LowerHingeForcesComponent, LowHingeControlComponent]

        super(ControlForceSpineFlexHingeLowerEvolve,self).__init__(components=components,genome=genome)

        # TODO: Add call to hinge lower
        self.make_hinge_lower()

        self.map_genome()

class ControlForceHingeLowerActiveSpineEvolve(BaseEvolve):
    """ Evolve the control and force parameters associated with an individual. """

    def __init__(self,genome=""):
        # Split the genome up as needed to validate.
        components = [ControlComponent, ForcesComponent, LowerHingeForcesComponent, LowHingeControlComponent, ActiveSpineControlComponent]

        super(ControlForceHingeLowerActiveSpineEvolve,self).__init__(components=components,genome=genome)

        # TODO: Add call to hinge lower
        self.make_hinge_lower()

        # Make the spine actively controlled
        self.make_actuated_spine()

        self.map_genome()        