"""
	Wrap the Python Interface to the underlying ANN code written in C in a convenient 
	class format amenable to working with in Python.
"""

import random

from cffi_code import *

class ANN2(object):
	""" Class that provides basic ANN functionality. 

	Object variables:
		genome: dictionary containing information about the stats of the network
				(number of neurons, type, etc), neurons, and connections
		ann: instantation of the neural network
	"""

	@classmethod
	def get_ann(cls, phenotype_spec):
		""" Build an ANN from the phenotype specification sent from the NEAT genome build_phenotype method. 

		phenotype_spec has the following form:
			num_inp,num_hid,num_out,c_src,c_trg,c_wts,wt_range
		"""

		# for i in phenotype_spec:
		# 	print(i)

		return cls(num_inp=phenotype_spec[0],num_hid=phenotype_spec[1],num_out=phenotype_spec[2],\
			c_src=phenotype_spec[3],c_trg=phenotype_spec[4],c_wts=phenotype_spec[5],\
			wt_range=phenotype_spec[6],out_range=phenotype_spec[7])

	def __init__(self,num_inp=0,num_hid=0,num_out=0,c_src=[],c_trg=[],c_wts=[],wt_range=1.,out_range=[-1.,1.]):
		""" Initializer for the class. 

		Args:
			num_inp: number of inputs to the ANN
			num_hid: initial number of hidden neurons in the ANN
			num_out: number of outputs for the ANN
			c_src: list containing the source neurons for connections
			c_trg: list containing the target neurons for connections
			c_wts: list containing the weights for connections
			wt_range: absolute value for the maximum/minimum weights
		"""

		#print(num_inp,num_hid,num_out)

		self.low_output = out_range[0]
		self.high_output = out_range[1]
		self.weight_range = wt_range

		self.ann = None

		# ANN Information about the nodes and connections in the network.
		self.num_inp = num_inp
		self.num_out = num_out
		self.num_hid = num_hid

		self.conn_src = c_src
		self.conn_trg = c_trg
		self.conn_wts = c_wts

		# Check to ensure that the number of src, trg and wts are the same.
		if len(c_src) != len(c_trg) or len(c_src) != len(c_trg) or len(c_trg) != len(c_wts):
			raise ValueError("c_src, c_trg, and c_wts not equal length!")

		self.initialize_ANN()

	def __str__(self):
		""" To string method for the ann class. """
		return str(self.low_output) + " " +\
			str(self.high_output) + " " +\
			str(self.weight_range) + " " +\
			str(self.num_inp) + " " +\
			str(self.num_out) + " " +\
			str(self.num_hid) + " " +\
			str(self.conn_src) + " " +\
			str(self.conn_trg) + " " +\
			str(self.conn_wts)

	def initialize_ANN(self):
		""" Initialize the actual artificial neural network. """

		self.ann = libann.new_ANN(ffi.new("int[]", [self.num_inp, self.num_hid, self.num_out]), 
			ffi.new("int[]", [i for i in self.conn_src]),
			ffi.new("int[]", [i for i in self.conn_trg]), 
			ffi.new("double[]", [i for i in self.conn_wts]), len(self.conn_src))

	def activate(self,inp):
		""" Activate the neural network by providing the inputs and returning the output.

		Args:
			inputs: list containing the inputs to activate with.
		Returns:
			a list containing the outputs from the ANN
		"""

		# Ensure that the ANN has been initialized before we activate it.
		#if not self.ann:
		#	self.initialize_ANN()

		inputs = ffi.new("double["+str(self.num_inp)+"]", inp)
		outputs = ffi.new("double["+str(self.num_out)+"]")
		
		libann.setInput_ANN(self.ann, inputs, self.num_inp)
		libann.activate_ANN(self.ann)
		libann.getOutput_ANN(self.ann, outputs, self.num_out)

		# Scale the outputs based on ranges.
		out = list(outputs)
		for i in range(len(out)):
			out[i] = self.low_output+((self.high_output-self.low_output)*out[i])

		return out