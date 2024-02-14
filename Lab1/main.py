import socket
import time

server_start_time = time.time()


def handle_command(comm):
    global server_start_time
    if comm.startswith("ECHO"):
        return comm[5:] + '\n'
    elif comm.startswith("TIME"):

        uptime_seconds = int(time.time() - server_start_time)
        uptime_str = time.strftime('%H:%M:%S', time.gmtime(uptime_seconds))
        return "Server uptime: {}\n".format(uptime_str)
    elif comm.startswith("CLOSE") or comm.startswith("EXIT") or comm.startswith("QUIT"):
        return "Closing connection\n"
    else:
        return "Unknown command\n"


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('', 12345)

server_socket.bind(server_address)

server_socket.listen(1)

print("Waiting for a connection...\n")

try:
    while True:
        client_socket, client_address = server_socket.accept()
        print("Connection from:", client_address)

        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break

                command = data.decode().strip()
                response = handle_command(command)

                client_socket.sendall(response.encode())

                if command.startswith("CLOSE") or command.startswith("EXIT") or command.startswith("QUIT"):
                    break
            except ConnectionResetError:
                print("Connection reset by peer")
                break
        client_socket.close()

except KeyboardInterrupt:
    print("Server interrupted. Closing...")
finally:
    server_socket.close()
