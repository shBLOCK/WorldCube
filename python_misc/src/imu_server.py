import json
import queue
import threading
import time
import socket

import serial as pyserial
import struct
from spatium import *

def read_wit_normal_packet(serial: pyserial.Serial):
    while True:
        if serial.read(1) != b"\x55":
            continue
        flag = serial.read(1)[0]
        data = serial.read(8)
        checksum = serial.read(1)[0]
        if (0x55 + flag + sum(data)) & 0xFF != checksum:
            continue
        return flag, data

packet_queue = queue.Queue(maxsize=200)

def imu_thread_main(imu_serial: pyserial.Serial):
    while True:
        try:
            if not imu_serial.is_open:
                imu_serial.open()

            imu_flag, imu_data = read_wit_normal_packet(imu_serial)
            if imu_flag == 89: # quaternion
                quat = Vec4(*struct.unpack("<hhhh", imu_data)) / 32768
                try:
                    packet_queue.put_nowait(json.dumps({"x": quat.x, "y": quat.y, "z": quat.z, "w": quat.w}))
                except queue.Full:
                    pass

        except pyserial.SerialException as e:
            print(f"Serial Exception: {e}")
            imu_serial.close()
            time.sleep(1)
            continue


def main():
    imu_thread = threading.Thread(target=imu_thread_main, args=[pyserial.Serial("COM14", 921600)], daemon=True)
    imu_thread.start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 30002))
        print("Server started")
        while True:
            sock.listen()
            conn, addr = sock.accept()
            with conn:
                print(f"Accepted client: {addr}")
                while True:
                    try:
                        conn.sendall((packet_queue.get() + "\n").encode())
                    except OSError as e:
                        print(f"Failed to send packet: {e}")
                        break

if __name__ == "__main__":
    main()
