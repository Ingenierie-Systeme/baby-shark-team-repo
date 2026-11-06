#!/usr/bin/env python3
"""
Node rc_to_servos : pilotage manuel des servos avec la télécommande.

Un interrupteur (CH_MODE) choisit le mode :
  - valeur <= MODE_THRESHOLD : MANUEL -> ce node publie sur /output/servos
  - valeur >  MODE_THRESHOLD : AUTO   -> ce node ne publie rien, c'est le
                                         node control qui pilote

Perte de la télécommande (plus de trame depuis TIMEOUT) : failsafe,
servos au neutre, quel que soit le mode.
"""
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray

CH_SERVO1 = 3   # à adapter : canal du throttle 1 (nageoire) THROTTLE A DROITE
CH_SERVO2 = 2   # à adapter : canal du throttle 2 (masse) ELEVATION A GAUCHE
CH_MODE = 7      # même canal que CH_ENABLE dans control.py Il s agit du bouton TRN de la telecommande. pour passer de telecommande à automatique
MODE_THRESHOLD = 0   # > seuil = AUTO
#quand on pousse le curseur c est la telecommande qui a le controle
DEADBAND = 0.03
TIMEOUT = 0.5    # s sans trame RC -> position neutre

# Position de chaque servo dans /output/servos
IDX_MASSE = 0
IDX_NAGEOIRE = 1


class RcToServos(Node):
    def __init__(self):
        super().__init__("rc_to_servos")
        self.pub = self.create_publisher(Float32MultiArray, "/output/servos", 10)
        self.create_subscription(Float32MultiArray, "/input/rc", self.rc_cb, 10)
        self.last_rx = time.time()
        self.auto = False
        self.create_timer(0.1, self.watchdog)

    def publish(self, u1, u2):
        msg = Float32MultiArray()
        msg.data = [float(u1), float(u2)]  # [servo1, servo2]
        self.pub.publish(msg)

    def rc_cb(self, msg):
        self.last_rx = time.time()

        auto = msg.data[CH_MODE] > MODE_THRESHOLD
        if auto != self.auto:
            self.auto = auto
            self.get_logger().info("Mode AUTO" if auto else "Mode TELECOMMANDE")

        if self.auto:
            return   # le node control pilote les servos

        s1 = msg.data[CH_SERVO1]
        s2 = msg.data[CH_SERVO2]
        s1 = 0.0 if abs(s1) < DEADBAND else s1
        s2 = 0.0 if abs(s2) < DEADBAND else s2
        self.publish(s1, s2)

    def watchdog(self):
        # Failsafe : radio perdue -> neutre, même en mode auto
        if time.time() - self.last_rx > TIMEOUT:
            self.publish(0.0, 0.0)


def main():
    rclpy.init()
    node = RcToServos()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()