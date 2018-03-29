"""
	Handle calling the default FFI required loading code for the ANN so it doesn't clutter up other modules.
"""

from cffi import FFI
ffi = FFI()

c_interface_str = ""
with open("../../Controllers/ANN/src/ann.h","r") as f:
	reading = False
	for line in f:
		if line.strip() == "typedef void ANN_C;":
			reading = True
			c_interface_str += line.strip()
		if reading and line.strip() != "}":
			c_interface_str += line.strip()
		else:
			reading = False

ffi.cdef(c_interface_str)

libann = ffi.dlopen('../../Controllers/ANN/bin/libann.dylib')