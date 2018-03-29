"""
	Unit tests to ensure that the genomes are serialized and deserialized correctly.  Modifications to the base classes 
	could cause incorrect translation in the future.
"""

import unittest

import quadruped_utils


class MutationOperatorTests(unittest.TestCase):

	def testZeroRange(self):
		self.failIf(quadruped_utils.mutate_value(10,10,10) != 10)

	def testUpperOutOfBoundsStart(self):
		self.failIf(quadruped_utils.mutate_value(20,0,10) != 10)

	def testLowerOutOfBoundsStart(self):
		self.failIf(quadruped_utils.mutate_value(-10,0,10) != 0)	


def GenomeSerialization(genome_class):
	""" Test the serialization and deserialization of the provided class.

	Args:
		genome_class: what type of genome we are testing.

	Returns:
		Boolean whether the serialization produced the same or dissimilar genomes.
	"""
	test_genome = genome_class()
	orig_genome = str(test_genome)
	serialized_genome = test_genome.serialize()
	test_genome.deserialize(serialized_genome)
	processed_genome = str(test_genome)
	return (orig_genome != processed_genome)


class GenomeSerializationTests(unittest.TestCase):

	def testControlEvolve(self):
		self.failIf(GenomeSerialization(quadruped_utils.ControlEvolve))

	def testControlForceEvolve(self):
		self.failIf(GenomeSerialization(quadruped_utils.ControlForceEvolve))

	def testControlForceInitZRotationEvolve(self):
		self.failIf(GenomeSerialization(quadruped_utils.ControlForceInitZRotationEvolve))

	def testControlForceInitZRotationLimbLenEvolve(self):
		self.failIf(GenomeSerialization(quadruped_utils.ControlForceInitZRotationLimbLenEvolve))	

	def testControlForceInitZRotationLimbLenJointRangeEvolve(self):
		self.failIf(GenomeSerialization(quadruped_utils.ControlForceInitZRotationLimbLenJointRangeEvolve))

	def testControlForceInitZRotationJointRangeShiftOscillatorEvolve(self):
		self.failIf(GenomeSerialization(quadruped_utils.ControlForceInitZRotationJointRangeShiftOscillatorEvolve))

	def testControlForceShiftOscillatorEvolve(self):
		self.failIf(GenomeSerialization(quadruped_utils.ControlForceShiftOscillatorEvolve))		

	def testControlForceShiftOscillatorPerJointEvolve(self):
		self.failIf(GenomeSerialization(quadruped_utils.ControlForceShiftOscillatorPerJointEvolve))	

def GenomeHeadItems(genome_class):
	""" Get the number of header items in a class. """
	gc = genome_class()
	return (len(gc.headers().split(',')),gc.genome_length())

class GenomeLengthTests(unittest.TestCase):
	""" Make sure the various genome header functions print out the correct number of items. """

	def testControlEvolve(self):
		head_len, num_genes = GenomeHeadItems(quadruped_utils.ControlEvolve)
		self.failIf(head_len != num_genes)

	def testControlForceEvolve(self):
		head_len, num_genes = GenomeHeadItems(quadruped_utils.ControlForceEvolve)
		self.failIf(head_len != num_genes)

	def testControlForceInitZRotationEvolve(self):
		head_len, num_genes = GenomeHeadItems(quadruped_utils.ControlForceInitZRotationEvolve)
		self.failIf(head_len != num_genes)

	def testControlForceInitZRotationLimbLenEvolve(self):
		head_len, num_genes = GenomeHeadItems(quadruped_utils.ControlForceInitZRotationLimbLenEvolve)
		self.failIf(head_len != num_genes)		

	def testControlForceInitZRotationLimbLenEvolve(self):
		head_len, num_genes = GenomeHeadItems(quadruped_utils.ControlForceInitZRotationLimbLenJointRangeEvolve)
		self.failIf(head_len != num_genes)

	def testControlForceInitZRotationJointRangeShiftOscillatorEvolve(self):
		head_len, num_genes = GenomeHeadItems(quadruped_utils.ControlForceInitZRotationJointRangeShiftOscillatorEvolve)
		self.failIf(head_len != num_genes)	

	def testControlForceShiftOscillatorEvolveEvolve(self):
		head_len, num_genes = GenomeHeadItems(quadruped_utils.ControlForceShiftOscillatorEvolve)
		self.failIf(head_len != num_genes)	

	def testControlForceShiftOscillatorPerJointEvolve(self):
		head_len, num_genes = GenomeHeadItems(quadruped_utils.ControlForceShiftOscillatorPerJointEvolve)
		self.failIf(head_len != num_genes)			
	

class GenomeEqualityTests(unittest.TestCase):
	""" Make sure the equality operator is overridden correctly. """

	def testControlEvolveNotEqual(self):
		genome1 = quadruped_utils.ControlEvolve()
		genome2 = quadruped_utils.ControlEvolve()
		genome1.osc_freq = 1.0
		genome2.osc_freq = 4.0
		self.failIf(genome1 == genome2)

	def testControlEvolveEqual(self):
		genome1 = quadruped_utils.ControlEvolve()
		genome2 = quadruped_utils.ControlEvolve(genome=str(genome1))
		self.failIf(not(genome1 == genome2))

	def testControlForceEvolveNotEqual(self):
		genome1 = quadruped_utils.ControlForceEvolve()
		genome2 = quadruped_utils.ControlForceEvolve()
		genome1.max_forces[0][0] = 1.0
		genome2.max_forces[0][0] = 4.0
		self.failIf(genome1 == genome2)

	def testControlForceEvolveEqual(self):
		genome1 = quadruped_utils.ControlForceEvolve()
		genome2 = quadruped_utils.ControlForceEvolve(genome=str(genome1))
		self.failIf(not(genome1 == genome2))

	def testControlForceEvolveNotEqual(self):
		genome1 = quadruped_utils.ControlForceInitZRotationEvolve()
		genome2 = quadruped_utils.ControlForceInitZRotationEvolve()
		genome1.components[2].rotations[0] = 10
		genome2.components[2].rotations[1] = 30
		self.failIf(genome1 == genome2)

	def testControlForceEvolveEqual(self):
		genome1 = quadruped_utils.ControlForceInitZRotationEvolve()
		genome2 = quadruped_utils.ControlForceInitZRotationEvolve(genome=str(genome1))
		self.failIf(not(genome1 == genome2))

	def testControlForceInitZRotationLimbLenEvolveNotEqual(self):
		genome1 = quadruped_utils.ControlForceInitZRotationLimbLenEvolve()
		genome2 = quadruped_utils.ControlForceInitZRotationLimbLenEvolve()
		genome1.components[3].lengths[0] = 10
		genome2.components[3].lengths[1] = 30
		self.failIf(genome1 == genome2)

	def testControlForceInitZRotationLimbLenEvolveEqual(self):
		genome1 = quadruped_utils.ControlForceInitZRotationLimbLenEvolve()
		genome2 = quadruped_utils.ControlForceInitZRotationLimbLenEvolve(genome=str(genome1))
		self.failIf(not(genome1 == genome2))

	def testControlForceInitZRotationLimbLenJointRangeEvolveNotEqual(self):
		genome1 = quadruped_utils.ControlForceInitZRotationLimbLenJointRangeEvolve()
		genome2 = quadruped_utils.ControlForceInitZRotationLimbLenJointRangeEvolve()
		genome1.components[4].joint_ranges[0][0] = 10
		genome2.components[4].joint_ranges[1][0] = 30
		self.failIf(genome1 == genome2)

	def testControlForceInitZRotationLimbLenJointRangeEvolveEqual(self):
		genome1 = quadruped_utils.ControlForceInitZRotationLimbLenJointRangeEvolve()
		genome2 = quadruped_utils.ControlForceInitZRotationLimbLenJointRangeEvolve(genome=str(genome1))
		self.failIf(not(genome1 == genome2))

	def testControlForceInitZRotationJointRangeShiftOscillatorEvolveNotEqual(self):
		genome1 = quadruped_utils.ControlForceInitZRotationJointRangeShiftOscillatorEvolve()
		genome2 = quadruped_utils.ControlForceInitZRotationJointRangeShiftOscillatorEvolve(genome=str(genome1))
		genome1.components[4].delta = -9.0
		genome2.components[4].delta = 0.5
		self.failIf(genome1 == genome2)

	def testControlForceInitZRotationJointRangeShiftOscillatorEvolveEqual(self):
		genome1 = quadruped_utils.ControlForceInitZRotationJointRangeShiftOscillatorEvolve()
		genome2 = quadruped_utils.ControlForceInitZRotationJointRangeShiftOscillatorEvolve(genome=str(genome1))
		self.failIf(not(genome1 == genome2))

	def testControlForceShiftOscillatorEvolveNotEqual(self):
		genome1 = quadruped_utils.ControlForceShiftOscillatorEvolve()
		genome2 = quadruped_utils.ControlForceShiftOscillatorEvolve(genome=str(genome1))
		genome1.components[2].delta = -9.0
		genome2.components[2].delta = 0.5
		self.failIf(genome1 == genome2)

	def testControlForceShiftOscillatorEvolveEvolveEqual(self):
		genome1 = quadruped_utils.ControlForceShiftOscillatorEvolve()
		genome2 = quadruped_utils.ControlForceShiftOscillatorEvolve(genome=str(genome1))
		self.failIf(not(genome1 == genome2))

	def testControlForceShiftOscillatorPerJointEvolveNotEqual(self):
		genome1 = quadruped_utils.ControlForceShiftOscillatorPerJointEvolve()
		genome2 = quadruped_utils.ControlForceShiftOscillatorPerJointEvolve(genome=str(genome1))
		genome1.components[2].deltas[0] = -9.0
		genome2.components[2].deltas[0] = 0.5
		self.failIf(genome1 == genome2)

	def testControlForceShiftOscillatorPerJointEvolveEqual(self):
		genome1 = quadruped_utils.ControlForceShiftOscillatorPerJointEvolve()
		genome2 = quadruped_utils.ControlForceShiftOscillatorPerJointEvolve(genome=str(genome1))
		self.failIf(not(genome1 == genome2))		


class GenomeMappingTests(unittest.TestCase):
	""" Check to make sure the genome is being mapped into the actual robot. """

	def testControlEvolveMapping(self):
		genome = quadruped_utils.ControlEvolve()
		self.failIf(genome.osc_freq != genome.components[0].osc_freq)

	def testControlEvolveMappingPostMutate(self):
		genome = quadruped_utils.ControlEvolve()
		genome.mutate(mut_prob=1.0)
		self.failIf(genome.osc_freq != genome.components[0].osc_freq)

	def testControlForceEvolveMapping(self):
		genome = quadruped_utils.ControlForceEvolve()
		self.failIf(genome.max_forces[0][0] != genome.components[1].max_forces[0][0])

	def testControlForceEvolveMappingPostMutate(self):
		genome = quadruped_utils.ControlForceEvolve()
		genome.mutate(mut_prob=1.0)
		self.failIf(genome.max_forces[0][0] != genome.components[1].max_forces[0][0])

	def testControlForceInitZRotationEvolveMapping(self):
		genome = quadruped_utils.ControlForceInitZRotationEvolve()
		self.failIf(genome.components[2].rotations[0] != genome.components[2].rotations[0])

	def testControlForceInitZRotationEvolvePostMutate(self):
		genome = quadruped_utils.ControlForceInitZRotationEvolve()
		genome.mutate(mut_prob=1.0)
		self.failIf(genome.components[2].rotations[0] != genome.components[2].rotations[0])

	def testControlForceInitZRotationLimbLenEvolveMapping(self):
		genome = quadruped_utils.ControlForceInitZRotationLimbLenEvolve()
		self.failIf(genome.components[3].lengths[0] != genome.components[3].lengths[0])

	def testControlForceInitZRotationLimbLenEvolvePostMutate(self):
		genome = quadruped_utils.ControlForceInitZRotationLimbLenEvolve()
		genome.mutate(mut_prob=1.0)
		self.failIf(genome.components[3].lengths[0] != genome.components[3].lengths[0])

	def testControlForceInitZRotationLimbLenEvolveMapping(self):
		genome = quadruped_utils.ControlForceInitZRotationLimbLenJointRangeEvolve()
		self.failIf(genome.joint_ranges[2][0] != genome.components[4].joint_ranges[0])

	def testControlForceInitZRotationLimbLenJointRangeEvolvePostMutate(self):
		genome = quadruped_utils.ControlForceInitZRotationLimbLenJointRangeEvolve()
		genome.mutate(mut_prob=1.0)
		self.failIf(genome.joint_ranges[2][0] != genome.components[4].joint_ranges[0])

	def testControlForceInitZRotationJointRangeShiftOscillatorEvolveMapping(self):
		genome = quadruped_utils.ControlForceInitZRotationJointRangeShiftOscillatorEvolve()
		self.failIf(genome.delta != genome.components[4].delta)

	def testControlForceInitZRotationJointRangeShiftOscillatorEvolvePostMutate(self):
		genome = quadruped_utils.ControlForceInitZRotationJointRangeShiftOscillatorEvolve()
		genome.mutate(mut_prob=1.0)
		self.failIf(genome.delta != genome.components[4].delta)

	def testControlForceShiftOscillatorPerJointEvolveMapping(self):
		genome = quadruped_utils.ControlForceShiftOscillatorPerJointEvolve()
		self.failIf(genome.deltas[0] != genome.components[2].deltas[0])

	def testControlForceShiftOscillatorPerJointEvolvePostMutate(self):
		genome = quadruped_utils.ControlForceShiftOscillatorPerJointEvolve()
		genome.mutate(mut_prob=1.0)
		self.failIf(genome.deltas[0] != genome.components[2].deltas[0])		


def main():
	unittest.main()

if __name__ == '__main__':
	main()