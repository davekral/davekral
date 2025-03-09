cmake_minimum_required(VERSION 3.16)
project(rocket_qt LANGUAGES CXX)

list(APPEND CMAKE_PREFIX_PATH "C:/Users/xXKra/Qt/Qt/6.5.2/msvc2019_64")

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Network)

qt_standard_project_setup()

qt_add_executable(rocket_qt
    main.cpp
    MyWidget.cpp MyWidget.h
)

set_target_properties(rocket_qt PROPERTIES
    WIN32_EXECUTABLE TRUE
    MACOSX_BUNDLE TRUE
)

target_link_libraries(rocket_qt PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    Qt6::Network
)
