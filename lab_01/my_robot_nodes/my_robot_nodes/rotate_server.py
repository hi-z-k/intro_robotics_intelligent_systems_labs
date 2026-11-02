#!/usr/bin/env python3
"""rotate_server: action server that turns the robot on the spot (exercise step 6).

Action      /rotate  my_robot_interfaces/action/Rotate  (angle in rad, positive = left)
Subscribes  /odom    nav_msgs/msg/Odometry              (yaw is integrated frame by frame)
Publishes   /cmd_vel geometry_msgs/msg/Twist
Parameters  turn_speed 0.5 rad/s, min_turn_speed 0.15 rad/s, odom_timeout 5 s
"""

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node

from my_robot_interfaces.action import Rotate

TOLERANCE = 0.005  # rad
LOOP_PERIOD = 0.02  # s


def yaw_from_quaternion(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def angle_difference(new, old):
    """Smallest signed difference new - old, wrapped to [-pi, pi]."""
    return math.atan2(math.sin(new - old), math.cos(new - old))


class RotateServer(Node):

    def __init__(self):
        super().__init__("rotate_server")
        self.declare_parameter("turn_speed", 0.5)
        self.declare_parameter("min_turn_speed", 0.15)
        self.declare_parameter("odom_timeout", 5.0)

        self.yaw = None
        self.busy = False
        group = ReentrantCallbackGroup()

        self.cmd_vel_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.create_subscription(Odometry, "odom", self.on_odom, 10, callback_group=group)
        self.server = ActionServer(
            self, Rotate, "rotate",
            execute_callback=self.execute,
            goal_callback=self.on_goal,
            cancel_callback=lambda _: CancelResponse.ACCEPT,
            callback_group=group,
        )
        self.get_logger().info("rotate action server ready on /rotate")

    def on_odom(self, msg: Odometry):
        self.yaw = yaw_from_quaternion(msg.pose.pose.orientation)

    def on_goal(self, goal):
        if abs(goal.angle) < 1e-3:
            self.get_logger().warn("rejecting a goal of zero angle")
            return GoalResponse.REJECT
        if self.busy:
            self.get_logger().warn("rejecting goal: already rotating")
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def stop(self):
        self.cmd_vel_pub.publish(Twist())

    def wait_for_odom(self):
        deadline = time.monotonic() + self.get_parameter("odom_timeout").value
        while self.yaw is None and rclpy.ok() and time.monotonic() < deadline:
            time.sleep(0.05)
        return self.yaw is not None

    def execute(self, goal_handle):
        self.busy = True
        try:
            return self.rotate(goal_handle)
        finally:
            self.busy = False

    def rotate(self, goal_handle):
        angle = goal_handle.request.angle
        direction = 1.0 if angle > 0.0 else -1.0
        target = abs(angle)
        cruise = self.get_parameter("turn_speed").value
        slowest = min(self.get_parameter("min_turn_speed").value, cruise)
        result = Rotate.Result()
        feedback = Rotate.Feedback()

        if not self.wait_for_odom():
            self.get_logger().error("no /odom messages received, aborting")
            goal_handle.abort()
            return result

        self.get_logger().info(f"rotating {angle:.2f} rad")
        deadline = time.monotonic() + 4.0 * target / cruise + 5.0
        last_yaw = self.yaw
        turned = 0.0
        twist = Twist()

        while rclpy.ok():
            if goal_handle.is_cancel_requested:
                self.stop()
                goal_handle.canceled()
                result.turned = float(direction * turned)
                self.get_logger().info(f"rotation canceled after {result.turned:.2f} rad")
                return result
            if time.monotonic() > deadline:
                self.stop()
                self.get_logger().error("rotation timed out, aborting")
                goal_handle.abort()
                result.turned = float(direction * turned)
                return result

            yaw = self.yaw
            turned += direction * angle_difference(yaw, last_yaw)
            last_yaw = yaw

            feedback.turned = float(direction * turned)
            goal_handle.publish_feedback(feedback)

            remaining = target - turned
            if remaining <= TOLERANCE:
                break
            twist.angular.z = direction * min(cruise, max(slowest, 2.0 * remaining))
            self.cmd_vel_pub.publish(twist)
            time.sleep(LOOP_PERIOD)

        self.stop()
        result.turned = float(direction * turned)
        if turned < target - TOLERANCE:
            goal_handle.abort()
        else:
            goal_handle.succeed()
            self.get_logger().info(f"rotation done: {result.turned:.2f} rad")
        return result


def main():
    rclpy.init()
    node = RotateServer()
    try:
        rclpy.spin(node, executor=MultiThreadedExecutor())
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
