#!/usr/bin/env python3
import cv2
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, CompressedImage


class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')

        # Paramètres modifiables au lancement (ros2 run ... --ros-args -p device:=1)
        self.declare_parameter('device', 0)          # /dev/video0
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 15.0)
        self.declare_parameter('publish_compressed', True)
        self.declare_parameter('publish_raw', False)   # l'image brute sature le WiFi

        device = self.get_parameter('device').value
        width = self.get_parameter('width').value
        height = self.get_parameter('height').value
        fps = self.get_parameter('fps').value
        self.publish_compressed = self.get_parameter('publish_compressed').value
        self.publish_raw = self.get_parameter('publish_raw').value

        # CAP_V4L2 = backend Linux, plus fiable sur Raspberry Pi
        self.cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
        # MJPG permet d'avoir de meilleurs fps en USB
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not self.cap.isOpened():
            self.get_logger().error(f'Impossible d\'ouvrir la caméra {device}')
        else:
            self.get_logger().info(f'Caméra {device} ouverte ({width}x{height} @ {fps} fps)')

        self.pub_image = self.create_publisher(
            Image, 'camera/image_raw', qos_profile_sensor_data)
        self.pub_compressed = self.create_publisher(
            CompressedImage, 'camera/image_raw/compressed', qos_profile_sensor_data)

        self.timer = self.create_timer(1.0 / fps, self.timer_callback)

    def timer_callback(self):
        ok, frame = self.cap.read()
        if not ok:
            self.get_logger().warning('Lecture de la caméra échouée')
            return

        stamp = self.get_clock().now().to_msg()

        header_frame_id = 'camera'

        if self.publish_raw:
            # Conversion manuelle OpenCV -> sensor_msgs/Image (sans cv_bridge)
            msg = Image()
            msg.header.stamp = stamp
            msg.header.frame_id = header_frame_id
            msg.height, msg.width = frame.shape[:2]
            msg.encoding = 'bgr8'
            msg.is_bigendian = 0
            msg.step = frame.shape[1] * 3
            msg.data = frame.tobytes()
            self.pub_image.publish(msg)

        if self.publish_compressed:
            ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                cmsg = CompressedImage()
                cmsg.header.stamp = stamp
                cmsg.header.frame_id = header_frame_id
                cmsg.format = 'jpeg'
                cmsg.data = buf.tobytes()
                self.pub_compressed.publish(cmsg)

    def destroy_node(self):
        if self.cap.isOpened():
            self.cap.release()
        super().destroy_node()


def main():
    rclpy.init()
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()