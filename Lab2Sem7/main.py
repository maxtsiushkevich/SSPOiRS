import socket
import struct
import threading
from interface import *
from network import get_network_params, is_valid_multicast

conn_list = []
block_list = []

multicast_ip = '224.0.0.1'
is_multicast_changed = False

broadcast_port = 5000
multicast_port = 5001


def send_broadcast(message, chat_text):
    if message == '':
        return
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(message.encode('utf-8'), ('<broadcast>', broadcast_port))
    text = f'You (Broadcast): {message}'
    update_textbox(chat_text, text)


def send_multicast(message, chat_text):
    if message == '':
        return
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
    sock.sendto(message.encode('utf-8'), (multicast_ip, multicast_port))
    # print(multicast_ip)
    text = f'You (Multicast): {message}'
    update_textbox(chat_text, text)


def receive_broadcast(chat_text):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(('', broadcast_port))
    sock.settimeout(2)
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if addr[0] in block_list:
                continue
            message = data.decode('utf-8')

            if message == "SSPOiRS_CHAT_DISCOVER":
                response = "SSPOiRS_CHAT_RESPONSE"
                sock.sendto(response.encode('utf-8'), addr)
                continue

            text = f'From {addr[0]} (Broadcast): {message}'
            update_textbox(chat_text, text)
        except socket.timeout:
            continue


def create_multicast_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', multicast_port))
    sock.setblocking(False)
    mreq = struct.pack("4sl", socket.inet_aton(multicast_ip), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    return sock


def receive_multicast(chat_text):
    global is_multicast_changed
    sock = create_multicast_socket()

    while True:
        try:
            if is_multicast_changed:
                print(multicast_ip)
                is_multicast_changed = False
                sock.close()
                sock = create_multicast_socket()

            data, addr = sock.recvfrom(1024)
            if addr[0] in block_list:
                continue

            message = data.decode('utf-8')
            text = f'From {addr[0]} (Multicast): {message}'

            update_textbox(chat_text, text)
        except BlockingIOError:
            continue


def change_multicast(new_mcast_ip, ip_multicast_label):
    global multicast_ip, is_multicast_changed
    if is_valid_multicast(new_mcast_ip):
        is_multicast_changed = True
        multicast_ip = new_mcast_ip
        ip_multicast_label.config(text=f'Multicast: {multicast_ip}')
    else:
        print(f'Invalid multicast address: {new_mcast_ip}')


def refresh_conn_devices(conn_devices_tree):
    print('refresh_conn_devices')

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(1)

    message = "SSPOiRS_CHAT_DISCOVER"
    try:
        # Отправляем сообщение на broadcast адрес
        sock.sendto(message.encode('utf-8'), ('<broadcast>', broadcast_port))

        while True:
            try:
                data, addr = sock.recvfrom(1024)
                if data.decode('utf-8') == "SSPOiRS_CHAT_RESPONSE" and addr[0] not in block_list:
                    if addr[0] not in conn_list:
                        conn_list.append(addr[0])
            except socket.timeout:
                break
    finally:
        sock.close()

    conn_devices_tree.delete(*conn_devices_tree.get_children())  # очищает список на экране
    for ip in conn_list:
        conn_devices_tree.insert("", "end", values=(ip,))


def block_device(treeview, blocked_treeview):
    selected_ip = treeview.selection()
    if selected_ip:
        device = treeview.item(selected_ip)["values"][0]
        if device:
            blocked_treeview.insert("", "end", values=(device,))
            treeview.delete(selected_ip)
            conn_list.remove(device)
            block_list.append(device)


def unblock_device(blocked_devices_tree, conn_devices_tree):
    selected_ip = blocked_devices_tree.selection()
    if selected_ip:
        device = blocked_devices_tree.item(selected_ip)["values"][0]
        if device:
            blocked_devices_tree.delete(selected_ip)
            block_list.remove(device)
            if device not in conn_list:
                conn_list.append(device)
            refresh_conn_devices(conn_devices_tree)


def main():
    root = tk.Tk()
    root.title("SSPOiRS Chat")
    root.geometry('860x600')

    chat_label = create_label(root, 'Chat', 0.02, 0.005, ('Arial', 14, 'bold'))
    chat_text = create_text_widget(root, 75, 33, 0.02, 0.05)

    info_label = create_label(root, 'Network settings', 0.67, 0.05, ('Arial', 14, 'bold'))

    network_params = get_network_params()
    ip_label = create_label(root, f'IP: {network_params[0]}', 0.67, 0.1)
    ip_mask_label = create_label(root, f'Mask: {network_params[1]}', 0.67, 0.13)
    ip_broadcast_label = create_label(root, f'Broadcast: {network_params[2]}', 0.67, 0.16)
    ip_multicast_label = create_label(root, f'Multicast: {multicast_ip}', 0.67, 0.19)

    message_label = create_label(root, 'Your message', 0.02, 0.8, ('Arial', 14, 'bold'))
    message_entry = create_input_entry(root, 58, 0.02, 0.84)

    send_broadcast_button = tk.Button(root, text='Send Broadcast',
                                      command=lambda: send_broadcast(message_entry.get(), chat_text))
    send_broadcast_button.place(relx=0.02, rely=0.9)

    send_multicast_button = tk.Button(root, text='Send Multicast',
                                      command=lambda: send_multicast(message_entry.get(), chat_text))
    send_multicast_button.place(relx=0.2, rely=0.9)

    conn_devices_label = create_label(root, 'Connected devices list', 0.67, 0.24, ('Arial', 14, 'bold'))

    conn_devices_tree = ttk.Treeview(root, columns=("IP Address",), show='headings')
    conn_devices_tree.heading("IP Address", text="IP Address")
    conn_devices_tree.place(relx=0.67, rely=0.28, width=200, height=150)

    refresh_device_button = tk.Button(root, text='Refresh',
                                      command=lambda: refresh_conn_devices(conn_devices_tree))
    refresh_device_button.place(relx=0.905, rely=0.32)

    block_device_button = tk.Button(root, text='Block',
                                    command=lambda: block_device(conn_devices_tree, blocked_devices_tree))
    block_device_button.place(relx=0.905, rely=0.37)

    block_devices_label = create_label(root, 'Blocked devices list', 0.67, 0.53, ('Arial', 14, 'bold'))

    blocked_devices_tree = ttk.Treeview(root, columns=("IP Address",), show='headings')
    blocked_devices_tree.heading("IP Address", text="IP Address")
    blocked_devices_tree.place(relx=0.67, rely=0.57, width=200, height=150)

    unblock_device_button = tk.Button(root, text='Unblock',
                                      command=lambda: unblock_device(blocked_devices_tree, conn_devices_tree))
    unblock_device_button.place(relx=0.905, rely=0.61)

    change_multicast_label = create_label(root, 'Enter multicast group:', 0.67, 0.84, ('Arial', 14, 'bold'))
    change_multicast_entry = create_input_entry(root, 20, 0.67, 0.88,
                                                lambda: change_multicast(change_multicast_entry.get(),
                                                                         ip_multicast_label))
    change_multicast_button = tk.Button(root, text='Change multicast group',
                                        command=lambda: change_multicast(change_multicast_entry.get(),
                                                                         ip_multicast_label))
    change_multicast_button.place(relx=0.67, rely=0.93)

    clear_chat_button = tk.Button(root, text='Clear Chat', command=lambda: clear_text_widget(chat_text))
    clear_chat_button.place(relx=0.525, rely=0.78)

    # Запуск потоков для получения сообщений
    threading.Thread(target=receive_broadcast, args=(chat_text,), daemon=True).start()
    threading.Thread(target=receive_multicast, args=(chat_text,), daemon=True).start()

    root.mainloop()


if __name__ == "__main__":
    main()
