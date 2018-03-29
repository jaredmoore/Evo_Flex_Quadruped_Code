"""
	This package provides a method to calculate the moment of inertia for a robot.

	Testing suite accompanying this package is analysis_testing.py.
"""

import math
import os

def calc_2d_moi(ref_point,com,mass):
	""" Calculate the moment of inertia for a body considering it as a point mass at the COM.

	Assumes that x and y are of interest.  (Indices 0 and 1)

	Formula:

	I = md^2 (m is mass, d is distance from axis to com)

	Args:
		ref_point: reference point to get the radius from
		com: center of mass of the body
		mass: mass of the body

	Returns:
		MOI from the ref point to com.
	"""

	# Get the euclidean distance (2d from the reference point to the center of mass)
	d = math.sqrt((ref_point[0]-com[0])**2+(ref_point[1]-com[1])**2)

	return mass * d**2

def calc_2d_composite_com(coms, masses):
	""" Calculate the composite center of mass for a group of centers of mass. 

	Assumes that x and y are of interest.  (Indices 0 and 1)

	Formula:

	com_x = sum(body_x*body_mass)/total_limb_mass (Repeat for each axis)

	Args:
		coms: centers of mass
		masses: masses of each body

	Returns:
		tuple of the composite com location and total mass
	"""

	# Calculate the total mass of the bodies.
	total_mass = sum(masses)

	# Calculate the x location
	com_x = sum([c[0]*mass for c,mass in zip(coms,masses)])/total_mass

	# Calculate the y location
	com_y = sum([c[1]*mass for c,mass in zip(coms,masses)])/total_mass

	return ([com_x,com_y],total_mass)

def calc_2d_angle(ref_point,com_point):
	""" Calculate the angle between the reference point and the com_point.

	Coordinate frame assumes 0 degrees to be positive x direction, 90 deg up, 180 neg x, 270 down

	Args:
		ref_point: base of rotation
		com_point: location of the center of mass.

	Returns:
		angle in radians

	Test Suite:
		class AngleTests
	"""
	x = math.fabs(ref_point[0] - com_point[0])
	y = math.fabs(ref_point[1] - com_point[1])

	# Test for tangent cases
	if x == 0:
		if ref_point[1] > com_point[1]:
			return 3.*math.pi/2.
		else:
			return math.pi/2.
	elif y == 0:
		if ref_point[0] > com_point[0]:
			return math.pi
		else:
			return 0.

	h = math.sqrt(x**2.+y**2.)

	# Determine domain so that we get a value between 0 and 360.
	# Don't care about quadrant 1 (already calculating for that.)
	angle = math.asin(y/h)
	if com_point[0] > ref_point[0]: # Positive X
		if com_point[1] < ref_point[1]: # Negative Y
			# Quadrant 4
			angle = 2.*math.pi - angle
	else: # Negative X
		if com_point[1] > ref_point[1]: # Positive Y
			# Quadrant 2
			angle = math.pi - angle
		else:
			# Quadrant 3
			angle = math.pi + angle
	return angle

def calc_ang_vel(coms,ts,ref_point_data):
	""" Calculate the angular velocity of a center of mass at each timestep.

	Args:
		coms: centers of mass for each timestep
		ts: timestep used in simulation
		ref_point_data: location of the reference point per timestep

	Returns:
		list of the angular velocities

	Test Suite:
		class AngVelTests
	"""

	# Create list of angular velocities
	# Initialize with zero as the body starts with a 0 velocity.
	ang_vels = [0]

	# Keep track of the previous angle of the center of mass with 0 being vertical. 
	# Initialize with the starting angle.
	prev_angle = calc_2d_angle(ref_point_data[0],coms[0])

	for i in range(1,len(coms)):
		# Calculate the current angle of the COM from vertical about the reference point.
		cur_angle = calc_2d_angle(ref_point_data[i],coms[i])

		# Calculate the angular velocity.
		ang_vels.append((cur_angle-prev_angle)/ts)

		# Set the previous angle to the current angle.
		prev_angle = cur_angle

	return ang_vels

class MOIAnalysis(object):

	def __init__(self,man,ref_body_key,ref_loc_coordinates,body_groups,ts):
		""" Initialize the Analysis package. 

		Args:
			man: ODEManager object containing the simulation.
			ref_body_key: body number of the ODE object we will be using for the reference point
			ref_loc_coordinates: offset from the ref_body COM which we will calculate the MOI from
			body_groups: the groups to calculate composite MOI from {'group_name':[body ids] for each group}
			ts: timestep between updates
		"""
		self.man = man

		# Timestep of the simulation
		self.ts = ts

		# Group individual components into their composite groups.
		# Ex: Rear Right Leg, Rear Left Leg, Tail, Torso
		# Format: { 'group_name': [body keys]}
		self.composite_groups = body_groups

		# Store the reference point.
		# Format: [body_number, [x,y,z]]
		# x,y,z are local coordinates from body's center.
		self.ref_point = [ref_body_key, ref_loc_coordinates]

		# Store the reference point position at each timestep.
		# Format: [[x,y,z] for each timestep]
		self.ref_point_data = []

		# Store the COM data for each body at each timestep.
		# Format: [ {'group_name':[{body_num:[x,y,z]}] for each group }  for each timestep]
		self.com_data = []

		# Store the composite MOI per each group.
		# Format: [ [{'group':composite_moi} for each group] for each timestep]
		self.group_composite_moi = []

		# Store the composite COM per each group.
		# Format: [ [{'group':composite_com} for each group] for each timestep]
		self.group_composite_com = []

		# Store the angular momentum data for each group.
		self.ang_mom = {}

	def add_timestep(self):
		""" Add the data for the various components for a given timestep. """
		
		# Get the reference point's location in world coordinates.
		self.ref_point_data.append(self.man.get_rel_position(self.ref_point[0],self.ref_point[1]))

		# Get the position of the center of each body being monitored.
		timestep_com_data = {}
		for group,v in self.composite_groups.iteritems():
			group_com_data = {}
			for i in v:
				group_com_data[i] = self.man.get_position(i)
			timestep_com_data[group] = group_com_data
		self.com_data.append(timestep_com_data)

	def process_data(self):
		""" Process the collected information. """

		# Loop through each timestep and calculate the MOI for each component group.
		for ts,rp in zip(self.com_data,self.ref_point_data):
			timestep_group_composite_moi = {}
			timestep_group_composite_com = {}

			# Loop through each group and calculate its composite COM.
			for g,b_data in ts.iteritems():
				composite_moi = []
				composite_com = []
				for b_id,pos in b_data.iteritems():
					body_mass = self.man.get_mass(b_id)
					composite_moi.append(calc_2d_moi(rp,pos,body_mass))
					composite_com.append([pos,body_mass])
				timestep_group_composite_moi[g] = sum(composite_moi)
				composite_com = zip(*composite_com)
				timestep_group_composite_com[g] = calc_2d_composite_com(composite_com[0],composite_com[1])
			self.group_composite_moi.append(timestep_group_composite_moi)
			self.group_composite_com.append(timestep_group_composite_com)
		
		# Translate the data into a form suitable for angular velocity calculation.
		groups = []
		for k,v in self.group_composite_com[0].iteritems():
			groups.append(k)

		# Composite MOI
		mois = {g:[] for g in groups}
		for ts in self.group_composite_moi:
			for g,moi_data in ts.iteritems():
				mois[g].append(moi_data)

		# Center of Mass
		coms = {g:[] for g in groups}
		masses = {g:[] for g in groups}
		for ts in self.group_composite_com:  # Loop through each timestep.
			for g,com_data in ts.iteritems():
				coms[g].append(com_data[0])
				masses[g].append(com_data[1])

		# Calculate the angular velocity for each component group.
		# Change in MOI over time or does this need to be COM change?
		ang_vels = {g:[] for g in groups}
		for g,vals in coms.iteritems():
			ang_vels[g] = calc_ang_vel(vals,self.ts,self.ref_point_data)

		# Calculate the angular momentum for each component group. 
		# angular_momentum = angular_velocity * limb_moi
		self.ang_mom = {g:[] for g in groups}
		for (g,ang_vel),(g_0,gmoi) in zip(ang_vels.iteritems(),mois.iteritems()):
			for av, moi in zip(ang_vel,gmoi):
				self.ang_mom[g].append(av*moi)

	def write_data(self,outpath):
		""" Write the collected data to a file. 

		Args:
			outpath: output path for the files
		"""

		# Write out the reference point data.
		with open(outpath+"reference_point_data.dat","w") as f:
			f.write("Time,Ref_Point_X,Ref_Point_Y,Ref_Point_Z\n")

			# Loop through the timesteps data.
			for i,loc in enumerate(self.ref_point_data):
				elapsed_time = i*self.ts
				f.write(str(elapsed_time)+","+str(loc[0])+","+str(loc[1])+","+str(loc[2])+"\n")

		# Write out the aggregated COM data. 
		# Format: Time, Body, COM_X, COM_Y, Mass
		with open(outpath+"composite_com_data.dat","w") as f:
			f.write("Time,Body,COM_X,COM_Y,Mass\n")

			# Loop through each timestep's data.
			for i,ts in enumerate(self.group_composite_com):
				elapsed_time = i*self.ts
				for g,vals in ts.iteritems():
					f.write(str(elapsed_time)+","+str(g)+","+str(vals[0][0])+","+str(vals[0][1])+","+str(vals[1])+"\n")

		# Write out the angular momentum data.
		# Format: Time, Body, Ang_Mom
		with open(outpath+"angular_mom_data.dat","w") as f:
			f.write("Time,Body,Ang_Mom\n")

			# Loop through each group.
			for g,vals in self.ang_mom.iteritems():
				for i,v in enumerate(vals):
					elapsed_time = i*self.ts
					f.write(str(elapsed_time)+","+str(g)+","+str(v)+"\n")

