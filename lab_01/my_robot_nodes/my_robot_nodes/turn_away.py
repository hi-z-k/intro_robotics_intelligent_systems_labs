#!/usr/bin/env python3
"""turn_away: drive forward and turn away from obstacles (exercise steps 2-5).

Subscribes  /obstacle          lab_interfaces/msg/ObstacleInfo
Publishes   /cmd_vel           geometry_msgs/msg/Twist
            /robot_status      my_robot_interfaces/msg/RobotStatus
Services    /turn_away_enable  std_srvs/srv/SetBool
            /set_turn_speed    my_robot_interfaces/srv/SetTurnSpeed
Parameters  forward_speed  0.2 m/s    read on every message, so changes apply at once
            turn_speed     0.5 rad/s
            max_turn_speed 1.5 rad/s  upper bound accepted for turn_speed
            start_enabled  false      the node idles until /turn_away_enable(true)
            invert_turn    false      set true if your robot turns towards obstacles
"""

import rclpy
from geometry_msgs.msg import Twist
from rcl_interfaces.msg import SetParametersResult
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_srvs.srv import SetBool

from lab_interfaces.msg import ObstacleInfo
from my_robot_interfaces.msg import RobotStatus
from my_robot_interfaces.srv import SetTurnSpeed


class TurnAway(Node):

    def __init__(self):
        super().__init__("turn_away")
        self.declare_parameter("forward_speed", 0.2)
        self.declare_parameter("turn_speed", 0.5)
        self.declare_parameter("max_turn_speed", 1.5)
        self.declare_parameter("start_enabled", False)
        self.declare_parameter("invert_turn", False)

        self.enabled = bool(self.get_parameter("start_enabled").value)
        self.last_distance = 0.0
        self.add_on_set_parameters_callback(self.on_parameters)

        self.cmd_vel_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.status_pub = self.create_publisher(RobotStatus, "robot_status", 10)
        self.create_subscription(ObstacleInfo, "obstacle", self.on_obstacle, 10)
        self.create_service(SetBool, "turn_away_enable", self.on_enable)
        self.create_service(SetTurnSpeed, "set_turn_speed", self.on_set_turn_speed)

        self.get_logger().info(
            "turn_away ready, driving is " + ("ON" if self.enabled else "OFF (call /turn_away_enable)"))

    def turn_speed_ok(self, value):
        return 0.0 < value <= self.get_parameter("max_turn_speed").value

    def publish_status(self, state):
        status = RobotStatus()
        status.state = state
        status.obstacle_distance = self.last_distance
        self.status_pub.publish(status)

    def on_parameters(self, params):
        for p in params:
            if p.name == "turn_speed" and not self.turn_speed_ok(p.value):
                return SetParametersResult(
                    successful=False, reason="turn_speed must be > 0 and <= max_turn_speed")
            if p.name == "forward_speed" and p.value < 0.0:
                return SetParametersResult(successful=False, reason="forward_speed must be >= 0")
        return SetParametersResult(successful=True)

    def on_obstacle(self, msg: ObstacleInfo):
        self.last_distance = float(msg.distance)
        if not self.enabled:
            self.publish_status("stopped")
            return

        twist = Twist()
        if msg.too_close:
            turn = self.get_parameter("turn_speed").value
            # angle > 0: obstacle on the left, so turn right (negative yaw rate)
            away = -turn if msg.angle > 0.0 else turn
            if self.get_parameter("invert_turn").value:
                away = -away
            twist.angular.z = away
            state = "turning"
        else:
            twist.linear.x = self.get_parameter("forward_speed").value
            state = "forward"
        self.cmd_vel_pub.publish(twist)
        self.publish_status(state)

    def on_enable(self, request, response):
        self.enabled = bool(request.data)
        if not self.enabled:
            self.cmd_vel_pub.publish(Twist())  # zero velocity so robot really stops
            self.publish_status("stopped")
        response.success = True
        response.message = "turn_away enabled" if self.enabled else "turn_away stopped"
        self.get_logger().info(response.message)
        return response

    def on_set_turn_speed(self, request, response):
        max_turn = self.get_parameter("max_turn_speed").value
        if not self.turn_speed_ok(request.turn_speed):
            response.success = False
            response.message = f"turn_speed must be > 0 and <= {max_turn:.2f} rad/s"
        else:
            self.set_parameters([Parameter("turn_speed", Parameter.Type.DOUBLE, float(request.turn_speed))])
            response.success = True
            response.message = f"turn_speed set to {request.turn_speed:.2f} rad/s"
        self.get_logger().info(response.message)
        return response


def main():
    rclpy.init()
    node = TurnAway()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
