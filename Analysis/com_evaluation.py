"""
	This class provides utilities to get the center of mass for each component of a robot, calculate the composite
	center of mass and then provide metrics assessing the variation in COM height and velocity.
"""

import utilities

class COMEvaluation(object):

	def __init__(self,man,body_nums,ts):
		""" Initialize the class. 

		Args:
			man: Manager class for the simulation environment.
			body_nums: list containing the id's of the bodies associated with the robot we are tracking.
			ts: simulation timestep duration
		"""

		# Metrics we are interested in.
		self.vertical_movement_delta = 0 # Total change in vertical position over the course of a simulation.
		self.potential_energy = [] # Ep = mgh
		self.kinetic_energy = [] # Ek = 0.5*mv^2
		self.velocity = []

		self.ts = ts
		self.steps = 0

		self.man = man

		self.body_nums = body_nums # Body Numbers Associated with the Robot (Manager Specific)

		self.body_masses = []

		for b in self.body_nums:
			self.body_masses.append(self.man.get_mass(b))

		self.comp_coms = [] # Tuple (position,total mass)

	def get_vertical_movement_delta(self):
		return self.vertical_movement_delta

	def get_total_kinetic_energy(self):
		return sum(self.kinetic_energy)

	def get_total_potential_energy(self):
		return sum(self.potential_energy)

	def add_timestep(self):
		""" Add the data for the various components for a given timestep. """
		
		self.comp_coms.append((self.ts*self.steps,self.calc_comp_com()))
		self.steps += 1

	def process_data(self):
		""" Process the collected information. """

		# Loop through the composite COM information and calculate the different metrics we are interested in.
		vertical_movement_total = 0
		for i,t in enumerate(self.comp_coms):
			vertical_movement_total += t[1][0][1]

			self.potential_energy.append(t[1][1] * -self.man.world.getGravity()[1] * t[1][0][1])

			if i > 0:
				self.velocity.append(self.calc_velocity(self.comp_coms[i-1][1][0],self.comp_coms[i][1][0]))
				self.kinetic_energy.append(0.5 * t[1][1] * self.velocity[i])
			else:
				# Append 0 to velocity and kinetic energy when initally starting. (Not moving yet.)
				self.velocity.append(0)
				self.kinetic_energy.append(0)

		# Calculate the average vertical position.
		avg_vert_pos = vertical_movement_total/len(self.comp_coms)

		self.vertical_movement_delta = 0
		for t in self.comp_coms:
			self.vertical_movement_delta += abs(t[1][0][1]-avg_vert_pos)

	def write_data(self,outpath):
		""" Write the collected data to a file. 

		Args:
			outpath: output path for the files
		"""
		# Write out the kinetic and potential energy.
		with open(outpath+"energy_data.dat","w") as f:
			f.write("Time,Kinetic_Energy,Potential_Energy,Velocity\n")

			# Loop through the timesteps data.
			for i in range(len(self.kinetic_energy)):
				f.write(str(i*self.ts)+","+\
					str(self.kinetic_energy[i])+","+\
					str(self.potential_energy[i])+","+\
					str(self.velocity[i])+"\n")

	def calc_comp_com(self):
		""" Calculate the composite center of mass for the robot. 

		Returns:
			Tuple containing the position of the composite COM and the total mass of the composite body.
		"""

		positions = []

		# Get the position for each body in the robot.
		for b in self.body_nums:
			positions.append(self.man.get_body_position(b))

		# Calculate the composite center of mass for the individual.
		return utilities.calc_3d_composite_com(positions, self.body_masses)

	def calc_velocity(self,com_1,com_2):
		""" Calculate the velocity between two centers of mass. """
		return utilities.euclidean_distance_3d(com_2,com_1)/self.ts
