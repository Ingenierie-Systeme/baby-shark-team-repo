#!/usr/bin/env python3

import sys
import argparse
from math import sin, pi, tanh

import rclpy
from rclpy.node import Node
from rclpy.utilities import remove_ros_args

from std_msgs.msg import Float32MultiArray
from std_msgs.msg import Float32

"""
Usage :
    python3 control.py --mission stop
    python3 control.py --mission forward
    python3 control.py --mission control_profondeur

Missions :
 - stop               : remet les servos au neutre
 - forward            : oscillation sinusoidale sur la nageoire, masse au neutre
 - control_profondeur : oscillation sur la nageoire + maintien de depth_target avec la masse

Parametres (ex. --ros-args -p freq:=2.0 -p kp:=0.3) :
 freq, amplitude, rate, depth_target, kp, u2_max, depth_timeout

Ce node pilote toujours les servos (mode auto uniquement) : il publie en
continu sur /output/servos des le lancement. Ne pas lancer en meme temps
que rc_to_servos, les deux publieraient sur le meme topic.
"""

MISSIONS = ["stop", "control_profondeur", "forward","bouger_masse"]

# Position de chaque servo dans /output/servos
IDX_MASSE = 0
IDX_NAGEOIRE = 1

# +1 : masse vers l'arriere (+1) = le robot remonte
# -1 : a inverser si le robot s'enfonce quand il devrait remonter
MASSE_SIGN = 1.0


class ControlNode(Node):

    def __init__(self, mission):
        super().__init__("control")

        # Parametres
        self.declare_parameter("freq", 5.0)            # frequence de l'oscillation (Hz)
        self.declare_parameter("amplitude", 1.0)       # entre 0 et 1
        self.declare_parameter("rate", 50.0)           # frequence de publication (Hz)
        self.declare_parameter("depth_target", 1.0)    # profondeur souhaitee (m)
        self.declare_parameter("kp", 1.0)              # gain proportionnel ds tanh
        self.declare_parameter("Kp", 1.0)              # gain proportionnel = amplitude 
        self.declare_parameter("u2_max", 1.0)          # limite de la commande de masse (0 a 1)
        self.declare_parameter("depth_timeout", 1.0)   # delai max sans mesure de profondeur (s)

        self.freq = self.get_parameter("freq").value
        self.amplitude = self.get_parameter("amplitude").value
        rate = self.get_parameter("rate").value
        self.depth_target = self.get_parameter("depth_target").value
        self.kp = self.get_parameter("kp").value
        self.Kp = self.get_parameter("Kp").value
        self.u2_max = self.get_parameter("u2_max").value
        self.depth_timeout = self.get_parameter("depth_timeout").value

        self.depth = None
        self.last_depth_time = None

        # Publisher
        self.pwm_pub = self.create_publisher(Float32MultiArray, "/output/servos", 10)

        # Subscriber
        self.depth_sub = self.create_subscription(
            Float32, "/input/depth", self.depth_callback, 10)

        # Temps de depart
        self.t0 = self.get_clock().now()

        # Mission en cours
        self.missions = {
            "stop": self.stop_servos,
            "control_profondeur": self.control_depth,
            "forward": self.forward,
            "bouger_masse": self.bouger_masse,
        }
        self.mission_en_cours = self.missions[mission]

        # Timer de commande (cree en dernier, une fois tout initialise)
        self.timer = self.create_timer(1.0 / rate, self.control_loop)

        self.get_logger().info(f"Mission '{mission}' lancee (mode auto).")

    def control_loop(self):
        self.mission_en_cours()

    # Utilitaires

    def elapsed(self):
        return (self.get_clock().now() - self.t0).nanoseconds * 1e-9

    def oscillation(self):
        """Sinusoide entre -amplitude et +amplitude."""
        return self.amplitude * sin(2 * pi * self.freq * self.elapsed())

    def publish(self, u_nageoire, u_masse):
        data = [0.0, 0.0]
        data[IDX_NAGEOIRE] = float(u_nageoire)
        data[IDX_MASSE] = float(u_masse)
        msg = Float32MultiArray()
        msg.data = data
        self.pwm_pub.publish(msg)

    # Missions
    def bouger_masse(self):
        self.publish(0.0, self.oscillation())


    def control_depth(self):
        u_nageoire = self.oscillation()
        u_masse=0.0

        """if self.depth is None:
            u_masse=0
        else:
            u_masse = self.Kp* tanh(self.kp * (self.depth - self.depth_target))"""

        self.publish(u_nageoire, u_masse)

    def forward(self):
        self.publish(self.oscillation(), 0.0)

    def stop_servos(self):
        """Remet les servos au neutre."""
        self.publish(0.0, 0.0)

    # Callback

    def depth_callback(self, msg):
        self.depth = msg.data
        self.last_depth_time = self.get_clock().now()


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mission",
        required=True,
        choices=MISSIONS,
        help="Mission a executer",
    )

    # On retire les arguments ROS (--ros-args ...) avant le parsing argparse
    parsed_args = parser.parse_args(remove_ros_args(sys.argv)[1:])

    rclpy.init(args=args)
    node = ControlNode(parsed_args.mission)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Servos au neutre a l'arret, sans planter si le contexte est deja ferme
        try:
            node.stop_servos()
        except Exception:
            pass
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()