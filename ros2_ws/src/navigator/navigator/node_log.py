#!/usr/bin/env python3
"""
Node log : enregistre dans un fichier CSV les dernières valeurs de tous les topics.

Une ligne est écrite à fréquence fixe (LOG_RATE_HZ) avec la dernière valeur
reçue de chaque topic. Une case vide signifie qu'aucune valeur n'a encore été
reçue pour ce topic.

Topics écoutés :
  /input/imu      (Imu)               accélération + vitesse angulaire brutes
  /input/mag      (MagneticField)     magnétomètre brut
  /input/depth    (Float32)           profondeur (m)
  /input/rc       (Float32MultiArray) 8 canaux de la télécommande
  /state/attitude (Imu)               quaternion de l'orientation
  /state/euler    (Vector3Stamped)    roulis, tangage, cap (deg)
  /output/servos  (Float32MultiArray) commandes envoyées aux servos
"""

import csv
import os
import time
from datetime import datetime

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Imu, MagneticField
from std_msgs.msg import Float32, Float32MultiArray
from geometry_msgs.msg import Vector3Stamped


LOG_RATE_HZ = 20.0                      # lignes par seconde
LOG_DIR = "/home"
FLUSH_PERIOD = 1.0                      # s, écriture sur disque
N_RC = 8                                # nombre de canaux RC

COLUMNS = (
    ["t", "depth",
     "roll", "pitch", "yaw",
     "qw", "qx", "qy", "qz",
     "ax", "ay", "az",
     "gx", "gy", "gz",
     "mx", "my", "mz",
     "servo1", "servo2"]
    + [f"rc{i}" for i in range(N_RC)]
)


class LogNode(Node):

    def __init__(self):
        super().__init__("log")

        # Dernières valeurs reçues (None = rien reçu)
        self.v = {name: None for name in COLUMNS if name != "t"}

        # Fichier CSV
        os.makedirs(LOG_DIR, exist_ok=True)
        name = datetime.now().strftime("log_%Y%m%d_%H%M%S.csv")
        self.path = os.path.join(LOG_DIR, name)
        self.file = open(self.path, "w", newline="")
        self.writer = csv.writer(self.file)
        self.writer.writerow(COLUMNS)

        self.t0 = time.time()

        # Abonnements
        self.create_subscription(Imu, "/input/imu", self.imu_cb, 10)
        self.create_subscription(MagneticField, "/input/mag", self.mag_cb, 10)
        self.create_subscription(Float32, "/input/depth", self.depth_cb, 10)
        self.create_subscription(Float32MultiArray, "/input/rc", self.rc_cb, 10)
        self.create_subscription(Imu, "/state/attitude", self.att_cb, 10)
        self.create_subscription(Vector3Stamped, "/state/euler", self.euler_cb, 10)
        self.create_subscription(Float32MultiArray, "/output/servos", self.servo_cb, 10)

        # Écriture périodique
        self.create_timer(1.0 / LOG_RATE_HZ, self.write_row)
        self.create_timer(FLUSH_PERIOD, self.file.flush)

        self.get_logger().info(f"Logging dans {self.path}")

    # ------------------------------------------------------------------
    def imu_cb(self, msg):
        a, g = msg.linear_acceleration, msg.angular_velocity
        self.v.update(ax=a.x, ay=a.y, az=a.z, gx=g.x, gy=g.y, gz=g.z)

    def mag_cb(self, msg):
        m = msg.magnetic_field
        self.v.update(mx=m.x, my=m.y, mz=m.z)

    def depth_cb(self, msg):
        self.v["depth"] = msg.data

    def rc_cb(self, msg):
        for i in range(min(N_RC, len(msg.data))):
            self.v[f"rc{i}"] = msg.data[i]

    def att_cb(self, msg):
        q = msg.orientation
        self.v.update(qw=q.w, qx=q.x, qy=q.y, qz=q.z)

    def euler_cb(self, msg):
        self.v.update(roll=msg.vector.x, pitch=msg.vector.y, yaw=msg.vector.z)

    def servo_cb(self, msg):
        if len(msg.data) >= 2:
            self.v.update(servo1=msg.data[0], servo2=msg.data[1])

    # ------------------------------------------------------------------
    def write_row(self):
        row = [f"{time.time() - self.t0:.3f}"]
        for name in COLUMNS[1:]:
            val = self.v[name]
            row.append("" if val is None else f"{val:.6g}")
        self.writer.writerow(row)

    def close(self):
        try:
            self.file.flush()
            self.file.close()
        except Exception:
            pass


def main():
    rclpy.init()
    node = LogNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()