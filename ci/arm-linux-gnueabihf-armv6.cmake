# PU2PNY-V2 TEST-3: ARMv6 hard-float toolchain (one binary runs Pi Zero W + Pi 4).
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_C_COMPILER arm-linux-gnueabihf-gcc)
set(CMAKE_C_FLAGS_INIT "-march=armv6 -marm -mfpu=vfp -mfloat-abi=hard")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
