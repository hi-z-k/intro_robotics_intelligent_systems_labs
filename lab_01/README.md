**Program:** BSc in Software Engineering

**Course:** Introduction to Robotics and Intelligent Systems

**Lecturer:** Mohammed Sraj (MSc AI)

**Lab Assistant:** Mohammed Sraj (MSc AI)

**Academic year:** 2026

# Lab 1: ROS 2 and Custom Robot Simulation

Lab material for the first lab session of **Introduction to Robotics and Intelligent Systems**, a
course in the BSc in Software Engineering at the School of Information Technology and Engineering
(SiTE), Addis Ababa Institute of Technology, Addis Ababa University.

## What the session covers

The session takes you from the basic ideas of ROS 2 to a simulated robot that you program yourself. It
has three parts.

1. **ROS 2 concepts on turtlesim.** You work through the official ROS 2 beginner tutorials, on the
   command line tools and on the client libraries, using turtlesim as the tutorials do. This part
   introduces nodes, topics, services, parameters, actions, launch files, workspaces and packages.
   Use the Python version of each tutorial. The tutorials are listed on the ROS 2 documentation site
   for [Humble](https://docs.ros.org/en/humble/Tutorials.html), the ROS 2 version this course uses.
2. **A robot of your own in Gazebo.** You build the packages in this folder and follow the
   [diffdrive_bot README](diffdrive_bot/README.md). It shows the same ideas on a robot model: a URDF
   description, simulation in Gazebo, the TF tree, and Python nodes that talk to each other with a
   custom message, a service and an action.
3. **Exercise.** In a project folder of your own, with your copy of the lab packages, you add a
   depth camera and an IMU to the robot's URDF, then write your own packages for the robot, from a
   simple node up to an action client. You hand in this folder as a GitHub repository. The tasks are
   in [EXERCISE.md](EXERCISE.md).

By the end of the session you should be able to create a ROS 2 workspace and packages, describe a
robot in URDF and simulate it in Gazebo, inspect a running system with the `ros2` tools, RViz and the
TF tools, and write Python nodes that use topics, parameters, services and actions with interface
types of your own.

## What is in this folder

| Package | What it is |
|---------|------------|
| [diffdrive_bot](diffdrive_bot) | A two-wheeled differential-drive robot with a lidar and a camera, the Gazebo world it drives in, launch files for RViz and Gazebo, and the Python nodes that drive it |
| [lab_interfaces](lab_interfaces) | The message, service and action types the nodes use: `ObstacleInfo.msg`, `SetSpeed.srv` and `DriveDistance.action` |

The interface types have a package of their own, as is usual in ROS 2, so that any package, including
the ones you write in the exercise, can use them.

## Requirements

- Ubuntu 22.04 with ROS 2 Humble
- Gazebo Harmonic with its ROS 2 packages (`ros-humble-ros-gzharmonic`)

The [diffdrive_bot README](diffdrive_bot/README.md) lists the packages to install and how.

## Getting started

First install the packages listed under "What you need" in the
[diffdrive_bot README](diffdrive_bot/README.md#what-you-need). Then clone the repository into the
`src` folder of a ROS 2 workspace and build this lab's packages:

```bash
source /opt/ros/humble/setup.bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/berito/intro_robotics_intelligent_systems_labs.git
cd ~/ros2_ws
colcon build --symlink-install --packages-up-to diffdrive_bot
source install/setup.bash
```

Then continue with Step 2 of the [diffdrive_bot README](diffdrive_bot/README.md).

## License

The packages are released under the MIT license; see [LICENSE](../LICENSE).

## Reflection

Making the robot turn precisely 90 degrees was the most challenging aspect of this lab. Subtracting the start angle produced incorrect results because the odometry angle jumps from 180 to -180 when the robot turns past its back. I added the tiny angle adjustments in between each update to address this. The node became caught in the loop and was unable to read odometry data, which caused the robot to freeze while rotating. This was resolved with a multi-threaded executor. Additionally, until I granted it display access, Gazebo would not open from my Linux container. Because odometry drifts, I would include the IMU the next time.
