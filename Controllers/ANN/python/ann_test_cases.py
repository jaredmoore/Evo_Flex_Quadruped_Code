"""
	Test cases for the Python ANN wrapper.
"""

from ann_wrap import ANN, Basic_Evolve_ANN
import time

# Test Case 1: Load a ANN with 2 inputs, 1 hidden, and 1 output. (No Connections Yet)
new_ann = ANN(2,1,1)

print("Passed Test 1: ANN Created")

###############################################################################################################

# Test Case 2: Create 2 inputs mapped to one output.
# 2 connections from input to output, weight .5
new_ann = ANN(2,0,1,c_src=[0,1],c_trg=[2,2],c_wts=[.5,.5])

test_act = new_ann.activate([1.,1.])
if test_act[0] != 0.7310585786300049:
	print("Failed Test 2: Values not equal. Got: "+str(test_act[0])+" Expected: "+str(0.7310585786300049))
else:
	print("Passed Test 2: Simple ANN Activation")

###############################################################################################################

# Test Case 3: Create 2 inputs mapped a hidden then to one output.
# 2 connections from input to hidden, weight .5
# 1 connection from hidden to output, weight .25
new_ann = ANN(2,1,1,c_src=[0,1,2],c_trg=[2,2,3],c_wts=[.5,.5,.25])

# Step twice due to the inclusion of a hidden neuron!
test_act = new_ann.activate([1.,1.])
test_act = new_ann.activate([1.,1.])
if test_act[0] != 0.5455643997353379:
	print("Failed Test 3: Values not equal. Got: "+str(test_act[0])+" Expected: "+str(0.5455643997353379))
else:
	print("Passed Test 3: Simple ANN Activation with Hidden Neuron")

###############################################################################################################

# Test Case 4: Create an ANN, activate it, record the output, then create a new ANN from the previous string.
# Ensure that the outputs are the same.
new_ann = ANN(2,1,1,c_src=[0,1,2],c_trg=[2,2,3],c_wts=[.5,.5,.25])

# Step twice due to the inclusion of a hidden neuron!
test_act_0 = new_ann.activate([1.,1.])
test_act_0 = new_ann.activate([1.,1.])

new_ann_2 = ANN(ann_str=str(new_ann))
# Step twice due to the inclusion of a hidden neuron!
test_act_1 = new_ann_2.activate([1.,1.])
test_act_1 = new_ann_2.activate([1.,1.])

if test_act_0 != test_act_1:
	print("Failed Test 4: Values are not equal.  Test_0: "+str(test_act_0)+" Test_1: "+str(test_act_1))
else:
	print("Passed Test 4: Print out ANN and reconstruct from string.")

new_ann = ANN(6,0,6,c_src=[0,1,2,3,4,5,0,1,2,3,4,5],
					c_trg=[6,7,8,9,10,11,7,8,9,10,11,6],
					c_wts=[.5 for i in xrange(12)])

###############################################################################################################

# Test Case 5: Check to see if we can add a node successfully.
new_ann = ANN(1,0,1,c_src=[0],c_trg=[1],c_wts=[.5])

# Add a node to the network.
Basic_Evolve_ANN.add_node(new_ann)

ann_str = str(new_ann).split(":")

if(ann_str[3][0] == '1' and ann_str[5][0] == '2'):
	print("Passed Test 5: Add node to ANN with connections.")
else:
	print("Failed Test 5: "+str(new_ann))

###############################################################################################################

# Test Case 6: Create an ANN, activate it, record the output, then create a new ANN from the previous string, 
# mutate it and activate.  The outputs shold differ.
new_ann = ANN(2,1,1,c_src=[0,1,2],c_trg=[2,2,3],c_wts=[.5,.5,.25])

# Step twice due to the inclusion of a hidden neuron!
test_act_0 = new_ann.activate([1.,1.])
test_act_0 = new_ann.activate([1.,1.])

new_ann_2 = ANN(ann_str=str(new_ann))
Basic_Evolve_ANN.mutate_weight(new_ann_2)
# Step twice due to the inclusion of a hidden neuron!
test_act_1 = new_ann_2.activate([1.,1.])
test_act_1 = new_ann_2.activate([1.,1.])

if test_act_0 == test_act_1:
	print("Failed Test 6: Values are equal.")
else:
	print("Passed Test 6: Mutate Weight in Neural Network")