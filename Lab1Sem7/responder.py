from scapy.all import *
from scapy.layers.inet import ICMP, IP

args = sys.argv[1:]
if len(args) != 2:
    print("IP and Broadcast required")
    exit(0)

ip = args[0]
broadcast_ip = args[1]


def icmp_responder(packet):
    if packet.haslayer(ICMP) and packet[ICMP].type == 8:
        if packet[IP].dst == broadcast_ip:
            payload = packet[Raw].load if packet.haslayer(Raw) else b''
            reply = IP(src=ip, dst=packet[IP].src) / ICMP(type=0, id=packet[ICMP].id, seq=packet[ICMP].seq) / payload
            send(reply, verbose=False)


sniff(filter="icmp", prn=icmp_responder, store=0)
