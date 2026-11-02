"""Start the simulation, the rotate action server and the square driver.

    ros2 launch my_robot_nodes square.launch.py side_length:=0.8
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    diffdrive_share = get_package_share_directory("diffdrive_bot")

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(diffdrive_share, "launch", "control.launch.py")),
    )

    rotate_server = Node(
        package="my_robot_nodes",
        executable="rotate_server",
        name="rotate_server",
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    square_driver = Node(
        package="my_robot_nodes",
        executable="square_driver",
        name="square_driver",
        output="screen",
        parameters=[{
            "side_length": ParameterValue(LaunchConfiguration("side_length"), value_type=float),
            "use_sim_time": True,
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "side_length", default_value="0.5", description="Side length of the square in metres"),
        simulation,
        rotate_server,
        square_driver,
    ])
