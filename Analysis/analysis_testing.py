"""
	Unit tests to ensure that the genomes are serialized and deserialized correctly.  Modifications to the base classes 
	could cause incorrect translation in the future.
"""

import math
import unittest

import moi_analysis


class AngleTests(unittest.TestCase):
	""" Test the angle calculation triangulation across many different degress.

	Specifically focus on testing each of the four quadrants.
	"""

	def test0(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[1,0]), 0., places=6, msg=None, delta=None)

	def test45(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[1,1]), math.pi/4., places=6, msg=None, delta=None)

	def test60(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[0.5,math.sqrt(3.)/2.]), math.pi/3., places=6, msg=None, delta=None)	

	def test90(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[0,1]), math.pi/2., places=6, msg=None, delta=None)

	def test120(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[-0.5,math.sqrt(3.)/2.]), 2.*math.pi/3., places=6, msg=None, delta=None)	

	def test180(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[-1,0]), math.pi, places=6, msg=None, delta=None)	

	def test225(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[-1,-1]), 5.*math.pi/4., places=6, msg=None, delta=None)	

	def test270(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[0,-1]), 3.*math.pi/2., places=6, msg=None, delta=None)	

	def test300(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[0.5,-math.sqrt(3.)/2.]), 5.*math.pi/3., places=6, msg=None, delta=None)	

	def test315(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[1,-1]), 2.*math.pi-math.pi/4., places=6, msg=None, delta=None)

	# Relax places here since we're converting from degrees to radians introducing more floating point rounding issues.
	# Test the four quadrants with non-normal values.
	def test20(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[0.940,0.342]), 20.*(math.pi/180.), places=2, msg=None, delta=None)

	def test107(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[-0.292,0.956]), 107.*(math.pi/180.), places=2, msg=None, delta=None)

	def test263(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[-0.122,-0.993]), 263.*(math.pi/180.), places=2, msg=None, delta=None)	

	def test341(self):
		self.assertAlmostEqual(moi_analysis.calc_2d_angle([0,0],[0.946,-0.326]), 341.*(math.pi/180.), places=2, msg=None, delta=None)	

class AngVelTests(unittest.TestCase):
	""" Test the calculation of the angular velocity with specific tests. """

	def testForwardNoRefMovement(self):
		""" Test forward velocity without the reference point moving. 

		Testing starting from 180 deg to 270 deg over four steps.  30 deg increments.
		"""
		coms = [[-1,0],[-math.sqrt(3.)/2.,-0.5],[-0.5,-math.sqrt(3.)/2.],[0,-1]]
		ref_point_data = [[0,0],[0,0],[0,0],[0,0]]
		ts = 0.2

		ang_vels = moi_analysis.calc_ang_vel(coms,ts,ref_point_data)

		test_data = [0, math.pi/6./ts, math.pi/6./ts, math.pi/6./ts]
		
		for av, td in zip(ang_vels,test_data):
			self.assertAlmostEqual(av,td,places=6,msg=None,delta=None)

	def testBackwardNoRefMovement(self):
		""" Test backward velocity without the reference point moving. 

		Testing starting from 270 deg to 180 deg over four steps.  30 deg increments.
		"""
		coms = [[0,-1],[-0.5,-math.sqrt(3.)/2.],[-math.sqrt(3.)/2.,-0.5],[-1,0]]
		ref_point_data = [[0,0],[0,0],[0,0],[0,0]]
		ts = 0.2

		ang_vels = moi_analysis.calc_ang_vel(coms,ts,ref_point_data)

		test_data = [0, -math.pi/6./ts, -math.pi/6./ts, -math.pi/6./ts]
		
		for av, td in zip(ang_vels,test_data):
			self.assertAlmostEqual(av,td,places=6,msg=None,delta=None)

	def testForwardAndBackwardNoRefMovement(self):
		""" Test velocity without the reference point moving for a pendulum like motion. 

		Testing starting from 270 deg to 180 deg back to 270 over four steps.  30 deg increments.
		"""
		coms = [
			[0,-1],
			[-0.5,-math.sqrt(3.)/2.],
			[-math.sqrt(3.)/2.,-0.5],
			[-1,0],
			[-math.sqrt(3.)/2.,-0.5],
			[-0.5,-math.sqrt(3.)/2.],
			[0,-1]
		]
		ref_point_data = [[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]]
		ts = 0.2

		ang_vels = moi_analysis.calc_ang_vel(coms,ts,ref_point_data)

		test_data = [0, -math.pi/6./ts, -math.pi/6./ts, -math.pi/6./ts, math.pi/6./ts, math.pi/6./ts, math.pi/6./ts]
		
		for av, td in zip(ang_vels,test_data):
			self.assertAlmostEqual(av,td,places=6,msg=None,delta=None)

	def testRefPointRotation(self):
		""" Make reference point move but leave the "limb com" stationary. """
		coms = [[0,-1],[0,-1],[0,-1],[0,-1]]
		ref_point_data = [[0,0],[1,0],[2,0],[3,0]]
		ts = 0.2

		ang_vels = moi_analysis.calc_ang_vel(coms,ts,ref_point_data)

		test_data = [0, -math.pi/4./ts, -math.radians(18.434)/ts, -math.radians(8.131)/ts]

		for av, td in zip(ang_vels,test_data):
			self.assertAlmostEqual(av,td,places=2,msg=None,delta=None)

	def testRefPointChangeNoMovement(self):
		""" Test for reference point moving, but "limb com" stationary with respect to ref point. """
		coms = [[0,-1],[1,-1],[2,-1],[3,-1]]
		ref_point_data = [[0,0],[1,0],[2,0],[3,0]]
		ts = 0.2

		ang_vels = moi_analysis.calc_ang_vel(coms,ts,ref_point_data)

		test_data = [0., 0., 0., 0.]

		for av, td in zip(ang_vels,test_data):
			self.assertAlmostEqual(av,td,places=6,msg=None,delta=None)		
			
def main():
	unittest.main()

if __name__ == '__main__':
	main()