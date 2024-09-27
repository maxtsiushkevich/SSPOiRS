import socket
import struct
import threading
import time

from packet import Packet

lock = threading.Lock()


def ping(target_ip: str, count: int, timeout=1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
    sock.settimeout(timeout)
    ident = threading.get_ident()

    for seq in range(count):
        packet = Packet(8, 0).create_packet(seq=seq, ident=ident)
        sock.sendto(packet, (target_ip, 0))
        time.sleep(1)

        try:
            while True:
                rec_packet, _ = sock.recvfrom(1024, socket.MSG_PEEK)
                recv_time = time.time_ns()
                send_time = struct.unpack('!Q', rec_packet[-8:])[0]
                icmp_header = rec_packet[20:28]
                type_code, _, ident_recv, seq_recv = Packet.parse_icmp_header(icmp_header)

                if ident_recv == ident % 65536 and seq_recv == seq:
                    sock.recvfrom(1024)
                    rtt = (recv_time - send_time) / 1_000 - 1_000_000
                    description = Packet.get_icmp_type_description(type_code)
                    ttl = rec_packet[8]
                    with lock:
                        print(
                            f'{target_ip} - {description} Reply: {rtt:.2f}ms Seq={seq_recv} bytes={len(rec_packet)} ttl={ttl}')
                    break
                else:
                    sock.recvfrom(1024)
        except socket.timeout:
            print(f"{target_ip} timeout")

    sock.close()
