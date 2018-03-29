"""
    Wrapper to conduct the actual simulation of a quadruped robot.  Access through methods: 
    evaluate individual, and physics only validation.
"""

import sys, os, random
import itertools
import math

sys.path.insert(0, '../../')

from Analysis import MOIAnalysis, COMEvaluation

from ODESystem import ODEManager
from ODESystem import Placement

from Robot import Sensors, TouchComponent

import ode

# Global constants for the simulation parameters.
eval_time = 10
file_prefix = ""
log_frames = False
run_num = 101
output_path = ""

##########################################################################################

def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step
        
def shift_oscillator(t,freq,d,phase_shift):
    """ Implement the shifted oscillator from the paper:
        "An Improved Evolvable Oscillator and Basis Function Set for 
        Control of an Insect-Scale Flapping-Wing Micro Air Vehicle"
        
        Args:
            freq: Oscillation frequency
            d: parameter determining how the wave will be skewed. (-12.0 to 1.0 acceptable.)
            phase_shift: percentage to shift the phase by.
    """
    
    # Adjust t to fall within the bounds of the oscillation frequency.
    t = t + (1.0/freq) * phase_shift
    t = t -(int(t/(1.0/freq))*1.0/freq)
    
    omega = 2.0*math.pi*freq

    # delta is the frequency offset that deines how much the upstroke phase is 
    # impeded or advanced
    delta = d*3.0*freq

    # rho and xi characterize a downstroke consisten with the split-cycle philosophy
    rho = delta * omega / (omega - 2.0*delta)
    xi = -2.0*math.pi*delta / (omega - 2.0*delta)
    xiS = 0.0

    thalfU = 1.0/(omega - delta)*2.0*math.pi/2.0
    thalfD = 1.0/(omega + rho)*2.0*math.pi/2.0

    if t < thalfU:
        return math.cos((omega - delta)*t)
    else:
        return math.cos((omega + rho)*t + xi)

##########################################################################################

def evaluate_individual(individual):
    """ Wrapper to call Simulation which will evaluate an individual.  

    Args:
        individual: arguments to pass to the simulation
        file_prefix: prefix for output files if validating

    Returns:
        fitness of an individual
    """

    simulation = Simulation(log_frames=log_frames, 
        run_num=run_num, 
        eval_time=eval_time, dt=.02, n=4,
        file_prefix=file_prefix)
    return simulation.evaluate_individual(individual)

##########################################################################################

man = 0
quadruped = 0

# For tracking toe touching over time.
num_touches = 0
touch_logging = [] # For keeping track of when a toe touch is persistent or new.

class Quadruped(object):
    """ Represent the quadruped robot. """

    def __init__(self,man,genome,base_pos=[0,0,0],logging=False):
        """ Initialize the robot in the ODE environment. 

        Arguments:
            man: ODE Manager for the Physics Simulation
            base_pos: base position to start the robot from
            morphology_genome: dict of dicts which contain different parameters for the morphology (TODO)
        """
        self.man = man
        self.body_keys = []

        self.joint_feedback_range = [0,14] # What joints do we want feedback on? Includes flexible sliders.
        # Deprecate joint_feedback_range in favor of joint_feedback_joints
        self.joint_feedback_joints = [] # Keep track of what actively controlled joints we monitor for force output.

        # Flexible Spine
        self.flex_spine = False

        # Lowe Hinge
        self.low_hinge = False

        # Sensors for robot.
        self.sensor = Sensors(man,logging=logging,log_path=output_path)
        self.sensor_components = {'touch':TouchComponent(man,logging=logging,log_path=output_path)}

        # Hardware Limits
        self.ref_moi_pivot = ""

        # Initialize the robot.
        self.__create_robot(genome,base_pos=base_pos)

    def __create_robot(self,genome,base_pos=[0,0,0]):
        """ Create the robot used in the experiment. 

        Arguments:
            base_pos: base position to start the robot from
            morphology: optional dict of dicts defining measurements for various parts of the robot.
        """
        global touch_logging

        self.flex_spine = genome.flex_spine

        self.low_hinge = genome.hinge_lower

        # Joint Power
        BACK_FORCE =  genome.max_forces[0]
        F_UPP_FORCE = genome.max_forces[1]
        R_UPP_FORCE = genome.max_forces[2]
        F_MID_FORCE = genome.max_forces[3]
        R_MID_FORCE = genome.max_forces[4]
        F_LOW_FORCE = 0
        R_LOW_FORCE = 0

        if self.low_hinge:
            F_LOW_FORCE = genome.max_forces[5]
            R_LOW_FORCE = genome.max_forces[6]

        # Flexibility for the joints.
        ERP = genome.erp

        CFM = genome.cfm

        joint_ranges = genome.joint_ranges

        # Verify that the joint ranges are greater than 10 degrees for the legs, 
        # otherwise set that one to 0 range of motion.
        for i in range(2,len(joint_ranges)):
            if (joint_ranges[i][0][1]-joint_ranges[i][0][0]) < 15.0*(math.pi/180.):
                joint_ranges[i][0][0] = 0.0
                joint_ranges[i][0][1] = 0.0

        #height = 3.0*genome.bf # Scale up by the genome base factor.
        height_front = genome.bf * (genome.body_dimensions[1][2]/2.0 + genome.body_dimensions[3][0] + genome.body_dimensions[5][0] + genome.body_dimensions[7][0])
        height_rear = genome.bf * (genome.body_dimensions[1][2]/2.0 + genome.body_dimensions[4][0] + genome.body_dimensions[6][0] + genome.body_dimensions[8][0])
        height = height_front + 0.01 if height_front >= height_rear else height_rear + 0.01

        # Torso body dimensions
        body_seg_dims = genome.body_dimensions[0:3]

        # Store mid torso dimensions for flipped checking.
        self.main_body_dimensions = [i for i in body_seg_dims[1]]

        # Torso body positions
        body_seg_pos = [
            [-body_seg_dims[1][0]/2.-body_seg_dims[0][0]/2.,height,0.], # Rear Segment
            [0,height,0.], # Mid Segment
            [body_seg_dims[1][0]/2.+body_seg_dims[2][0]/2.,height,0.]  # Front Segment
        ]

        # Leg Dimensions 
        leg_dims = genome.body_dimensions[3:]

        # Leg Rotations
        leg_rotations = [
            genome.body_rotations[0], # Front Upper Legs
            genome.body_rotations[1], # Rear Upper Legs
            genome.body_rotations[2], # Front Mid Legs
            genome.body_rotations[3], # Rear Mid Legs
            0, # genome.body_rotations[4], # Front Lower Legs
            0, # genome.body_rotations[5], # Rear Lower Legs
        ]

        # Slider joint limits
        slider_ranges = genome.slider_ranges

        # Prevent jittering with very small sliders.
        low_slider = [
            slider_ranges[0] if slider_ranges[0] < -0.03 else 0.0, # Front Slider
            slider_ranges[1] if slider_ranges[1] < -0.03 else 0.0 # Rear Slider
            ]
        high_slider = 0.01

        # Slider joint erp and cfm.
        slider_erp = genome.slider_erp # Front Slider, Rear Slider
        slider_cfm = genome.slider_cfm # Front Slider, Rear Slider 

        # Masses of the segments.
        body_masses = genome.body_masses

        # Body segement and upper leg joint positions
        fudge_factor = 0.0001 # Put the legs slightly outside the body, helps with stability.
        body_seg_joint_pos = [
            [-body_seg_dims[1][0]/2.,height,0.], # Spine Rear - Mid Connection
            [body_seg_dims[1][0]/2.,height,0.],  # Spine Mid - Front Connection
            [body_seg_pos[2][0]+body_seg_dims[2][0]/4., height, -body_seg_dims[2][2]/2.-leg_dims[0][1]-fudge_factor], # Front Upper Left Leg
            [body_seg_pos[2][0]+body_seg_dims[2][0]/4., height,  body_seg_dims[2][2]/2.+leg_dims[0][1]+fudge_factor], # Front Upper Right Leg
            [body_seg_pos[0][0]-body_seg_dims[0][0]/4., height, -body_seg_dims[0][2]/2.-leg_dims[1][1]-fudge_factor], # Rear Upper Left Leg
            [body_seg_pos[0][0]-body_seg_dims[0][0]/4., height,  body_seg_dims[0][2]/2.+leg_dims[1][1]+fudge_factor], # Rear Upper Right Leg
        ]

        # Set the reference point for the MOI pivot.
        # (Relative to the body used as the pivot point!)
        self.ref_moi_pivot = [0.,0.,0.]

        # Main Body (3 sections
        self.man.create_box(0,body_seg_dims[0],body_seg_pos[0],density=body_masses[0],mass_flag=True) # Rear Segment
        self.man.create_box(1,body_seg_dims[1],body_seg_pos[1],density=body_masses[1],mass_flag=True) # Mid Segment
        self.man.create_box(2,body_seg_dims[2],body_seg_pos[2],density=body_masses[2],mass_flag=True) # Front Segment

        # Determine if they are stiff spine joints or flexible.
        if not self.flex_spine:
            self.man.create_universal(0,body_seg_joint_pos[0],[0,1],axis1=[0,0,1],axis2=[0,1,0],loStop1=joint_ranges[0][0][0],hiStop1=joint_ranges[0][0][1],loStop2=joint_ranges[0][1][0],hiStop2=joint_ranges[0][1][1],fmax=BACK_FORCE[0],fmax2=BACK_FORCE[1])
            self.man.create_universal(1,body_seg_joint_pos[1],[1,2],axis1=[0,0,1],axis2=[0,1,0],loStop1=joint_ranges[1][0][0],hiStop1=joint_ranges[1][0][1],loStop2=joint_ranges[1][1][0],hiStop2=joint_ranges[1][1][1],fmax=BACK_FORCE[0],fmax2=BACK_FORCE[1])
            # Log the spine if it is actively actuated.
            if joint_ranges[0][0][0] < -30:
                self.joint_feedback_joints.append(0)
                self.joint_feedback_joints.append(1)
        else:
            self.man.create_flexible_universal(0, body_seg_joint_pos[0],[0,1],axis1=[0,0,1],axis2=[0,1,0],loStop1=joint_ranges[0][0][0],hiStop1=joint_ranges[0][0][1],loStop2=joint_ranges[0][1][0],hiStop2=joint_ranges[0][1][1],fmax=BACK_FORCE[0],fmax2=BACK_FORCE[1],erp1=ERP[0][0],erp2=ERP[0][1],cfm1=CFM[0][0],cfm2=CFM[0][1])    
            self.man.create_flexible_universal(1, body_seg_joint_pos[1],[1,2],axis1=[0,0,1],axis2=[0,1,0],loStop1=joint_ranges[1][0][0],hiStop1=joint_ranges[1][0][1],loStop2=joint_ranges[1][1][0],hiStop2=joint_ranges[1][1][1],fmax=BACK_FORCE[0],fmax2=BACK_FORCE[1],erp1=ERP[0][0],erp2=ERP[0][1],cfm1=CFM[0][0],cfm2=CFM[0][1])    

        # Front Upper Legs
        self.man.create_capsule(3, body_masses[3], leg_dims[0][0], leg_dims[0][1],[0,0,0],rot=[0.,0.,0.],mass_flag=True)
        Placement.place_capsule_at_trans(self.man.bodies[3],pos=body_seg_joint_pos[2],rot=leg_rotations[0])
        self.man.create_flexible_universal(2, body_seg_joint_pos[2],[2,3],axis1=[1,0,0],axis2=[0,0,1],loStop1=joint_ranges[2][1][0],hiStop1=joint_ranges[2][1][1],loStop2=joint_ranges[2][0][0],hiStop2=joint_ranges[2][0][1],fmax=F_UPP_FORCE[0],fmax2=F_UPP_FORCE[1],erp1=ERP[1][0],erp2=ERP[1][1],cfm1=CFM[1][0],cfm2=CFM[1][1])
        self.joint_feedback_joints.append(2)
        self.man.create_capsule(4, body_masses[3], leg_dims[0][0], leg_dims[0][1],[0,0,0],rot=[0.,0.,0.],mass_flag=True)
        Placement.place_capsule_at_trans(self.man.bodies[4],pos=body_seg_joint_pos[3],rot=leg_rotations[0])
        self.man.create_flexible_universal(3, body_seg_joint_pos[3],[2,4],axis1=[1,0,0],axis2=[0,0,1],loStop1=joint_ranges[2][1][0],hiStop1=joint_ranges[2][1][1],loStop2=joint_ranges[2][0][0],hiStop2=joint_ranges[2][0][1],fmax=F_UPP_FORCE[0],fmax2=F_UPP_FORCE[1],erp1=ERP[1][0],erp2=ERP[1][1],cfm1=CFM[1][0],cfm2=CFM[1][1])
        self.joint_feedback_joints.append(3)

        # Rear Upper Legs
        self.man.create_capsule(5, body_masses[4], leg_dims[1][0], leg_dims[1][1],[0,0,0],rot=[0.,0.,0.],mass_flag=True)
        Placement.place_capsule_at_trans(self.man.bodies[5],pos=body_seg_joint_pos[4],rot=leg_rotations[1])
        self.man.create_flexible_universal(4, body_seg_joint_pos[4],[0,5],axis1=[1,0,0],axis2=[0,0,1],loStop1=joint_ranges[3][1][0],hiStop1=joint_ranges[3][1][1],loStop2=joint_ranges[3][0][0],hiStop2=joint_ranges[3][0][1],fmax=R_UPP_FORCE[0],fmax2=R_UPP_FORCE[1],erp1=ERP[2][0],erp2=ERP[2][1],cfm1=CFM[2][0],cfm2=CFM[2][1])
        self.joint_feedback_joints.append(4)
        self.man.create_capsule(6, body_masses[4], leg_dims[1][0], leg_dims[1][1],[0,0,0],rot=[0.,0.,0.],mass_flag=True)
        Placement.place_capsule_at_trans(self.man.bodies[6],pos=body_seg_joint_pos[5],rot=leg_rotations[1])
        self.man.create_flexible_universal(5, body_seg_joint_pos[5],[0,6],axis1=[1,0,0],axis2=[0,0,1],loStop1=joint_ranges[3][1][0],hiStop1=joint_ranges[3][1][1],loStop2=joint_ranges[3][0][0],hiStop2=joint_ranges[3][0][1],fmax=R_UPP_FORCE[0],fmax2=R_UPP_FORCE[1],erp1=ERP[2][0],erp2=ERP[2][1],cfm1=CFM[2][0],cfm2=CFM[2][1])
        self.joint_feedback_joints.append(5)

        # Front Mid Legs
        self.man.create_capsule(7, body_masses[5], leg_dims[2][0], leg_dims[2][1],[0,0,0],rot=[0.,0.,0.],mass_flag=True)
        j_loc = Placement.place_capsule_trans(self.man.bodies[3],self.man.bodies[7],rot=leg_rotations[2]) 
        self.man.create_flexible_universal(6, j_loc,[3,7],axis1=[1,0,0],axis2=[0,0,1],loStop1=joint_ranges[4][1][0],hiStop1=joint_ranges[4][1][1],loStop2=joint_ranges[4][0][0],hiStop2=joint_ranges[4][0][1],fmax=F_MID_FORCE[0],fmax2=F_MID_FORCE[1],erp1=ERP[3][0],erp2=ERP[3][1],cfm1=CFM[3][0],cfm2=CFM[3][1])
        self.joint_feedback_joints.append(6)
        self.man.create_capsule(8, body_masses[5], leg_dims[2][0], leg_dims[2][1],[0,0,0],rot=[0.,0.,0.],mass_flag=True)
        j_loc = Placement.place_capsule_trans(self.man.bodies[4],self.man.bodies[8],rot=leg_rotations[2]) 
        self.man.create_flexible_universal(7, j_loc,[4,8],axis1=[1,0,0],axis2=[0,0,1],loStop1=joint_ranges[4][1][0],hiStop1=joint_ranges[4][1][1],loStop2=joint_ranges[4][0][0],hiStop2=joint_ranges[4][0][1],fmax=F_MID_FORCE[0],fmax2=F_MID_FORCE[1],erp1=ERP[3][0],erp2=ERP[3][1],cfm1=CFM[3][0],cfm2=CFM[3][1])
        self.joint_feedback_joints.append(7)

        # Rear Mid Legs
        self.man.create_capsule(9, body_masses[6], leg_dims[3][0], leg_dims[3][1],[0,0,0],rot=[0.,0.,0.],mass_flag=True)
        j_loc = Placement.place_capsule_trans(self.man.bodies[5],self.man.bodies[9],rot=leg_rotations[3]) 
        self.man.create_flexible_universal(8, j_loc,[5,9],axis1=[1,0,0],axis2=[0,0,1],loStop1=joint_ranges[5][1][0],hiStop1=joint_ranges[5][1][1],loStop2=joint_ranges[5][0][0],hiStop2=joint_ranges[5][0][1],fmax=R_MID_FORCE[0],fmax2=R_MID_FORCE[1],erp1=ERP[4][0],erp2=ERP[4][1],cfm1=CFM[4][0],cfm2=CFM[4][1])
        self.joint_feedback_joints.append(8)
        self.man.create_capsule(10, body_masses[6], leg_dims[3][0], leg_dims[3][1],[0,0,0],rot=[0.,0.,0.],mass_flag=True)
        j_loc = Placement.place_capsule_trans(self.man.bodies[6],self.man.bodies[10],rot=leg_rotations[3]) 
        self.man.create_flexible_universal(9, j_loc,[6,10],axis1=[1,0,0],axis2=[0,0,1],loStop1=joint_ranges[5][1][0],hiStop1=joint_ranges[5][1][1],loStop2=joint_ranges[5][0][0],hiStop2=joint_ranges[5][0][1],fmax=R_MID_FORCE[0],fmax2=R_MID_FORCE[1],erp1=ERP[4][0],erp2=ERP[4][1],cfm1=CFM[4][0],cfm2=CFM[4][1])
        self.joint_feedback_joints.append(9)

        # Front Low Legs
        self.man.create_capsule(11, body_masses[7], leg_dims[4][0], leg_dims[4][1],[0,0,0],rot=[0.,0.,0.],mass_flag=True)
        j_loc = Placement.place_capsule_trans(self.man.bodies[7],self.man.bodies[11],rot=leg_rotations[4]) 
        if(self.low_hinge):
            self.man.create_flexible_universal(10, j_loc,[7,11],axis1=[1,0,0],axis2=[0,0,1],loStop1=joint_ranges[6][1][0],hiStop1=joint_ranges[6][1][1],loStop2=joint_ranges[6][0][0],hiStop2=joint_ranges[6][0][1],fmax=F_LOW_FORCE[0],fmax2=F_LOW_FORCE[1],erp1=ERP[5][0],erp2=ERP[5][1],cfm1=CFM[5][0],cfm2=CFM[5][1])
            self.joint_feedback_joints.append(10)
        elif(genome.stiff_slider):
            self.man.create_slider(10,j_loc,[7,11],axis=[0,1,0],loStop=low_slider[0],hiStop=high_slider)
        else:
            self.man.create_flexible_slider(10,j_loc,[7,11],axis=[0,1,0],loStop=low_slider[0],hiStop=high_slider,erp=slider_erp[0],cfm=slider_cfm[0])
        self.man.create_capsule(12, body_masses[7], leg_dims[4][0], leg_dims[4][1],[0,0,0],rot=[0.,0.,0.],mass_flag=True)
        j_loc = Placement.place_capsule_trans(self.man.bodies[8],self.man.bodies[12],rot=leg_rotations[4]) 
        if(self.low_hinge):
            self.man.create_flexible_universal(11, j_loc,[8,12],axis1=[1,0,0],axis2=[0,0,1],loStop1=joint_ranges[6][1][0],hiStop1=joint_ranges[6][1][1],loStop2=joint_ranges[6][0][0],hiStop2=joint_ranges[6][0][1],fmax=F_LOW_FORCE[0],fmax2=F_LOW_FORCE[1],erp1=ERP[5][0],erp2=ERP[5][1],cfm1=CFM[5][0],cfm2=CFM[5][1])
            self.joint_feedback_joints.append(11)
        elif(genome.stiff_slider):
            self.man.create_slider(11,j_loc,[8,12],axis=[0,1,0],loStop=low_slider[0],hiStop=high_slider)
        else:
            self.man.create_flexible_slider(11,j_loc,[8,12],axis=[0,1,0],loStop=low_slider[0],hiStop=high_slider,erp=slider_erp[0],cfm=slider_cfm[0])

        # Rear Low Legs
        self.man.create_capsule(13, body_masses[8], leg_dims[5][0], leg_dims[5][1],[0,0,0],rot=[0.,0.,0.],mass_flag=True)
        j_loc = Placement.place_capsule_trans(self.man.bodies[9],self.man.bodies[13],rot=leg_rotations[5]) 
        if(self.low_hinge):
            self.man.create_flexible_universal(12, j_loc,[9,13],axis1=[1,0,0],axis2=[0,0,1],loStop1=joint_ranges[7][1][0],hiStop1=joint_ranges[7][1][1],loStop2=joint_ranges[7][0][0],hiStop2=joint_ranges[7][0][1],fmax=R_LOW_FORCE[0],fmax2=R_LOW_FORCE[1],erp1=ERP[6][0],erp2=ERP[6][1],cfm1=CFM[6][0],cfm2=CFM[6][1])
            self.joint_feedback_joints.append(12)
        elif(genome.stiff_slider):
            self.man.create_slider(12,j_loc,[9,13],axis=[0,1,0],loStop=low_slider[1],hiStop=high_slider)
        else:
            self.man.create_flexible_slider(12,j_loc,[9,13],axis=[0,1,0],loStop=low_slider[1],hiStop=high_slider,erp=slider_erp[1],cfm=slider_cfm[1])
        self.man.create_capsule(14, body_masses[8], leg_dims[5][0], leg_dims[5][1],[0,0,0],rot=[0.,0.,0.],mass_flag=True)
        j_loc = Placement.place_capsule_trans(self.man.bodies[10],self.man.bodies[14],rot=leg_rotations[5]) 
        if(self.low_hinge):
            self.man.create_flexible_universal(13, j_loc,[10,14],axis1=[1,0,0],axis2=[0,0,1],loStop1=joint_ranges[7][1][0],hiStop1=joint_ranges[7][1][1],loStop2=joint_ranges[7][0][0],hiStop2=joint_ranges[7][0][1],fmax=R_LOW_FORCE[0],fmax2=R_LOW_FORCE[1],erp1=ERP[6][0],erp2=ERP[6][1],cfm1=CFM[6][0],cfm2=CFM[6][1])
            self.joint_feedback_joints.append(13)
        elif(genome.stiff_slider):
            self.man.create_slider(13,j_loc,[10,14],axis=[0,1,0],loStop=low_slider[1],hiStop=high_slider)
        else:
            self.man.create_flexible_slider(13,j_loc,[10,14],axis=[0,1,0],loStop=low_slider[1],hiStop=high_slider,erp=slider_erp[1],cfm=slider_cfm[1])

        # Add in information about the feet.
        self.sensor_components['touch'].add_touch_sensors([11,12,13,14],['FLFoot','FRFoot','RLFoot','RRFoot'])
        #self.sensor.add_touch_sensor([11,12,13,14])
        self.man.bodies[11].touch=True
        self.man.bodies[12].touch=True
        self.man.bodies[13].touch=True
        self.man.bodies[14].touch=True
        touch_logging.append({11:0,12:0,13:0,14:0})
        touch_logging.append({11:0,12:0,13:0,14:0})

        # Add in joint positions sensors.
        self.sensor.register_joint_sensors([0,1,2,3,4,5,6,7,8,9,10,11,12,13])

        # Turn feedback on for the actuated joints.
        for i in self.joint_feedback_joints:
            self.man.joints[i].setFeedback()

    def get_body_nums(self):
        """ Get the body numbers used in the quadruped. """
        return [i for i in range(15)]

    def actuate_joints_by_pos(self,positions=[[0.,0.] for i in xrange(8)]):
        """ Actuate the joints of the quadruped to the specified position. 

        Arguments:
            positions: position of the joints to actuate to.
        """

        for i,p in enumerate(positions):
            # This if statement is redundant, but explicitly breaks out commands in case
            # we change them in the future based on the joint.
            if i < 10:
                self.man.actuate_universal(i,p[0],p[1])
            elif i < 14 and self.low_hinge: # Actuate hinge joints if we have hinge lower set.
                self.man.actuate_universal(i,p[0],p[1])

    def get_flipped(self):
        """ Determine if the hopper flipped over or not based on the position of the main torso. """
        top_pos = (self.man.get_rel_position(1,(0.,self.main_body_dimensions[1]/2.,0.)))[1]
        bot_pos = (self.man.get_rel_position(1,(0.,-self.main_body_dimensions[1]/2.,0.)))[1]

        # Check to see if we've flipped to almost completely upside down.
        if (top_pos-bot_pos)/math.fabs(self.main_body_dimensions[1]) < -0.9:
            return True

        return False            

    def get_sensor_states(self):
        """ Get the states of the various sensors on the robot. """
        sensors = [i for i in self.sensor.get_touch_sensor_states()]
        sensors += [i for i in self.sensor.get_joint_sensors()]
        return sensors

    def activate_touch_sensor(self,body_id,contact_pos):
        """ Activate a touch sensor.

        Args:
            body_id: body id of the sensor
            contact_pos: position of the contact (x,y,z)
        """
        self.sensor_components['touch'].activate_touch_sensor(body_id,contact_pos)

    def get_touch_sensor_states(self):
        """ Get the state of the touch sensor for debugging. """
        return self.sensor_components['touch'].get_sensors()

    def get_joint_feedback(self):
        """ Get the feedback from the joints. """

        joint_feedback = []
        for i in self.joint_feedback_joints:
            joint_feedback.append(self.man.joints[i].getFeedback())
        return joint_feedback

    def step_sensors(self,cur_time):
        """ Step the sensor information. """
        self.sensor.step(cur_time)
        self.sensor_components['touch'].clear_sensors(cur_time)

    def log_sensor_data(self,file_prefix):
        """ Log the sensor data. 

            Intended to use for validation.
        """
        self.sensor.dump_sensor_data(file_prefix)
        self.sensor_components['touch'].dump_data(file_prefix)

############################################################################################################        

def vector_3d_magnitude(vec):
    """ Return the magnitude of a vector in 3D. """

    vec = [vec[0],vec[1],vec[2]]

    # Filter out low values in the vector.
    for i in range(len(vec)):
        if math.fabs(vec[i]) < 0.0001:
            vec[i] = math.copysign(0.0001,vec[i])
        elif math.fabs(vec[i]) > 1000.:
            vec[i] = math.copysign(1000.,vec[i])

    if sum(vec) < 0.01 or (math.isnan(vec[0]) or math.isnan(vec[1]) or math.isnan(vec[2])):
        return 0
    force_mag = 0    
    try:
        force_mag = math.sqrt(vec[0]**2+vec[1]**2+vec[2]**2)
    except OverflowError as e:
        print("\n\n\n")
        print("OverflowError: ",e,vec)
        print("\n\n\n")
    return force_mag

def distance_per_unit_of_power(p1,p2,forces):
    """ Calculate the distance per unit of power. """
    distance = math.sqrt((p1[0]-p2[0])**2 + (p1[2]-p2[2])**2)

    forces = [i for f in forces for i in f]
    forces = zip(*forces)
    total_power = sum([abs(i) for i in forces[0]]) + sum([abs(j) for j in forces[1]])

    return (distance)/total_power    

def euclidean_distance(p1,p2):
    """ Calculate the 2d Euclidean distance of two coordinates.
    
    Args:
        p1: position 1
        p2: position 2
    Returns:
        Euclidean distance between the two points.
    """
    return math.sqrt((p1[0]-p2[0])**2 + (p1[2]-p2[2])**2) 

############################################################################################################

# Collision callback
def near_callback(args, geom1, geom2):
    """Callback function for the collide() method.

    This function checks if the given geoms do collide and
    creates contact joints if they do.
    """
    global touch_logging

    # Check to see if the two objects are connected.  Don't collide.
    if(man.are_connected(geom1.getBody(), geom2.getBody()) or (geom1 != man.floor and geom2 != man.floor)):
        return

    # Check if the objects do collide
    contacts = man.generate_contacts(geom1, geom2)

    # Check to see if one of the objects is a foot sensor and the other
    # is the ground.
    if (geom1 == man.floor and hasattr(geom2.getBody(),'touch') or
        geom2 == man.floor and hasattr(geom1.getBody(),'touch')):
        body_id = man.get_body_key(geom2.getBody()) if geom1 == man.floor else man.get_body_key(geom1.getBody())
        quadruped.activate_touch_sensor(body_id,[i for i in contacts[0].getContactGeomParams()[0]])
        touch_logging[1][body_id] = 1

    # Check to see if we are colliding between the floor and a body or bodies on the robot.
    # Set the friction accordingly.
    if not(geom1 == man.floor or geom2 == man.floor):
        mu = 0.1 # Low friction
    else:
        mu = 10 # High friction

    # Create contact joints
    man.world,man.contactgroup = args
    for c in contacts:
        c.setBounce(0.2)
        c.setMu(mu)
        j = man.create_contact_joint(c)
        j.attach(geom1.getBody(), geom2.getBody())

class Simulation(object):
    """ Define a simulation to encapsulate an ODE simulation. """

    def __init__(self, log_frames=0, run_num=0, eval_time=10., dt=.02, n=4,hyperNEAT=False,substrate=False,periodic=True,file_prefix=""):
        """ Initialize the simulation class. """
        global simulate

        man = ""

        # Settings for the simulation.
        self.log_frames = log_frames
        self.run_num = run_num
        self.eval_time = eval_time
        self.elapsed_time = 0.
        self.dt = dt            # Timestep for simulation.
        self.n = n              # How many timesteps to simulate per callback.

        self.current_network = 0

        self.hyperNEAT = True if hyperNEAT else False
        self.substrate = substrate

        # Whether we include a periodic oscillating input signal.
        self.periodic = periodic

        # Genome for a quadruped.
        self.genome = ""

        # Explosion condition.
        self.exploded = False

        # Flipping condition.
        self.flipped = False
        self.flipped_time = 0.
        self.flipped_dist = 0.

        # Joint Force Logging
        self.joint_feedback = []
        self.forces = []

        # Set the file prefix for validation purposes.
        self.file_prefix = file_prefix

    def update_callback(self):
        """ Function to handle updating the joints and such in the simulation. """

        # Record joint forces for calculation in the fitness function.
        jf = quadruped.get_joint_feedback()
        
        self.forces.append([vector_3d_magnitude(jf[i][0]),vector_3d_magnitude(jf[i][2])] for i in range(len(jf)))
        
        if self.log_frames:
            # Record the joint feedback for validation.
            self.joint_feedback.append([self.elapsed_time,
                                        i,
                                        sum(jf[i][0]),
                                        sum(jf[i][1]),
                                        sum(jf[i][2]),
                                        sum(jf[i][3])] for i in range(len(jf)))

        positions = []

        if not hasattr(self.genome, 'delta') and not hasattr(self.genome, 'deltas'):
            # Use a sin oscillator.
            positions = [
                         [0,0], # Rear Spine (Up/Down, sideways)
                         [0,0], # Front Spine (Up/Down, sideways)
                         [0,math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.limb_offsets[0]+self.genome.joint_offsets[0])))], # Front Left Hip (Outwards, Forward/Back)
                         [0,math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.limb_offsets[1]+self.genome.joint_offsets[0])))], # Front Right Hip (Outwards, Forward/Back)
                         [0,math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.limb_offsets[2]+self.genome.joint_offsets[2])))], # Rear Left Hip (Outwards, Forward/Back)
                         [0,math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.limb_offsets[3]+self.genome.joint_offsets[2])))], # Rear Right Hip (Outwards, Forward/Back)
                         [0,math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.limb_offsets[0]+self.genome.joint_offsets[1])))], # Front Left Knee (Outwards, Forward/Back)
                         [0,math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.limb_offsets[1]+self.genome.joint_offsets[1])))], # Front Right Knee (Outwards, Forward/Back)
                         [0,math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.limb_offsets[2]+self.genome.joint_offsets[3])))], # Rear Left Knee (Outwards, Forward/Back)
                         [0,math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.limb_offsets[3]+self.genome.joint_offsets[3])))], # Rear Right Knee (Outwards, Forward/Back)
                        ]
            if (self.genome.hinge_lower):
                positions.append([0,math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.limb_offsets[0]+self.genome.joint_offsets[4])))]) # Front Left Ankle (Outwards, Forward/Back)
                positions.append([0,math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.limb_offsets[1]+self.genome.joint_offsets[4])))]) # Front Right Ankle (Outwards, Forward/Back)
                positions.append([0,math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.limb_offsets[2]+self.genome.joint_offsets[5])))]) # Rear Left Ankle (Outwards, Forward/Back)
                positions.append([0,math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.limb_offsets[3]+self.genome.joint_offsets[5])))]) # Rear Right Ankle (Outwards, Forward/Back)
            if (self.genome.actuated_spine):
                positions[0] = [math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.spine_offsets[0]))),0] # Rear spine, (Outwards, Forward/Back)
                positions[1] = [math.sin(-self.genome.osc_freq*2.*math.pi*(self.elapsed_time)+(2.*math.pi*(self.genome.spine_offsets[1]))),0] # Front spine, (Outwards, Forward/Back)                    
        elif hasattr(self.genome, 'delta'):
            # Use the shift_oscillator
            positions = [
                     [0,0], # Rear Spine (Up/Down, sideways)
                     [0,0], # Front Spine (Up/Down, sideways)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.delta,(self.genome.limb_offsets[0]+self.genome.joint_offsets[0]))], # Front Left Hip (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.delta,(self.genome.limb_offsets[1]+self.genome.joint_offsets[0]))], # Front Right Hip (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.delta,(self.genome.limb_offsets[2]+self.genome.joint_offsets[2]))], # Rear Left Hip (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.delta,(self.genome.limb_offsets[3]+self.genome.joint_offsets[2]))], # Rear Right Hip (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.delta,(self.genome.limb_offsets[0]+self.genome.joint_offsets[1]))], # Front Left Knee (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.delta,(self.genome.limb_offsets[1]+self.genome.joint_offsets[1]))], # Front Right Knee (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.delta,(self.genome.limb_offsets[2]+self.genome.joint_offsets[3]))], # Rear Left Knee (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.delta,(self.genome.limb_offsets[3]+self.genome.joint_offsets[3]))], # Rear Right Knee (Outwards, Forward/Back)
                    ]
            if (self.genome.hinge_lower):
                raise RuntimeError('Hinge lower was not implemented for the shift_oscillator.')
            if (self.genome.actuated_spine):
                raise RuntimeError('Actuated spine was not implemented for the shift_oscillator.')                
        else:
            # Use the shift_oscillator per joint
            positions = [
                     [0,0], # Rear Spine (Up/Down, sideways)
                     [0,0], # Front Spine (Up/Down, sideways)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.deltas[0],(self.genome.limb_offsets[0]+self.genome.joint_offsets[0]))], # Front Left Hip (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.deltas[0],(self.genome.limb_offsets[1]+self.genome.joint_offsets[0]))], # Front Right Hip (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.deltas[1],(self.genome.limb_offsets[2]+self.genome.joint_offsets[2]))], # Rear Left Hip (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.deltas[1],(self.genome.limb_offsets[3]+self.genome.joint_offsets[2]))], # Rear Right Hip (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.deltas[2],(self.genome.limb_offsets[0]+self.genome.joint_offsets[1]))], # Front Left Knee (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.deltas[2],(self.genome.limb_offsets[1]+self.genome.joint_offsets[1]))], # Front Right Knee (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.deltas[3],(self.genome.limb_offsets[2]+self.genome.joint_offsets[3]))], # Rear Left Knee (Outwards, Forward/Back)
                     [0,shift_oscillator(self.elapsed_time,self.genome.osc_freq,self.genome.deltas[3],(self.genome.limb_offsets[3]+self.genome.joint_offsets[3]))], # Rear Right Knee (Outwards, Forward/Back)
                    ]
            if (self.genome.hinge_lower):
                raise RuntimeError('Hinge lower was not implemented for the shift_oscillator per joint.')
            if (self.genome.actuated_spine):
                raise RuntimeError('Actuated spine was not implemented for the shift_oscillator per joint.')                    

        quadruped.actuate_joints_by_pos(positions=positions)

    def reset_simulation(self):
        """ Reset the simulation. """
        
        global num_touches

        man.delete_joints()
        man.delete_bodies()
        self.exploded = False
        self.flipped = False
        self.elapsed_time = 0.
        self.flipped_time = 0.
        self.flipped_dist = 0.
        self.forces = []
        self.joint_feedback = []
        num_touches = 0
        touch_logging = []

    def simulate(self):
        """ Perform physics simulation. """
        global num_touches, touch_logging

        if self.elapsed_time < self.eval_time: 
            self.update_callback()

            # Update the touching code.
            for k,v in touch_logging[0].iteritems():
                if touch_logging[1][k] != v and v == 0:
                    num_touches += 1
            touch_logging[0] = touch_logging[1].copy() # Ensure we don't copy objects.
            touch_logging[1] = dict.fromkeys( touch_logging[1].iterkeys(), 0 ) # Reset the touch sensors to null state.

            # Check to see if we flipped over.
            if not self.flipped and quadruped.get_flipped():
                self.flipped = True
                self.flipped_time = self.elapsed_time
                self.flipped_dist = euclidean_distance(man.get_body_position(0),[0,0,0])

            # Periodically check to see if we exploded.
            # Check to see about explosions.
            pos = man.bodies[0].getPosition()
            ang_vel = man.bodies[0].getAngularVel()
            lin_vel = man.bodies[0].getLinearVel()
            #if int(self.elapsed_time*100.) % 2 == 0 and 
            if (math.fabs(pos[0]) > 200 or math.fabs(pos[1]) > 20. or math.fabs(pos[2]) > 200) \
                or (math.fabs(ang_vel[0]) > 20 or math.fabs(ang_vel[1]) > 20 or math.fabs(ang_vel[2]) > 20) or \
                (math.fabs(lin_vel[0]) > 30 or math.fabs(lin_vel[1]) > 30 or math.fabs(lin_vel[2]) > 30):
                # Dump explosion genome and logging information to file.
                # self.explosion_logging(pos,ang_vel,lin_vel)
                self.exploded = True 
        if self.elapsed_time >= self.eval_time or self.exploded:
            #fit = [0,100000,0,0,100000]
            fit = [0,0,100000]
            if not self.exploded:
                self.com_evaluation.process_data()

                # fit[0] = euclidean_distance(man.get_body_position(1),[0,0,0]) if not self.flipped else self.flipped_dist
                # fit[1] = num_touches
                # fit[2] = self.flipped_time if self.flipped else self.elapsed_time
                # fit[3] = distance_per_unit_of_power(man.get_body_position(0),[0,0,0],self.forces)
                # fit[4] = self.com_evaluation.get_vertical_movement_delta()

                fit[0] = euclidean_distance(man.get_body_position(1),[0,0,0]) if not self.flipped else self.flipped_dist
                #fit[1] = num_touches
                #fit[2] = self.flipped_time if self.flipped else self.elapsed_time
                fit[1] = distance_per_unit_of_power(man.get_body_position(0),[0,0,0],self.forces)
                fit[2] = self.com_evaluation.get_vertical_movement_delta()

                if self.log_frames:
                    self.com_evaluation.write_data(output_path+"/"+self.file_prefix)

            self.reset_simulation()
            return False, fit
        quadruped.step_sensors(self.elapsed_time)
        return True, 0 

    def explosion_logging(self, pos, ang_vel, lin_vel):
        """ Log the genome and conditions leading to an explosion for an individual. 

        Args:
            pos: position of an individual
            ang_vel: angular velocity of an individual
            lin_vel: linear velocity of an individual
        """
        # Check to see if explosion file has been created.
        with open(str(self.run_num)+"_explosion_log.dat","a") as f:
            f.write("Genome: "+str(self.genome)+"\n")
            f.write("Position:"+str(pos)+"\n")
            f.write("Ang Vel:"+str(ang_vel)+"\n")
            f.write("Lin Vel:"+str(lin_vel)+"\n")
            f.write("\n\n\n")

    def physics_only_simulation(self):
        """ Initialize and conduct a simulation. """
        global man, quadruped

        # Initialize the manager to be unique to the process.
        man = ODEManager(near_callback, stepsize=self.dt/self.n, log_data=self.log_frames, run_num=self.run_num, eval_time=self.eval_time, max_joint_vel=self.genome.max_joint_vel,output_path=output_path+"/"+self.file_prefix)

        # Initialize the quadruped
        quadruped = Quadruped(man=man,genome=self.genome,logging=self.log_frames)

        # Initialize the COMEvaluation
        self.com_evaluation = COMEvaluation(
            man,
            quadruped.get_body_nums(),
            self.dt
        )

        # If logging the output, tell manager to write the body type, dimensions, and position to the logging file.
        if self.log_frames:
            man.log_world_setup()

        # Have a settling period to fall to the ground.
        settle = 0.0
        while settle < 1.0:
            man.step(near_callback, self.n)
            settle += self.dt
       
        go_on, fit = self.simulate()
        while go_on:
            # Simulate physics
            man.step(near_callback, self.n)
            self.com_evaluation.add_timestep()
            self.elapsed_time += self.dt
            go_on, fit = self.simulate()

        # Log the sensor data at the end of a run.
        if self.log_frames:
            quadruped.log_sensor_data(self.file_prefix)

        return fit

    def evaluate_individual(self,genome):
        """ Evaluate an individual solution. 

        Args:
            genome: genome of the individual to evaluate

        Returns:
            fitness value of the individual
        """

        # Set the genome.
        self.genome = genome

        # Conduct the evaluation
        return self.physics_only_simulation() 
