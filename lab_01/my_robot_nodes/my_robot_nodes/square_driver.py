#!/usr/bin/env python3
"""square_driver: drive a square with the /drive_distance and /rotate actions (step 7).

Parameters  side_length    0.5 m    length of each side
            server_timeout 120 s    wait timeout for action servers
            exit_when_done false    keep node alive afterwards so rqt_graph shows it
"""

import math

import rclpy
from action_msgs.msg import GoalStatus
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from lab_interfaces.action import DriveDistance
from my_robot_interfaces.action import Rotate


class SquareDriver(Node):

    def __init__(self):
        super().__init__("square_driver")
        self.declare_parameter("side_length", 0.5)
        self.declare_parameter("server_timeout", 120.0)
        self.declare_parameter("exit_when_done", False)

        self.drive_client = ActionClient(self, DriveDistance, "drive_distance")
        self.rotate_client = ActionClient(self, Rotate, "rotate")

    def run_action(self, client, goal, label):
        send_future = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future)
        handle = send_future.result()
        if handle is None or not handle.accepted:
            self.get_logger().error(f"{label}: goal rejected")
            return False
        result_future = handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        if result_future.result().status != GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().error(f"{label}: did not succeed")
            return False
        return True

    def wait_for_servers(self):
        timeout = self.get_parameter("server_timeout").value
        for client, name in ((self.drive_client, "drive_distance"), (self.rotate_client, "rotate")):
            self.get_logger().info(f"waiting for the /{name} action server...")
            if not client.wait_for_server(timeout_sec=timeout):
                self.get_logger().error(f"/{name} action server not available")
                return False
        return True

    def run_square(self):
        if not self.wait_for_servers():
            return False
        side = float(self.get_parameter("side_length").value)
        self.get_logger().info(f"driving a square, side {side:.2f} m")

        for i in range(1, 5):
            drive_goal = DriveDistance.Goal()
            drive_goal.distance = side
            if not self.run_action(self.drive_client, drive_goal, f"side {i}/4 (drive)"):
                return False

            rotate_goal = Rotate.Goal()
            rotate_goal.angle = math.pi / 2.0  # quarter turn left
            if not self.run_action(self.rotate_client, rotate_goal, f"corner {i}/4 (rotate)"):
                return False
            self.get_logger().info(f"side {i}/4 done")

        self.get_logger().info("square complete")
        return True


def main():
    rclpy.init()
    node = SquareDriver()
    try:
        node.run_square()
        if not node.get_parameter("exit_when_done").value:
            node.get_logger().info("idle (Ctrl-C to quit); rqt_graph still shows this node")
            rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
