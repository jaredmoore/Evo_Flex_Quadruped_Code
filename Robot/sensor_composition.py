"""
	Interface for various sensors on a robot.  This approach uses composition in the robot definition of the ODE code
	to encapsulate each sensor with its own class and logging support.  
"""

import os

class BaseLog(object):
	""" Base class for logging functionality. """

	def __init__(self,log_path):
		""" Initialize the class.

		Args:
			log_path: path to write the log files to.
		"""
		self.log_path = log_path

	def write_headers(self,file_prefix):
		""" Write the headers for the sensor component. 

		Args:
			file_prefix: what to prepend to the filenames.
		"""
		pass

	def write_data(self,file_prefix):
		""" Write the data for the sensor component. 

		Args:
			file_prefix: what to prepend to the filenames.
		"""
		pass

class BaseSensorComponent(object):
	""" Base class for sensor functionality. """

	def __init__(self, man):
		self.man = man

	def set_sensors(self):
		pass

	def get_sensors(self):
		pass

##############################

class TouchLog(BaseLog):
	""" Touch sensor logging functionality. """

	def __init__(self,log_path):
		""" Initialize the class.

		Args:
			log_path: path to write the log files to.
		"""
		super(TouchLog,self).__init__(log_path)
		self.header_abbreviations = {} # Map Body_ID to Component Name

		self.touches = {} # Key: Cur_Time, Body_ID

	def set_header_abbreviations(self,header_abbrev):
		""" Set the header abbrevations for logging. 

		Args:
			header_abbrev: string of abbreviations to map header to what component
		"""
		self.header_abbreviations = header_abbrev

	def write_data(self,file_prefix):
		""" Write the data for the sensor component. 

		Args:
			file_prefix: what to prepend to the filenames.
		"""
		if not os.path.exists(self.log_path+"/validator_logging/contact_sensors"):
			os.makedirs(self.log_path+"/validator_logging/contact_sensors")

		f_pre = file_prefix.split("/")[-1].strip()
		with open(self.log_path+"/validator_logging/contact_sensors/"+f_pre+"_contacts.dat","w") as f:
			# Write the headers.
			f.write("Time,Component,X,Y,Z\n")

			# Write out the values.
			for k,i in self.touches.iteritems():
				f.write(str(k[0])+','+str(self.header_abbreviations[k[1]])+','+','.join(map(str,i[0:]))+"\n")

	def record_touches_for_time(self,cur_time,touch,touching,touch_position):
		""" Log the touches for a timestep.

		Args:
			cur_time: current simulation time
			touch: mapping of body_ids to index in touching
			touching: which components are touching
			touch_position: position of a touch
		"""
		for (k,v) in touch.iteritems():
			if touching[v] == 1:
				self.touches[(cur_time,k)] = touch_position[v]


class TouchComponent(BaseSensorComponent):
    """ Provides touch sensor capability. """

    def __init__(self,man,logging=False,log_path="./"):
        """ Initializer """
    	super(TouchComponent, self).__init__(man)

        # Touch Sensor Data
        self.touch_index = 0
        self.touch = {} # Map body key to index in touching.
        self.touching = []
        self.touch_position = []

        # Logging information
        self.logging = logging
        if self.logging:
            self.touch_log = TouchLog(log_path)

    def dump_data(self,file_prefix):
        """ Write the sensor data to a file. """
        self.touch_log.write_data(file_prefix)

    def clear_sensors(self,cur_time):
        """ Clear the sensor values currently held.  (Each Timestep) """
        # Log the sensor data.
        if self.logging:
            if len(self.touching) > 0:
                self.touch_log.record_touches_for_time(cur_time,self.touch,self.touching,self.touch_position)

        self.clear_touching()

    def reset(self):
        """ Reset the information held by the sensor class. """
        self.touch_index = 0
        self.touch = {}
        self.touching = []
        self.touch_position = []

    """ Touch Sensor Information """
    def add_touch_sensors(self,body_nums,header_abbrevs):
        """ Add a touch sensor to the dictionary.

        Args:
            body_nums: body numbers to add as a touch sensor. (list)
        """
        assert type(body_nums) is list, "Body numbers for touching are not a list!"
        
        for bnum in body_nums:
            self.touch[bnum] = self.touch_index
            self.touch_index += 1
            self.touching.append(0)
            self.touch_position.append(["NA","NA","NA"])

        if self.logging:
        	header_dict = {}
        	for i,j in zip(body_nums,header_abbrevs):
        		header_dict[i] = j
        	self.touch_log.set_header_abbreviations(header_dict)

    def is_touch_sensor(self,body_num):
        """ See if a body is a touch sensor.  

        Args:
            body_num: body number to check
        Returns:
            1 if a touch sensor, 0 if not
        """
        if hasattr(self.man.bodies[body_num],'touch'):
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

    def get_sensors(self):
        """ Return a list containing the current touch sensor states. """
        return self.touching

    def clear_touching(self):
        """ Reset the touch values to 0. """
        for i in range(len(self.touching)):
            self.touching[i] = 0
            self.touch_position[i] = ["NA","NA","NA"]