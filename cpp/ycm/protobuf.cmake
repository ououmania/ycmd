set(PROTOBUF_LIBRARY_NAME "libprotobuf")

if(NOT USE_SYSTEM_PROTOBUF)
  # Building the protobuf tests require gmock what is not part of a standard protobuf checkout.
  # Disable them unless they are explicitly requested from the cmake command line (when we assume
  # gmock is downloaded to the right location inside protobuf).
  option(protobuf_BUILD_TESTS "Build protobuf tests" OFF)
  option(protobuf_BUILD_SHARED_LIBS "Build Shared Libraries" OFF)
  # Disable building protobuf with zlib. Building protobuf with zlib breaks
  # the build if zlib is not installed on the system.
  include(CheckLibraryExists)
  check_library_exists(z zlibVersion "" HAVE_LIBZ)
  if(HAVE_LIBZ)
    set(protobuf_WITH_ZLIB ON CACHE BOOL "Build protobuf tests")
  endif()
  if(NOT PROTOBUF_ROOT_DIR)
    set( PROTOBUF_ROOT_DIR "${CMAKE_SOURCE_DIR}/../third_party/protobuf" )
  endif()

  set(CMAKE_POSITION_INDEPENDENT_CODE ON)
  if(EXISTS "${PROTOBUF_ROOT_DIR}/cmake/CMakeLists.txt")
    add_subdirectory(${PROTOBUF_ROOT_DIR}/cmake third_party/protobuf)
    if(TARGET ${PROTOBUF_LIBRARY_NAME})
      set(PROTOBUF_LIBRARIES ${PROTOBUF_LIBRARY_NAME})
    endif()
    if(TARGET libprotoc)
      set(PROTOBUF_PROTOC_LIBRARIES libprotoc)
    endif()
    if(TARGET protoc)
      set(PROTOBUF_PROTOC protoc)
      set(PROTOBUF_PROTOC_EXECUTABLE $<TARGET_FILE:protoc>)
    endif()
    set(PROTOBUF_INCLUDE_DIR "${PROTOBUF_ROOT_DIR}/src")
    # For well-known .proto files distributed with protobuf
    set(PROTOBUF_WELLKNOWN_INCLUDE_DIR "${PROTOBUF_ROOT_DIR}/src")
  else()
      message(WARNING "System protobuf is not used but PROTOBUF_ROOT_DIR is wrong")
  endif()
else()
  set(Protobuf_USE_STATIC_LIB ON)
  find_package(Protobuf REQUIRED )

  # {Protobuf,PROTOBUF}_FOUND is defined based on find_package type ("MODULE" vs "CONFIG").
  # For "MODULE", the case has also changed between cmake 3.5 and 3.6.
  # We use the legacy uppercase version for *_LIBRARIES AND *_INCLUDE_DIRS variables
  # as newer cmake versions provide them too for backward compatibility.
  if(Protobuf_FOUND OR PROTOBUF_FOUND)
    if(TARGET protobuf::${PROTOBUF_LIBRARY_NAME})
      set(PROTOBUF_LIBRARIES protobuf::${PROTOBUF_LIBRARY_NAME})
    else()
      set(PROTOBUF_LIBRARIES ${Protobuf_LIBRARIES})
    endif()
    if(TARGET protobuf::libprotoc)
      set(PROTOBUF_PROTOC_LIBRARIES protobuf::libprotoc)
      # extract the include dir from target's properties
      get_target_property(PROTOBUF_WELLKNOWN_INCLUDE_DIR protobuf::libprotoc INTERFACE_INCLUDE_DIRECTORIES)
    else()
      set(PROTOBUF_PROTOC_LIBRARIES ${PROTOBUF_PROTOC_LIBRARIES})
      set(PROTOBUF_WELLKNOWN_INCLUDE_DIR ${PROTOBUF_INCLUDE_DIRS})
    endif()
    if(TARGET protobuf::protoc)
      set(PROTOBUF_PROTOC protobuf::protoc)
      set(PROTOBUF_PROTOC_EXECUTABLE $<TARGET_FILE:protobuf::protoc>)
    else()
      set(PROTOBUF_PROTOC ${PROTOBUF_PROTOC_EXECUTABLE})
      set(PROTOBUF_PROTOC_EXECUTABLE ${PROTOBUF_PROTOC_EXECUTABLE})
    endif()
    set(PROTOBUF_INCLUDE_DIR ${PROTOBUF_INCLUDE_DIRS})
  endif()
endif()

function(protobuf_generate_cpp output_dir proto_dir SRCS HDRS)
  if(NOT ARGN)
    message(SEND_ERROR "Error: PROTOBUF_GENERATE_CPP() called without any proto files")
    return()
  endif()
  set(${SRCS})
  set(${HDRS})

  set(_protobuf_include_path -I ${CMAKE_CURRENT_SOURCE_DIR} -I ${PROTOBUF_WELLKNOWN_INCLUDE_DIR})
  foreach(FIL ${ARGN})
    get_filename_component(ABS_FIL ${FIL} ABSOLUTE)
    get_filename_component(FIL_WE ${FIL} NAME_WE)
    set(GENERATED_FILE_WE "${output_dir}/${FIL_WE}")
    set(SRC_FILE "${GENERATED_FILE_WE}.pb.cc")
    set(HEADER_FILE "${GENERATED_FILE_WE}.pb.h")
    list(APPEND SRCS ${SRC_FILE})
    list(APPEND HDRS ${HEADER_FILE})

    add_custom_command(
      OUTPUT "${SRC_FILE}" "${HEADER_FILE}"
      COMMAND ${PROTOBUF_PROTOC_EXECUTABLE}
      ARGS ${ABS_FIL}
           --cpp_out=${output_dir}
           --proto_path=${proto_dir}
           ${_protobuf_include_path}
      DEPENDS ${ABS_FIL} ${PROTOBUF_PROTOC} 
      WORKING_DIRECTORY ${output_dir}
      COMMENT "Running C++ protocol buffer compiler on ${ABS_FIL}"
      VERBATIM)

    set_source_files_properties("${SRC_FILE}" "${HEADER_FILE}" PROPERTIES GENERATED TRUE)
  endforeach()
  set(${SRCS} ${${SRCS}} PARENT_SCOPE)
  set(${HDRS} ${${HDRS}} PARENT_SCOPE)
endfunction()

