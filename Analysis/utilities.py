"""
	Utilities for analysis calculations.
"""

import math

def calc_3d_composite_com(coms, masses):
	""" Calculate the composite center of mass for a group of centers of mass. 

	Assumes that x, y, and z are of interest.  Index 1 is vertical axis

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

	# Calculate the z location
	com_z = sum([c[2]*mass for c,mass in zip(coms,masses)])/total_mass 

	return ([com_x,com_y,com_z],total_mass)

def euclidean_distance_3d(p1,p2):
    """ Calculate the 3d Euclidean distance of two coordinates.
    
    Args:
        p1: position 1
        p2: position 2
    Returns:
        Euclidean distance between the two points.
    """
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2) 	