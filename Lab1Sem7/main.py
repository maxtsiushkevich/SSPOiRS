import sys
import threading

from ping import ping
from smurf import smurf
from traceroute import traceroute


def main():
    args = sys.argv[1:]
    threads = []
    print()

    if args[0].startswith('traceroute:'):
        target_ip = args[0][len('traceroute:'):]
        traceroute_thread = threading.Thread(target=traceroute, args=(target_ip,))
        threads.append(traceroute_thread)
        traceroute_thread.start()
    elif args[0].startswith('smurf:'):
        ips = args[0][len('smurf:'):].split(',')
        if len(ips) == 2:
            attack_target_ip = ips[0]
            broadcast_ip = ips[1]
            for i in range(100000):
                smurf_thread = threading.Thread(target=smurf, args=(attack_target_ip, broadcast_ip))
                threads.append(smurf_thread)
                smurf_thread.start()
        else:
            print("Error: smurf requires exactly two IP addresses (target, broadcast).")
            return
    elif len(args) % 2 != 0:
        print("Error: the number of arguments must be even")
        return
    else:
        pairs = list(zip(args[::2], args[1::2]))
        for addr, count in pairs:
            ping_thread = threading.Thread(target=ping, args=(addr, int(count)))
            threads.append(ping_thread)
            ping_thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
