import struct
import time


class Packet:
    def __init__(self, icmp_type, icmp_code, data=None):
        self.type = icmp_type
        self.code = icmp_code
        self.data = data if data is not None else b''

    @staticmethod
    def calc_checksum(packet: bytes):
        words = [int.from_bytes(packet[_:_ + 2], "big") for _ in range(0, len(packet), 2)]
        checksum = sum(words)
        while checksum > 0xffff:
            checksum = (checksum & 0xffff) + (checksum >> 16)
        return 0xffff - checksum

    def create_packet(self, seq, ident=1):
        ident = ident % 65536
        header = struct.pack('!bbHHH', self.type, self.code, 0, ident, seq)

        send_time = time.time_ns()
        self.data = struct.pack('!Q', send_time)

        full_packet = header + self.data
        checksum = Packet.calc_checksum(full_packet)

        header = struct.pack('!bbHHH', self.type, self.code, checksum, ident, seq)

        return header + self.data

    @staticmethod
    def get_icmp_type_description(type_code):
        descriptions = {
            0: "Echo",
            3: "Destination Unreachable",
            8: "Echo Request",
            11: "Time Exceeded"
        }
        return descriptions.get(type_code, "Unknown")

    @staticmethod
    def parse_icmp_header(recv_packet: bytes):
        type_c, code, checksum, ident, seq = struct.unpack('!bbHHH', recv_packet[:8])
        return type_c, code, ident, seq
