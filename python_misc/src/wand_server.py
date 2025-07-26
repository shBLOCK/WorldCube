import socket

import serial as pyserial

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        serial = pyserial.Serial("COM27", 115200)

        sock.bind(("127.0.0.1", 30003))
        print("Server started")
        while True:
            sock.listen()
            conn, addr = sock.accept()
            with conn:
                print(f"Accepted client: {addr}")
                while True:
                    try:
                        conn.sendall(serial.read_all())
                    except OSError as e:
                        print(f"Failed to send packet: {e}")
                        break

if __name__ == '__main__':
    main()
