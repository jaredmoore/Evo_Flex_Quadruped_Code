
# 
# Create a library for this subdirectory
# add_library: Add a library to the project using the specified source files.
# --> add_library(<name> [STATIC | SHARED | MODULE] [EXCLUDE_FROM_ALL]
#              source1 source2 ... sourceN)
# 
add_library(ann SHARED ann.cpp)
