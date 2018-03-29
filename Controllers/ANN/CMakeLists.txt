
cmake_minimum_required(VERSION 2.6)
project(ANN_CPP_PYTHON)

# 
# Setup variables
# set: Set a CMAKE variable to a given value.
# --> set(<variable> <value> [[CACHE <type> <docstring> [FORCE]] | PARENT_SCOPE])
# 
set(PACKAGE_VERSION 0.1)
set(EXECUTABLE_OUTPUT_PATH ${PROJECT_SOURCE_DIR}/bin)
# SET(LIBRARY_OUTPUT_PATH ${PROJECT_SOURCE_DIR}/lib)

# 
# Add subdirectories
# add_subdirectory: Add a subdirectory to the build.
# --> add_subdirectory(source_dir [binary_dir] [EXCLUDE_FROM_ALL])
# 
add_subdirectory(src)
add_subdirectory(python)
add_subdirectory(tests)


# 
# Header search paths
# include_directories: Add include directories to the build.
# --> include_directories([AFTER|BEFORE] [SYSTEM] dir1 dir2 ...)
# 
include_directories(src)


# 
# Library search paths
# link_directories: Specify directories in which the linker will look for libraries.
# --> link_directories(directory1 directory2 ...)
# find_library: Find a library.
# --> find_library(<VAR> name1 [path1 path2 ...])
# 


# 
# Add an executable
# add_executable: Add an executable to the project using the specified source files.
# --> add_executable(<name> [WIN32] [MACOSX_BUNDLE] [EXCLUDE_FROM_ALL]
#                        source1 source2 ... sourceN)
# 


# 
# Link libraries
# target_link_libraries: Link a target to given libraries.
# --> target_link_libraries(<target> [lib1 [lib2 [...]]]
#                        [[debug|optimized|general] <lib>] ...)
# 



