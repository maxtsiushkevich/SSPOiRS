import socket
import os
import time

TCP_SERVER_HOST = '127.0.0.1'
TCP_SERVER_PORT = 8000

UDP_SERVER_HOST = '127.0.0.1'
UDP_SERVER_PORT = 8001

BUFFER_SIZE = 1024
DIRECTORY = "server_folder/"

server_start_time = time.time()

user_file_upload = {}
user_file_download = {}


def handle_client_tcp(client_socket, address, server_socket_udp):
    print(f"Accepted connection from {address} via TCP")

    try:
        name = client_socket.recv(BUFFER_SIZE).decode()
    except socket.timeout:
        print("No response from client within 20 seconds")
        return

    client_socket.sendall(b'OK')

    while True:
        try:
            command = client_socket.recv(BUFFER_SIZE).decode()
        except ConnectionResetError:
            print("Client disconnect")
            return

        if command == 'PING':
            client_socket.sendall(b'PONG')

        if not command or command == 'EXIT':
            print(f'Client {address} disconnected')
            break

        if command == "UPLOAD":
            try:
                protocol = client_socket.recv(BUFFER_SIZE)
            except ConnectionResetError:
                print("Client disconnect")
                continue

            print(protocol)
            if protocol == b'TCP':
                client_socket.sendall(b'OK')
                handle_upload_tcp(client_socket, name)
            elif protocol == b'UDP':
                client_socket.sendall(b'OK')
                handle_upload_udp(server_socket_udp)
                pass
            else:
                print("Unavailable protocol")
                client_socket.sendall(b'NOT OK')
                continue

        elif command == "DOWNLOAD":
            try:
                protocol = client_socket.recv(BUFFER_SIZE)
            except ConnectionResetError:
                print("Client disconnect")
                continue
            client_socket.sendall(b'OK')
            print(protocol)
            if protocol == b'TCP':
                handle_download_tcp(client_socket, name)
            elif protocol == b'UDP':
                handle_download_udp(server_socket_udp)
                pass
            else:
                print("Unavailable protocol")
                client_socket.sendall(b'NOT OK')
                continue

        elif command == "TIME":
            handle_time(client_socket)

        elif command == "ECHO":
            handle_echo(client_socket, address)

        elif command == "CHECK UPLOADS":
            handle_check_uploads(client_socket, name)

        elif command == "CHECK DOWNLOADS":
            handle_check_downloads(client_socket, name)

    client_socket.close()


def handle_check_uploads(client_socket, name):
    print(user_file_upload)
    if name in user_file_upload:
        client_socket.sendall(b"Pumping " + user_file_upload[name].encode())
        try:
            if client_socket.recv(BUFFER_SIZE) == b'OK':
                handle_upload_tcp(client_socket, name)
        except ConnectionResetError:
            print("Client disconnect")
            return
    else:
        client_socket.sendall(b'No pumping')


def handle_check_downloads(client_socket, name):
    print(user_file_download)
    if name in user_file_download:
        client_socket.sendall(b"Pumping " + user_file_download[name].encode())
        try:
            if client_socket.recv(BUFFER_SIZE) == b'OK':
                handle_download_tcp(client_socket, name)
        except ConnectionResetError:
            print("Client disconnect")
            return
    else:
        client_socket.sendall(b'No pumping')


def handle_upload_tcp(client_socket, name):
    try:
        filename = client_socket.recv(BUFFER_SIZE).decode()
    except ConnectionResetError:
        print("Client disconnect")
        return

    if filename == 'BREAK':
        return

    user_file_upload[name] = filename

    print(f"filename {filename}")
    file_path = os.path.join(DIRECTORY, filename)
    with open(file_path, 'wb') as f:
        while True:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if not data or data == b'DONE':
                    print(data)
                    break
                else:
                    client_socket.sendall(B"OK")
            except ConnectionResetError:
                print("Client disconnect")
                return
            f.write(data)

    print(f"File '{filename}' uploaded successfully.")
    del user_file_upload[name]


def handle_download_tcp(client_socket, name):
    try:
        filename = client_socket.recv(BUFFER_SIZE).decode()
    except ConnectionResetError:
        print("Client disconnect")
        return

    print(f"filename {filename}")
    user_file_download[name] = filename

    file_path = os.path.join(DIRECTORY, filename)
    if os.path.exists(file_path):
        client_socket.sendall(b"OK")
        with open(file_path, 'rb') as f:
            data = f.read(BUFFER_SIZE)

            while data:
                client_socket.sendall(data)

                # time.sleep(5)

                try:
                    if client_socket.recv(BUFFER_SIZE) == b'OK':
                        data = f.read(BUFFER_SIZE)
                except ConnectionResetError:
                    print("Client disconnect")
                    return

            client_socket.sendall(b'DONE')

        print(f"File '{filename}' sent successfully.")
    else:
        client_socket.sendall("File not found".encode())

    del user_file_download[name]


def handle_upload_udp(server_socket_udp):
    data, address = server_socket_udp.recvfrom(BUFFER_SIZE)
    data = data.decode()
    name, filename = data.split(',', 1)
    print(f"data {data}")
    if filename == "BREAK":
        return
    user_file_upload[name] = filename

    file_path = os.path.join(DIRECTORY, filename)
    with open(file_path, 'wb') as f:
        seq_num = 0
        while True:
            data, addr = server_socket_udp.recvfrom(BUFFER_SIZE)
            if addr == address:
                if data == b'DONE':
                    break
                packet = data.decode().split(',', 1)
                seq = int(packet[0])
                payload = packet[1]
                if seq == seq_num:
                    f.write(payload.encode())
                    seq_num += 1
                server_socket_udp.sendto(str(seq_num).encode(), address)

    del user_file_upload[name]


def handle_download_udp(server_socket_udp):
    data, address = server_socket_udp.recvfrom(BUFFER_SIZE)
    data = data.decode()
    name, filename = data.split(',', 1)
    print(f"data {data}")

    user_file_download[name] = filename

    file_path = os.path.join(DIRECTORY, filename)
    if os.path.exists(file_path):
        server_socket_udp.sendto("OK".encode(), address)
        with open(file_path, 'rb') as f:
            seq_num = 0
            while True:
                data = f.read(BUFFER_SIZE - len(str(seq_num)) - 1)
                if not data:
                    break
                packet = f"{seq_num},{data.decode()}"
                server_socket_udp.sendto(packet.encode(), address)
                ack, _ = server_socket_udp.recvfrom(BUFFER_SIZE)
                ack = int(ack.decode())
                if ack == seq_num:
                    seq_num += 1
                else:
                    seq_num = ack

            server_socket_udp.sendto("DONE".encode(), address)
    else:
        server_socket_udp.sendto("File not found".encode(), address)

    del user_file_download[name]


def handle_time(client_socket):
    uptime_seconds = int(time.time() - server_start_time)
    uptime_str = time.strftime('%H:%M:%S', time.gmtime(uptime_seconds))
    response = f"Server uptime: {uptime_str}"
    client_socket.sendall(response.encode())


def handle_echo(client_socket, address):
    try:
        message = client_socket.recv(BUFFER_SIZE).decode()
    except ConnectionResetError:
        print("Client disconnect")
        return

    print(f"Received message from {address}: {message}")
    client_socket.sendall(message.encode())


def start_tcp_server():
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_server_socket.bind((TCP_SERVER_HOST, TCP_SERVER_PORT))

    # tcp_server_socket.listen(5)
    tcp_server_socket.listen(1)

    print(f"TCP server listening on {TCP_SERVER_HOST}:{TCP_SERVER_PORT}")

    server_socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket_udp.bind((UDP_SERVER_HOST, UDP_SERVER_PORT))
    print(f"UDP server listening on {UDP_SERVER_HOST}:{UDP_SERVER_PORT}")

    try:
        while True:
            client_socket, address = tcp_server_socket.accept()
            handle_client_tcp(client_socket, address, server_socket_udp)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Shutting down the server.")
    finally:
        tcp_server_socket.close()
        server_socket_udp.close()

    # while True:
    #     client_socket, address = tcp_server_socket.accept()
    #     client_handler = threading.Thread(target=handle_client_tcp, args=(client_socket, address, server_socket_udp))
    #     client_handler.start()


def main():
    start_tcp_server()


if __name__ == "__main__":
    main()
