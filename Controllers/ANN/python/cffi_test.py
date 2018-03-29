
from cffi_code import *

#test = ffi.new("ANN_C *")

new_ann = libann.new_ANN(ffi.new("int[]", [3, 1, 4]), [], [], [], 0)
#libann.fullyConnectFF_ANN(new_ann)
#libann.activate(new_ann)
#print(libann.getOutput_ANN(new_ann))

#new_ann = libann.new_ANN_FromFile(b"../build/ann_file.ann")
libann.print_ANN(new_ann)

inputs = [1, 1, 1]
for a in range(3):

    outputs = ffi.new("double[4]")
    libann.getOutput_ANN(new_ann, outputs, 4)

    inputs = ffi.new("double[3]", [1.0, 1.0, outputs[0]])
    libann.setInput_ANN(new_ann, inputs, 3)

    libann.activate_ANN(new_ann)

    outputs = ffi.new("double[4]")
    libann.getOutput_ANN(new_ann, outputs, 4)


    output_str = "Outputs: "
    output_str += str(outputs[0])
    output_str += " " + str(outputs[1])
    output_str += " " + str(outputs[2])
    output_str += " " + str(outputs[3])
    print(output_str)


# 1) Declare types and functions
# --- ffi.cdef(source)
# + cannot contain #include...
# + can use single cdef to declare functions from multiple libraries


# 2a) Loading libraries
# --- ffi.dlopen(libpath, [flags])
# + use this or ffi.verify depending on application
# + call functions declared by ffi.cdef()
# + read/write global variables
# + can load multiple libraries
# + path can be full path (or it will be in standard location)
# + man dlopen --> flags, etc.
# + if libpath==None, load standard C library
# + no checking is done --> recommend ffi.verity()


# 2b) Verification step
# --- ffi.verify(source, tmpdir=.., ext_package=.., modulename=.., **kwargs)
# + verify that ffi signatures compile
# + callfunctions and access global variables
# + compiled JIT
# + source : should at least contain necessary #include
# + 


# Pointer or array type initialization
# --- ffi.new(ctype, [initializer])
# + ffi.NULL
# + dereference : p[0]
# + access      : p.x


# C equivalent casting
# --- ffi.cast("type", value)

# Includes typedefs, structs, unions and enum types in another FFI instance
# --- ffi.include(other_ffi)

# Error value from C call
# --- ffi.errno

# Return Python string from cdata
# --- ffi.string(cdata, [maxlen])
# + decode strings for P3: b'some string'

# Return buffer object that references raw C data pointed to by cdata
# --- ffi.buffer(cdata, [size])
# + useful for reading/writing without copying (i.e. file.write, file.readinto)

# Return type of C cdata instance
# --- ffi.typeof("C type" or cdata object)
# + ffi.typeof(ptr) is ffi.typeof("foo_t*")

# Return size of argument in bytes
# --- ffi.sizeof("C type" or cdata object)

# Return alignment of C type
# --- ffi.alignof("C type")

# Return offset within struct of given field
# --- ffi.offsetof("C struct type", "fieldname")

# Return string representation fo given C type
# --- ffi.getctype("C type" or <ctype>, extra="")
# + ffi.getctype(ffi.typeof(x), "*")

# Return new cdata object that points to same data
# --- ffi.gc(cdata, destructor)
# + ptr = ffi.gc(lib.malloc(42), lib.free)

# Return non-NULL cdata type of void *
# --- ffi.new_handle(python_object)

# Return address of cdata type
# --- ffi.addressof(cdata, field=None)

# Python callback function
# --- ffi.callback("int(int, int)", myfunc, error=42)
# + decorator: @ffi.callback(...)









