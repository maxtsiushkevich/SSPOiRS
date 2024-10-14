import ipaddress

import netifaces


def get_network_params():
    iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
    iface_info = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]
    ip = iface_info['addr']
    netmask = iface_info['netmask']
    broadcast_ip = iface_info.get('broadcast', None)
    return ip, netmask, broadcast_ip


def is_valid_multicast(ip_str):
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_multicast
    except ValueError:
        return False
