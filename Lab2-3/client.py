import os
import socket
import threading
import time
import keyboard

TCP_SERVER_HOST = '127.0.0.1'
TCP_SERVER_PORT = 8000

UDP_SERVER_HOST = '127.0.0.1'
UDP_SERVER_PORT = 8001

BUFFER_SIZE = 1024
DIRECTORY = "client_folder/"

socket_lock = threading.Condition()
last_command_time = time.time()
global name

def main():
    global last_command_time
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((TCP_SERVER_HOST, TCP_SERVER_PORT))
    client_socket.settimeout(20)

    client_socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket_udp.settimeout(20)

    print('\nWelcome to client app!\n To input commands press button I\nSupported commands:\n\n'
          '\t1. UPLOAD – upload file to server (transmission protocol can be selected)\n'
          '\t2. DOWNLOAD – download file from server (transmission protocol can be selected)\n'
          '\t3. TIME – returns up-time of server\n'
          '\t4. ECHO – returns your string\n'
          '\t5. CHECK UPLOADS – checks the files that need to be uploaded to the server\n'
          '\t6. CHECK DOWNLOADS – checks the files that need to be downloaded from the server\n')

    global name
    try:
        name = input("Enter your client name: ")
        client_socket.sendall(name.encode())
    except KeyboardInterrupt:
        print("Client terminated by user")
        client_socket.close()
        exit(0)

    try:
        if client_socket.recv(BUFFER_SIZE) != b'OK':
            print("Some unexpected error")
            exit(0)
    except ConnectionResetError:
        print("Server has disconnected")
        return

    while True:
        try:
            current_time = time.time()
            if current_time - last_command_time > 5:
                print("Sending PING...")
                client_socket.sendall(b'PING')
                response = client_socket.recv(BUFFER_SIZE)
                if response == b'PONG':
                    print("Received PONG. Connection is active.")
                    last_command_time = time.time()
                else:
                    print("No response to PING. Server may be unreachable.")
                    break

            if keyboard.is_pressed('i'):
                command = input("\nEnter command (UPLOAD, DOWNLOAD, TIME, ECHO, EXIT): ").strip().upper()
            else:
                continue
        except KeyboardInterrupt:
            print("Client terminated by user")
            client_socket.close()
            exit(0)

        try:
            with socket_lock:
                client_socket.sendall(command.encode())
        except BrokenPipeError:
            print("Server disconnect")
            break

        if command == "UPLOAD":
            filename = input("Enter filename: ")
            protocol = input("Choose protocol (TCP, UDP): ").strip().upper()

            client_socket.sendall(protocol.encode())
            resp = client_socket.recv(BUFFER_SIZE)
            print(f'resp {resp}')
            if resp == b'OK':
                if protocol == 'TCP':
                    handle_upload_tcp(client_socket, filename)
                elif protocol == 'UDP':
                    handle_upload_udp(client_socket_udp, filename)
            else:
                print('Wrong protocol')
                continue

        elif command == "DOWNLOAD":
            filename = input("Enter filename: ")
            protocol = input("Choose protocol (TCP, UDP): ").strip().upper()

            client_socket.sendall(protocol.encode())
            resp = client_socket.recv(BUFFER_SIZE)
            if resp == b"OK":
                if protocol == 'TCP':
                    handle_download_tcp(client_socket, filename)
                elif protocol == 'UDP':
                    handle_download_udp(client_socket_udp, filename)
                else:
                    print('Wrong protocol')
                    continue

        elif command == "TIME":
            handle_time(client_socket)

        elif command == "ECHO":
            handle_echo(client_socket)

        elif command == "EXIT":
            break

        elif command == "CHECK UPLOADS":
            handle_check_uploads(client_socket)

        elif command == "CHECK DOWNLOADS":
            handle_check_downloads(client_socket)

    client_socket.close()
    client_socket_udp.close()


def handle_check_uploads(client_socket):
    try:
        server_msg = client_socket.recv(BUFFER_SIZE)
    except socket.timeout:
        print("No response from server within 20 seconds")
        return

    if server_msg != b'No pumping':
        client_socket.sendall(b'OK')
        handle_upload_tcp(client_socket, server_msg.split()[1].decode())
    else:
        print("No file to continue upload")
        return


def handle_check_downloads(client_socket):
    try:
        server_msg = client_socket.recv(BUFFER_SIZE)
    except socket.timeout:
        print("No response from server within 20 seconds")
        return

    if server_msg != b'No pumping':
        client_socket.sendall(b'OK')
        print(server_msg)
        handle_download_tcp(client_socket, server_msg.split()[1].decode())
    else:
        print("No file to continue download")
        return


def handle_upload_tcp(client_socket, filename):
    file_path = os.path.join(DIRECTORY, filename)

    if os.path.exists(file_path):
        with socket_lock:
            client_socket.sendall(filename.encode())

            with open(file_path, 'rb') as f:
                data = f.read(BUFFER_SIZE)
                while data:
                    with socket_lock:
                        client_socket.sendall(data)
                        try:
                            response = client_socket.recv(BUFFER_SIZE)
                            if response != b'OK':
                                print("Server response:", response)
                                return
                        except socket.timeout:
                            print("No response from server within 20 seconds")
                            return
                    data = f.read(BUFFER_SIZE)

            with socket_lock:
                client_socket.sendall(b'DONE')

        print(f"File '{filename}' uploaded successfully.")
    else:
        client_socket.sendall(b'BREAK')
        print(f"File {filename} doesn't exist")


def handle_download_tcp(client_socket, filename):
    with socket_lock:
        client_socket.sendall(filename.encode())

        try:
            response = client_socket.recv(BUFFER_SIZE).decode()
            print(f"response {response}")
        except socket.timeout:
            print("Server has disconnected")
            return

        if response == "OK":
            file_path = os.path.join(DIRECTORY, filename)
            with open(file_path, 'wb') as f:
                while True:

                    try:
                        data = client_socket.recv(BUFFER_SIZE)
                    except socket.timeout:
                        f.close()
                        print("Server has disconnected")
                        return

                    if not data or data == b'DONE':
                        print(data)
                        break
                    else:
                        with socket_lock:
                            client_socket.sendall(B"OK")
                        f.write(data)
            print(f"File '{filename}' downloaded successfully.")
        else:
            print(response)


def handle_upload_udp(client_socket_udp, filename):

    global name
    file_path = os.path.join(DIRECTORY, filename)

    if os.path.exists(file_path):
        client_socket_udp.sendto(f"{name},{filename}".encode(), (UDP_SERVER_HOST, UDP_SERVER_PORT))
        with open(file_path, 'rb') as f:
            seq_num = 0
            while True:
                data = f.read(BUFFER_SIZE - len(str(seq_num)) - 1)  # необходимо часть сообщения выделить на номер последовательности и разделяющую запятую
                if not data:
                    break
                packet = f"{seq_num},{data.decode()}"
                client_socket_udp.sendto(packet.encode(), (UDP_SERVER_HOST, UDP_SERVER_PORT))
                try:
                    ack, _ = client_socket_udp.recvfrom(BUFFER_SIZE)
                    ack = int(ack.decode())

                    if ack == seq_num:
                        seq_num += 1
                    else:
                        seq_num = ack

                except socket.timeout:
                    print("No response from server within 20 seconds")
                    return
            client_socket_udp.sendto("DONE".encode(), (UDP_SERVER_HOST, UDP_SERVER_PORT))
        print(f"File '{filename}' uploaded successfully.")
    else:
        client_socket_udp.sendto(f"{name},BREAK".encode(), (UDP_SERVER_HOST, UDP_SERVER_PORT))
        print(f"File {filename} doesn't exist")


def handle_download_udp(client_socket_udp, filename):
    global name
    client_socket_udp.sendto(f"{name},{filename}".encode(), (UDP_SERVER_HOST, UDP_SERVER_PORT))

    try:
        response, addr = client_socket_udp.recvfrom(BUFFER_SIZE)
    except socket.timeout:
        print("Server has disconnected")
        return

    if response == b'OK':
        file_path = os.path.join(DIRECTORY, filename)
        with open(file_path, 'wb') as f:
            seq_num = 0
            while True:
                try:
                    data, _ = client_socket_udp.recvfrom(BUFFER_SIZE)
                    if data == b'DONE':
                        break
                    seq, payload = data.decode().split(',', 1)
                    seq = int(seq)
                    if seq == seq_num:
                        f.write(payload.encode())
                        seq_num += 1
                except socket.timeout:
                    print("Server has disconnected")
                    return
                client_socket_udp.sendto(str(seq_num).encode(), (UDP_SERVER_HOST, UDP_SERVER_PORT))
            print(f"File '{filename}' downloaded successfully.")
    else:
        print(response)


def handle_time(client_socket):
    try:
        response = client_socket.recv(BUFFER_SIZE).decode()
    except socket.timeout:
        print("Server has disconnected")
        return
    print(response)


def handle_echo(client_socket):
    message = input("Enter message to send: ")

    with socket_lock:
        client_socket.sendall(message.encode())
        try:
            response = client_socket.recv(BUFFER_SIZE).decode()
        except socket.timeout:
            print("Server has disconnected")
            return

    print("Echo response:", response)


if __name__ == "__main__":
    main()
