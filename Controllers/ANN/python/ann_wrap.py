"""
	Wrap the Python Interface to the underlying ANN code written in C in a convenient class format amenable to working with in Python.
"""

import random

from cffi_code import *

class ANN(object):
	""" Class that provides basic ANN functionality. 

	Object variables:
		genome: dictionary containing information about the stats of the network
				(number of neurons, type, etc), neurons, and connections
		ann: instantation of the neural network
	"""

	def __init__(self,num_inp=0,num_hid=0,num_out=0,c_src=[],c_trg=[],c_wts=[],wt_range=1.,ann_str="",out_range=[-1.,1.]):
		""" Initializer for the class. 

		Args:
			num_inp: number of inputs to the ANN
			num_hid: initial number of hidden neurons in the ANN
			num_out: number of outputs for the ANN
			c_src: list containing the source neurons for connections
			c_trg: list containing the target neurons for connections
			c_wts: list containing the weights for connections
			wt_range: absolute value for the maximum/minimum weights
			ann_str: string containing the definition for a neural network.
		"""

		self.genome = {"stats":{},"neurons":{},"connections":{}}
		self.ann = None

		self.genome['stats']['weight_range'] = wt_range
		self.genome['stats']['low_output'] = out_range[0]
		self.genome['stats']['high_output'] = out_range[1]
		self.genome['stats']['outputs_range'] = out_range[1] - out_range[0]

		# Check to see if we should be loading the network from a string.
		if ann_str:
			self.parse_ANN_string(ann_str)
		else:
			# Check to ensure that the number of src, trg and wts are the same.
			if len(c_src) != len(c_trg) or len(c_src) != len(c_trg) or len(c_trg) != len(c_wts):
				raise ValueError("c_src, c_trg, and c_wts not equal length!")

			# Setup the genome.
			self.construct_genome(num_inp,num_hid,num_out,c_src,c_trg,c_wts)

	def __str__(self):
		""" To string method for the ann class. """
		out_str = "<ANN>"

		# Parse the stats associated with the network.
		out_str += "<stats>"
		for key,val in self.genome['stats'].iteritems():
			out_str += str(key)+":"+str(val)+";"
		out_str += "</stats>"

		# Parse the neurons in the network
		out_str += "<neurons>"
		for key,val in self.genome['neurons'].iteritems():
			out_str += str(key)+":"+str(val)+";"
		out_str += "</neurons>"

		# Parse the connections in the network.
		out_str += "<connections>"
		for key,val in self.genome['connections'].iteritems():
			out_str += str(key)+":"+str(val)+";"
		out_str += "</connections>"

		out_str += "</ANN>"

		return out_str

	def parse_ANN_string(self,ann_str):
		""" Parse the given stringe to construct the genome for the ANN. 

		Args:
			ann_str: string containing the ANN
		"""

		# Tokenize the string.
		tokenized = ann_str.split("><")[1:4]

		# Strip the tags and split by category.
		parsed_stats_str = (tokenized[0][6:len(tokenized[0])-7]).split(";")[:-1]
		parsed_neurons_str = (tokenized[1][8:len(tokenized[1])-9]).split(";")[:-1]
		parsed_connections_str = (tokenized[2][12:len(tokenized[2])-13]).split(";")[:-1]

		# Parse the stats string.
		for elem in parsed_stats_str:
			split_elem = elem.split(":")
			self.genome['stats'][split_elem[0]] = int(float(split_elem[1]))

		# Check the stats to make sure that the necessary values are there.
		keys = ['num_neurons','num_connections','num_inp','num_hid','num_out']
		for k in keys:
			if k not in self.genome['stats']:
				raise KeyError("Key "+str(k)+" is missing from the parsed ANN string. "+ann_str)

		# Parse the neuron string.
		for elem in parsed_neurons_str:
			split_elem = elem.split(":")
			self.genome['neurons'][int(split_elem[0])] = split_elem[1]

		# Parse the connections string:
		for elem in parsed_connections_str:
			split_elem = elem.split(":")
			self.genome['connections'][split_elem[0]] = float(split_elem[1])

	def construct_genome(self,num_inp,num_hid,num_out,c_src,c_trg,c_wts):
		""" Construct a dictionary containing information about the ANN.

		Args:
			num_inp: number of inputs to the ANN
			num_hid: initial number of hidden neurons in the ANN
			num_out: number of outputs for the ANN
			c_src: list containing the source neurons for connections
			c_trg: list containing the target neurons for connections
			c_wts: list containing the weights for connections
			wt_range: absolute value for the maximum/minimum weights
		Returns:
			dictionary containing dictionaries for: 
											stats: information about network size, number of connections, etc
											neurons: neuron id/information(type)
											connections: list of tuples(src_id,trg_id,weight)
		"""

		# Fill out the statistics about the network.
		self.genome['stats']['num_neurons'] = num_inp+num_hid+num_out
		self.genome['stats']['num_connections'] = len(c_src)
		self.genome['stats']['num_inp'] = num_inp
		self.genome['stats']['num_hid'] = num_hid
		self.genome['stats']['num_out'] = num_out

		# Create the entries for the neuron numbers.
		for i in xrange(num_inp): # Inputs
			self.genome['neurons'][i] = "input"

		for i in xrange(num_inp,num_inp+num_hid): # Hidden Neurons
			self.genome['neurons'][i] = "hidden"

		for i in xrange(num_inp+num_hid,num_inp+num_hid+num_out): # Outputs
			self.genome['neurons'][i] = "output"

		# Create the entries for the connections.
		for i in xrange(len(c_src)):
			self.genome['connections'][str(c_src[i])+"->"+str(c_trg[i])] = c_wts[i]

	def initialize_ANN(self):
		""" Initialize the actual artificial neural network. """

		# Decode the connections.
		c_src, c_trg, c_wts = [], [], []
		for key,val in self.genome['connections'].iteritems():
			link = key.split("->")
			c_src.append(int(link[0]))
			c_trg.append(int(link[1]))
			c_wts.append(val)

		self.ann = libann.new_ANN(ffi.new("int[]", [	self.genome['stats']['num_inp'],
														self.genome['stats']['num_hid'],
														self.genome['stats']['num_out']]), 
			ffi.new("int[]", [i for i in c_src]),
			ffi.new("int[]", [i for i in c_trg]), 
			ffi.new("double[]", [i for i in c_wts]), len(c_src))

	def activate(self,inputs):
		""" Activate the neural network by providing the inputs and returning the output.

		Args:
			inputs: list containing the inputs to activate with.
		Returns:
			a list containing the outputs from the ANN
		"""

		# Ensure that the ANN has been initialized before we activate it.
		if not self.ann:
			self.initialize_ANN()

		inputs = ffi.new("double["+str(self.genome['stats']['num_inp'])+"]", inputs)
		outputs = ffi.new("double["+str(self.genome['stats']['num_out'])+"]")
		
		libann.setInput_ANN(self.ann, inputs, self.genome['stats']['num_inp'])
		libann.activate_ANN(self.ann)
		libann.getOutput_ANN(self.ann, outputs, self.genome['stats']['num_out'])

		# Scale the outputs based on ranges.
		outputs = list(outputs)
		for i in range(len(outputs)):
			outputs[i] = self.genome['stats']['low_output']+(self.genome['stats']['outputs_range']*outputs[i])

		return list(outputs)

class Basic_Evolve_ANN(object):
	""" Class that implements static methods to perform evolutionary development of an ANN. """

	@staticmethod
	def add_node(ann):
		""" Add a new node to a neural network. 

		Currently, the method places a node between two currently connected nodes.

		Args:
			ann: artificial neural network to add a node to.
		"""

		if (len(ann.genome['connections']) == 0):
			return

		# Insert the node into the ANN's dictionary of neurons.
		new_id = ann.genome['stats']['num_neurons']
		ann.genome['neurons'][new_id] = 'hidden'

		# Select a connection randomly from the ANN's set of connections to split and insert the node.
		conn_to_split = random.choice(list(ann.genome['connections'].keys()))

		con_nodes = conn_to_split.split("->")
		ann.genome['connections'][con_nodes[0]+"->"+str(new_id)] = 1.0 # float("{0:.4f}".format(-ann.genome['stats']['weight_range'] + (random.random()*(2.*ann.genome['stats']['weight_range']))))
		ann.genome['connections'][str(new_id)+"->"+con_nodes[1]] = ann.genome['connections'][conn_to_split] # float("{0:.4f}".format(-ann.genome['stats']['weight_range'] + (random.random()*(2.*ann.genome['stats']['weight_range']))))

		# Remove the split connection.
		del ann.genome['connections'][conn_to_split]

		# Update the stats of the ANN
		ann.genome['stats']['num_neurons'] += 1
		ann.genome['stats']['num_connections'] += 1
		ann.genome['stats']['num_hid'] += 1

	@staticmethod
	def remove_node(ann):
		""" Remove a node from the neural network. 

		Remove the node and all associated connections.  Only hidden nodes are eligible to be removed!

		Args:
			ann: artificial neural network to add a node to.
		"""

		# Don't remove inputs or outputs
		if ann.genome['stats']['num_hid'] < 1:
			return

		# Pick a hidden node randomly to remove from the network.
		neuron_id = random.randint(ann.genome['stats']['num_inp']+ann.genome['stats']['num_out'],ann.genome['stats']['num_neurons']-1)

		# Find what connections neuron_id is a part of and delete them.
		con_adj = 0 # Keep track of how many are removed.
		for k in ann.genome['connections'].keys():
			spl = k.split("->")
			if neuron_id == int(spl[0]) or neuron_id == int(spl[1]):
				del ann.genome['connections'][k]
				con_adj += 1
		ann.genome['stats']['num_connections'] -= con_adj

		# Move the last neuron to the removed neuron's id to maintain continuity in numbering
		if neuron_id != ann.genome['stats']['num_neurons']-1:
			last_id = ann.genome['stats']['num_neurons']-1

			# Find what connections last_id is a part of and rekey them.
			for k in ann.genome['connections'].keys():
				spl = k.split("->")
				if last_id == int(spl[0]):
					ann.genome['connections'][str(neuron_id)+"->"+spl[1]] = ann.genome['connections'][k]
					del ann.genome['connections'][k]			
				elif last_id == int(spl[1]):
					ann.genome['connections'][spl[0]+"->"+str(neuron_id)] = ann.genome['connections'][k]
					del ann.genome['connections'][k]			

		# Adjust the number of neuron count.
		ann.genome['stats']['num_neurons'] -= 1
		ann.genome['stats']['num_hid'] -= 1

	@staticmethod
	def mutate_weights(ann,mut_prob=0.05):
		""" Go through all weights and mutate one if it's under the threshold for mutation. 

		Args:
			ann: artificial neural network to perturb.
			mut_prob: probability to mutate a weight
		"""
		for conn in ann.genome['connections'].keys():
			if random.random() < mut_prob:
				Basic_Evolve_ANN.mutate_ann_weight(ann,conn)

	@staticmethod
	def mutate_weight(ann):
		""" Mutate a randomly selected weight in a neural network with a new random value.

		Args:
			ann: artificial neural network to perturb.
		"""
		#ann.genome['connections'][random.choice(list(ann.genome['connections'].keys()))] = float("{0:.4f}".format(-ann.genome['stats']['weight_range'] + (random.random()*(2.*ann.genome['stats']['weight_range']))))
		connection = random.choice(list(ann.genome['connections'].keys()))
		Basic_Evolve_ANN.mutate_ann_weight(ann,connection)
		# cur_weight = ann.genome['connections'][connection]

		# # Decide whether to greatly alter the weight or just perturb it slightly.
		# if random.random() <= 0.1:
		# 	ann.genome['connections'][connection] = float("{0:.4f}".format(-ann.genome['stats']['weight_range'] + (random.random()*(2.*ann.genome['stats']['weight_range']))))
		# else:
		# 	new_weight = random.gauss(cur_weight,0.1)

		# 	# Make sure it's within the bounds.
		# 	if new_weight < -ann.genome['stats']['weight_range']:
		# 		new_weight = -ann.genome['stats']['weight_range']
		# 	elif new_weight > ann.genome['stats']['weight_range']:
		# 		new_weight = ann.genome['stats']['weight_range']
		# 	ann.genome['connections'][connection] = float("{0:.4f}".format(new_weight))

	@staticmethod
	def mutate_ann_weight(ann,connection):
		""" Mutate a given connection in an ann.

		Args:
			ann: artificial neural network
			connection: key identifying the connection to mutate
		"""
		cur_weight = ann.genome['connections'][connection]

		# Decide whether to greatly alter the weight or just perturb it slightly.
		if random.random() <= 0.1:
			ann.genome['connections'][connection] = float("{0:.4f}".format(-ann.genome['stats']['weight_range'] + (random.random()*(2.*ann.genome['stats']['weight_range']))))
		else:
			new_weight = random.gauss(cur_weight,0.1)

			# Make sure it's within the bounds.
			if new_weight < -ann.genome['stats']['weight_range']:
				new_weight = -ann.genome['stats']['weight_range']
			elif new_weight > ann.genome['stats']['weight_range']:
				new_weight = ann.genome['stats']['weight_range']
			ann.genome['connections'][connection] = float("{0:.4f}".format(new_weight))

	@staticmethod
	def add_link(ann):
		""" Add a link between two neurons.  

		Cannot connect to an input neuron.

		Args:
			ann: artificial neural network to perturb.
		"""
		src = random.randint(0,ann.genome['stats']['num_neurons']-1)
		dst = random.randint(ann.genome['stats']['num_inp'],ann.genome['stats']['num_neurons']-1)

		# Don't add a second connection if one already exists!
		max_tries = 5
		while str(src)+"->"+str(dst) in ann.genome['connections'] and max_tries > 0:
			src = random.randint(0,ann.genome['stats']['num_neurons']-1)
			dst = random.randint(ann.genome['stats']['num_inp'],ann.genome['stats']['num_neurons']-1)
			max_tries -= 1

		# If we couldn't find a new pairing, give up.
		if max_tries == 0:
			return

		ann.genome['connections'][str(src)+"->"+str(dst)] = float("{0:.4f}".format(-ann.genome['stats']['weight_range'] + (random.random()*(2.*ann.genome['stats']['weight_range']))))
		
		# Adjust stats of the network.
		ann.genome['stats']['num_connections'] += 1

	@staticmethod
	def remove_link(ann):
		""" Remove a link between two neurons.  

		Args:
			ann: artificial neural network to perturb.
		"""
		# Don't try on an empty network!
		if len(ann.genome['connections']) < 1:
			return

		del ann.genome['connections'][random.choice(list(ann.genome['connections'].keys()))]

		ann.genome['stats']['num_connections'] -= 1