cmake_minimum_required(VERSION 3.10)

project(dr_crypto_profiler C CXX)

find_package(DynamoRIO REQUIRED)

add_library(dr_crypto_profiler SHARED
    dr_crypto_profiler.c
)

configure_DynamoRIO_client(dr_crypto_profiler)

use_DynamoRIO_extension(dr_crypto_profiler drmgr)
