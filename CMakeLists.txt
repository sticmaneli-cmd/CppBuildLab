cmake_minimum_required(VERSION 3.20)
project(CppBuildLab
    VERSION 1.0.0
    LANGUAGES CXX
    DESCRIPTION "CppBuildLab - CI/CD laboratory with Jenkins, Docker and C++"
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" OR CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wpedantic -Werror")
endif()

option(BUILD_TESTS "Build tests" ON)
option(USE_SDL3 "Enable SDL3 support" OFF)

add_executable(calculator_app
    src/main.cpp
    src/calculator.cpp
)

target_include_directories(calculator_app PRIVATE src)

if(USE_SDL3)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(SDL3 REQUIRED sdl3>=3.2.0)
    target_include_directories(calculator_app PRIVATE ${SDL3_INCLUDE_DIRS})
    target_link_directories(calculator_app PRIVATE ${SDL3_LIBRARY_DIRS})
    target_link_libraries(calculator_app ${SDL3_LIBRARIES})
    target_compile_definitions(calculator_app PRIVATE HAVE_SDL3)
endif()

if(BUILD_TESTS)
    include(FetchContent)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG        v1.14.0
    )
    FetchContent_MakeAvailable(googletest)

    enable_testing()

    add_executable(calculator_tests
        tests/calculator_tests.cpp
        src/calculator.cpp
    )

    target_include_directories(calculator_tests PRIVATE src)
    target_link_libraries(calculator_tests GTest::gtest GTest::gtest_main)

    add_test(NAME calculator_tests COMMAND calculator_tests)
endif()

install(TARGETS calculator_app
    RUNTIME DESTINATION bin
)