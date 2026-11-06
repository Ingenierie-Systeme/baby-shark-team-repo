#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32MultiArray

from math import sin, pi


class ControlNode(Node):

    def __init__(self):
        super().__init__("control")

        ### Paramètres (modifiables au lancement avec --ros-args -p freq:=2.0)
        self.declare_parameter("freq", 5.0)          # fréquence de l'oscillation (Hz)
        self.declare_parameter("amplitude", 1.0)     # entre 0 et 1
        self.declare_parameter("rate", 50.0)         # fréquence de publication (Hz)

        self.freq = self.get_parameter("freq").value
        self.amplitude = self.get_parameter("amplitude").value
        rate = self.get_parameter("rate").value

        ### Publisher
        self.pwm_pub = self.create_publisher(
            Float32MultiArray,
            "/output/servos",
            10)

        ### Temps de départ
        self.t0 = self.get_clock().now()

        ### Timer de commande
        self.timer = self.create_timer(
            1 / rate,
            self.control_loop)

    def control_loop(self):
        # Temps écoulé depuis le démarrage, en secondes
        t = (self.get_clock().now() - self.t0).nanoseconds * 1e-9

        # Oscillation sinusoïdale entre -amplitude et +amplitude
        u = self.amplitude * sin(2 * pi * self.freq * t)

        msg = Float32MultiArray()
        msg.data = [u, u]          # [servo1, servo2]
        self.pwm_pub.publish(msg)

    def stop_servos(self):
        # Remet les servos au neutre
        msg = Float32MultiArray()
        msg.data = [0.0, 0.0]
        self.pwm_pub.publish(msg)


def main():
    rclpy.init()
    node = ControlNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_servos()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()