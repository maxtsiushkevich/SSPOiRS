import socket
import threading
import time

from packet import Packet

lock = threading.Lock()


def traceroute(target_ip: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
    sock.settimeout(1)
    ident = threading.get_ident()
    ttl = 1
    src_ip = ''
    while src_ip != target_ip:
        sock.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
        packet = Packet(8, 0).create_packet(seq=ttl, ident=ident)
        send_time = time.time_ns()
        sock.sendto(packet, (target_ip, 0))
        try:
            rec_packet, recv_addr = sock.recvfrom(1024)
            recv_time = time.time_ns()

            icmp_header = rec_packet[20:28]
            type_code, _, ident_recv, seq_recv = Packet.parse_icmp_header(icmp_header)

            rtt = (recv_time - send_time) / 1_000
            description = Packet.get_icmp_type_description(type_code)
            src_ip = recv_addr[0]
            with lock:
                print(f'TTL={ttl} {src_ip} - {description} Reply: {rtt:.2f}ms')
                ttl += 1

            if type_code == 0:
                break
        except socket.timeout:
            with lock:
                print(f'TTL={ttl} Request timed out.')
                continue

    sock.close()
