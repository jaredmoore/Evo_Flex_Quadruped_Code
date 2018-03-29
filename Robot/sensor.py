"""
    Version 2

    Class to hold information about various sensors on a robot.
"""

import os
import random
import ode
from temp_signal import TSignal

class SensorLog(object):
    """ Provides a set of methods to log the various sensors and 
        write them out to log files. """

    def __init__(self,log_path):
        """ Initializer """

        self.touches = {}
        self.body_touches = {}
        self.joint_angles = {}
        self.dist_sensors = {}

        # Where to store the log files.
        self.log_path = log_path

    def log_touching(self,cur_time,touch_mapping,touch_data,touch_positions):
        """ Log the touch sensor information. """
        for (k,v) in touch_mapping.iteritems():
            if touch_data[v] == 1:
                self.touches[(cur_time,k)] = touch_positions[v]
        #self.touches[cur_time] = [i for i in touch_data] + [i for j in touch_positions for i in j]

    def log_body_touching(self,cur_time,body_touch_mapping,body_touch_data,body_touch_positions):
        """ Log the touch sensor information. """
        for (k,v) in body_touch_mapping.iteritems():
            if body_touch_data[v] == 1:
                self.body_touches[(cur_time,k)] = body_touch_positions[v]

    def log_joints(self,cur_time,joint_data):
        """ Log the joint angle sensor information. """
        self.joint_angles[cur_time] = [i for i in joint_data]

    def log_distances(self,cur_time,dist_data):
        """ Log the distance sensor information. """
        self.dist_data[cur_time] = [i for i in dist_data]

    def write_log_files(self,file_prefix):
        """ Write out the various log files. """
        # Create the directories for logging.
        if not os.path.exists(self.log_path+"/validator_logging/"):
            os.makedirs(self.log_path+"/validator_logging")

        # Write the files.
        if len(self.touches) > 0:
            if not os.path.exists(self.log_path+"/validator_logging/contact_sensors"):
                os.makedirs(self.log_path+"/validator_logging/contact_sensors")
            self.write_touch_file(file_prefix)
        if len(self.body_touches) > 0:
            if not os.path.exists(self.log_path+"/validator_logging/body_touching"):
                os.makedirs(self.log_path+"/validator_logging/body_touching")
            self.write_body_touch_file(file_prefix)
        if len(self.joint_angles) > 0:
            if not os.path.exists(self.log_path+"/validator_logging/joint_angles"):
                os.makedirs(self.log_path+"/validator_logging/joint_angles")
            self.write_joints_file(file_prefix)
        #if len(self.dist_sensors) > 0:
        #    if not os.path.exists(self.log_path+"/validator_logging/dist_sensors"):
        #        os.makedirs(self.log_path+"/validator_logging/dist_sensors")
        #    self.write_dist_file(file_prefix)

    def write_touch_file(self,file_prefix):
        """ Write out the touch file. """
        f_pre = file_prefix.split("/")[-1].strip()
        with open(self.log_path+"/validator_logging/contact_sensors/"+f_pre+"_contacts.dat","w") as f:
            # Write the headers.
            f.write("Time,Body_ID,X,Y,Z\n")

            # Write out the values.
            for k,i in self.touches.iteritems():
                f.write(str(k[0])+','+str(k[1])+','+','.join(map(str,i[0:]))+"\n")

    def write_body_touch_file(self,file_prefix):
        """ Write out the body touch file. """
        f_pre = file_prefix.split("/")[-1].strip()
        with open(self.log_path+"/validator_logging/body_touching/"+f_pre+"_body_touches.dat","w") as f:
            # Write the headers.
            f.write("Time,Body_ID,X,Y,Z\n")

            # Write out the values.
            for k,i in self.body_touches.iteritems():
                f.write(str(k[0])+','+str(k[1])+','+','.join(map(str,i[0:]))+"\n")

    def write_joints_file(self,file_prefix):
        """ Write out the joints file. """
        # Setup the joint angles file.
        with open(self.log_path+"/validator_logging/joint_angles/"+file_prefix+"_joint_angles.dat", "w") as f:
            # Write the headers.
            f.write("Time")
            for i in range(0,len(self.joint_angles.itervalues().next()),2):
                f.write(",Universal_Angle_1_"+str(i/2)+",Universal_Angle_2_"+str(i/2))
            f.write("\n")

            # Write out the values.
            for k,i in self.joint_angles.iteritems():
                f.write(str(k)+','+','.join(map(str,i[0:]))+"\n")

    def write_dist_file(self,file_prefix):
        """ Write out the distances file. """
        pass

class Sensors(object):
    """ Provides methods to emulate sensors on a robot. """

    def __init__(self,man,logging=False,log_path="./"):
        """ Initializer """
    
        self.man = man

        # Touch Sensor Data
        self.touch_index = 0
        self.touch = {}
        self.touching = []
        self.touch_position = []

        # Body Touching Data
        self.body_touch_index = 0
        self.body_touch = {}
        self.body_touching = []
        self.body_touch_position = []

        # Joint Position Sensor Data
        self.joints = [] # What joints are logged?
        self.joint_angles = [] # Current angles of the joints.

        # Temporal Signal Generators
        self.tsignals = []

        # Distance Sensor Data
        self.dist_sensors = {}

        # Logging information
        self.logging = logging
        if self.logging:
            self.sensor_log = SensorLog(log_path)


    def copy(self):
        """ Copy self. """
        s = Sensors(self.man)
        s.touch = self.touch
        s.touching = self.touching
        s.touch_position = self.touch_position
        s.body_touch = self.body_touch
        s.body_touching = self.body_touching
        s.body_touch_position = self.body_touch_position
        s.joints = self.joints
        s.dist_sensors = self.dist_sensors
        for tsig in self.tsignals:
            s.add_temp_signal(params=tsig.serialize())

        return s

    def __str__(self):
        """ To string function. """
        out = ""
        for i in xrange(len(self.tsignals)-1):
            out += str(self.tsignals[i])+","
        out += str(self.tsignals[-1])+"\n"
        return out

    def dump_sensor_data(self,file_prefix):
        """ Dump the sensor data. 

            Intended to be used for logging.
        """
        self.sensor_log.write_log_files(file_prefix)

    def step(self,cur_time):
        """ Step the sensors, commit data to logs, and reset sensors. 

        <Deprecated in favor of calling clear_sensors.>
        """
        import warnings
        warnings.warn(
            "Function Sensor.step() deprecated in favor of Sensor.clear_sensors.",
            DeprecationWarning
        )

        self.clear_sensors(cur_time)

    def clear_sensors(self,cur_time):
        """ Clear the sensor values currently held.  (Each Timestep) """
        # Log the sensor data.
        if self.logging:
            if len(self.touching) > 0:
                self.sensor_log.log_touching(cur_time,self.touch,self.touching,self.touch_position)
            if len(self.body_touching) > 0:
                self.sensor_log.log_body_touching(cur_time,self.body_touch,self.body_touching,self.body_touch_position)
            if len(self.joint_angles) > 0:
                self.sensor_log.log_joints(cur_time,self.joint_angles)
            if len(self.dist_sensors) > 0:
                self.sensor_log.log_distances(cur_time,self.dist_sensors)

        self.clear_touching()
        self.clear_body_touching()
        self.joint_angles = []
        self.reset_distance_sensors()

    def reset(self):
        """ Reset the information held by the sensor class. """
        self.touch_index = 0
        self.touch = {}
        self.touching = []
        self.touch_position = []
        self.body_touch_index = 0
        self.body_touch = {}
        self.body_touching = []
        self.touch_position = []
        self.joints = []
        self.joint_angles = []
        self.tsignals = []
        self.dist_sensors = {}

    def mutate(self):
        """ Mutate a signal node if necessary. """
        if len(self.tsignals) > 0:
            index = random.randint(0,len(self.tsignals)-1)
            self.tsignals[index].mutate()

    """ Touch Sensor Information """
    def add_touch_sensor(self,body_nums):
        """ Add a touch sensor to the dictionary.

        Args:
            body_nums: body number to add as a touch sensor.
        """
        if type(body_nums) is list:
            for bnum in body_nums:
                self.touch[bnum] = self.touch_index
                self.touch_index += 1
                self.touching.append(0)
                self.touch_position.append(["NA","NA","NA"])
        else:
            self.touch[body_nums] = self.touch_index
            self.touch_index += 1
            self.touching.append(0)
            self.touch_position.append(["NA","NA","NA"])

    def is_touch_sensor(self,body_num):
        """ See if a body is a touch sensor.  

        Args:
            body_num: body number to check
        Returns:
            1 if a touch sensor, 0 if not
        """
        if body_num in self.touch:
            return 1
        else:
            return 0

    def activate_touch_sensor(self,body_num,touch_position):
        """ Activate a touch sensor. 

        Args:
            body_num: body number of the sensor to trigger
            touch_position: [x,y,z] of touch location
        """
        self.touching[self.touch[body_num]] = 1
        self.touch_position[self.touch[body_num]] = touch_position

    def get_touch_sensor_states(self):
        """ Return a list containing the current touch sensor states. """
        return self.touching

    def clear_touching(self):
        """ Reset the touch values to 0. """
        for i in range(len(self.touching)):
            self.touching[i] = 0
            self.touch_position[i] = ["NA","NA","NA"]

    """ Body Touch Sensor Information """
    def add_body_touch_sensor(self,body_nums):
        """ Add a touch sensor to the dictionary.

        Args:
            body_nums: body number to add as a touch sensor.
        """
        if type(body_nums) is list:
            for bnum in body_nums:
                self.body_touch[bnum] = self.body_touch_index
                self.body_touch_index += 1
                self.body_touching.append(0)
                self.body_touch_position.append(["NA","NA","NA"])
        else:
            self.body_touch[body_nums] = self.body_touch_index
            self.body_touch_index += 1
            self.body_touching.append(0)
            self.body_touch_position.append(["NA","NA","NA"])

    def activate_body_touch_sensor(self,body_num,touch_position):
        """ Activate a touch sensor. 

        Args:
            body_num: body number of the sensor to trigger
            touch_position: [x,y,z] of touch location
        """
        self.body_touching[self.body_touch[body_num]] = 1
        self.body_touch_position[self.body_touch[body_num]] = touch_position

    def get_body_touch_sensor_states(self):
        """ Return a list containing the current touch sensor states. """
        return self.body_touching

    def clear_body_touching(self):
        """ Reset the touch values to 0. """
        for i in range(len(self.body_touching)):
            self.body_touching[i] = 0
            self.body_touch_position[i] = ["NA","NA","NA"]

    """ Joint Position Sensor Information """
    def add_joint_sensor(self,joint):
        """ Add a joint sensor to the suite. 

        Args:
            joint: ODE joint object
        """
        self.joints.append(joint)

    def register_joint_sensors(self,joint_nums):
        """ Register a list of joints as joint sensors.

        Args:
            joint_nums: list of joint numbers to register
        """
        if type(joint_nums) is list:
            self.joints += joint_nums
#            for jnum in joint_nums:
#                self.joints.append(joint_nums)
        else:
            self.joints.append(joint_nums)

    def get_joint_sensors(self):
        """ Get the position of each joint sensor.

        Returns:
            list containing position of joints in radians.
        """
        for j in self.joints:
            low1 = self.man.get_uni_joint_limit(j,ode.ParamLoStop)
            high1 = self.man.get_uni_joint_limit(j,ode.ParamHiStop)
            range1 = (high1 - low1)
            midpoint = low1 + range1/2.
            cur_pos = self.man.get_uni_joint_position(j,0)
            if high1-low1 == 0:
                self.joint_angles.append(0)
            else:
                self.joint_angles.append((cur_pos-midpoint)/(range1/2.))

            low2 = self.man.get_uni_joint_limit(j,ode.ParamLoStop2)
            high2 = self.man.get_uni_joint_limit(j,ode.ParamHiStop2)
            range2 = (high2 - low2)
            midpoint = low2 + range2/2.
            cur_pos = self.man.get_uni_joint_position(j,1)
            if high2-low2 == 0:
                self.joint_angles.append(0)
            else:
                self.joint_angles.append((cur_pos-midpoint)/(range2/2.))

        return self.joint_angles

    def clear_joint_sensors(self):
        """ Clear the list of joint sensors. """
        self.joints = []

    def add_temp_signal(self,params=0):
        """ Add a temporal signal node to the sensor suite. 

        Args:
            params: parameters to create a predefined temporal signal node
        """
        self.tsignals.append(TSignal(params=params))

    def get_temp_signals(self):
        """ Get the signal from all temporal signal nodes. """
        return [tsig.next() for tsig in self.tsignals]
            
    def clear_temp_signals(self):
        """ Clear the list of temporal signals. """
        self.tsignals = []

    """ Distance Sensor Configuration """
    def add_dist_sensor(self,geom_num,max_dist):
        """ Add a distance sensor. 

        Args:
            geom_num: the number of the geom that is the sensor
            max_dist: maximum distance the sensor can reach
        """
        self.dist_sensors[geom_num] = {"max_dist":max_dist,"distance":max_dist+1}

    def set_distance(self,geom_num,dist):
        """ Set the distance to the nearest object within the sensors range. """
        self.dist_sensors[geom_num]['distance'] = dist

    def get_scaled_distances(self):
        """ Get the scaled distance data from each distance sensor. 

        Returns:
            list containing values between 0 and 1
        """
        return [float("{0:.6f}".format(self.get_scaled_distance(k))) for k,i in self.dist_sensors.iteritems()]

    def get_raw_distances(self):
        """ Get the raw distance data from each distance sensor. 

        Returns:
            list containing values between 0 and 1
        """
        return [self.get_raw_distance(k) for k,i in self.dist_sensors.iteritems()]

    def get_raw_distance(self,geom_num):
        """ Get the raw values associated with the distance sensor.

        This is the distance from the sensor to the nearest contact point.

        Args:
            geom_num: number of the sensor in ODE
        """
        return self.dist_sensors[geom_num]['distance'] if self.dist_sensors[geom_num]['distance'] < self.dist_sensors[geom_num]['max_dist'] \
            else self.dist_sensors[geom_num]['max_dist']

    def get_scaled_distance(self,geom_num,min=0,max=1):
        """ Return the scaled distance of an object in the sensor.  

        Args:
            geom_num: number of the sensor in ODE
            min: minimum value to scale to
            max: maximum value to scale to

        Returns:
            Value between min and max, closer to max the closer object is.
        """
        scaled = (self.dist_sensors[geom_num]['max_dist']-self.dist_sensors[geom_num]['distance'])/self.dist_sensors[geom_num]['max_dist']

        scaled = scaled if scaled >= 0 else 0

        return scaled

    def reset_distance_sensors(self):
        """ Reset all distance sensors. """
        for k,ds in self.dist_sensors.iteritems():
            ds['distance'] = ds['max_dist']+1

    def reset_distance_sensor(self,geom_num):
        """ Reset the distance sensor. """
        self.dist_sensors[geom_num]['distance'] = self.dist_sensors[geom_num]['max_dist']+1
