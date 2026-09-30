import socket
import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

VERSION = "0.2.0"

# Number of ports scanned at the same time for each speed level (1 = slowest, 5 = fastest)
SPEED_WORKERS = {1: 10, 2: 50, 3: 100, 4: 250, 5: 500}
DEFAULT_SPEED = 4

TIMEOUT = 1


def build_parser():
    parser = argparse.ArgumentParser(description=f"PortSweeper v{VERSION} ( https://github.com/jirimdf )")
    parser.add_argument("target", help="Target IP address (IPv4/IPv6) or hostname")
    parser.add_argument("-p", "--port", nargs="+", type=int,
                        help="One port, a range (two values: start end) or a list of ports")
    parser.add_argument("-t", "--tcp", action="store_true", help="Scan TCP ports (default)")
    parser.add_argument("-u", "--udp", action="store_true", help="Scan UDP ports")
    parser.add_argument("-a", "--all", action="store_true", help="Scan all ports (1-65535)")
    parser.add_argument("-s", "--speed", type=int, choices=range(1, 6), default=DEFAULT_SPEED,
                        help=f"Scan speed from 1 (slowest) to 5 (fastest), default {DEFAULT_SPEED}")
    parser.add_argument("-r", "--reverse-dns", action="store_true", help="Perform reverse DNS lookup")
    parser.add_argument("-b", "--banner", action="store_true", help="Grab banner from open TCP ports")
    return parser


def parse_ports(ports, scan_all=False):
    """Turn the -p values into a sorted list of ports."""
    if scan_all:
        return list(range(1, 65536))
    if not ports:
        raise ValueError("No ports given. Use -p or -a.")
    if len(ports) == 2:
        start, end = ports
        if start > end:
            raise ValueError("Range start must not be greater than range end.")
        result = list(range(start, end + 1))
    else:
        result = sorted(set(ports))
    if result[0] < 1 or result[-1] > 65535:
        raise ValueError("Ports must be between 1 and 65535.")
    return result


def resolve_target(target):
    """Return (address family, IP address) for an IP or hostname."""
    family, _, _, _, sockaddr = socket.getaddrinfo(target, None)[0]
    return family, sockaddr[0]


def tcp_scan(family, ip, port, timeout=TIMEOUT):
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((ip, port)) == 0


def udp_scan(family, ip, port, timeout=TIMEOUT):
    """A UDP port counts as open only when it sends a reply."""
    with socket.socket(family, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.sendto(b"", (ip, port))
            sock.recvfrom(1024)
            return True
        except OSError:
            return False


def banner_grab(family, ip, port, host, timeout=2):
    try:
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((ip, port))
            sock.sendall(b"HEAD / HTTP/1.1\r\nHost: %s\r\n\r\n" % host.encode())
            banner = sock.recv(1024)
        return banner.decode(errors="replace").strip() or None
    except OSError:
        return None


def reverse_dns_lookup(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except OSError:
        return None


def port_scan(target, ports, tcp=True, udp=False, speed=DEFAULT_SPEED, banner=False, reverse_dns=False):
    family, ip = resolve_target(target)
    start_time = time.time()

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Starting MDF scanner v{VERSION} ( https://github.com/jirimdf ) at {current_time}")
    if len(ports) > 1 and ports == list(range(ports[0], ports[-1] + 1)):
        print(f"Scanning target {target} ({ip}) on port {ports[0]} to {ports[-1]}\n")
    else:
        print(f"Scanning target {target} ({ip}) on ports {', '.join(map(str, ports))}\n")

    if reverse_dns:
        host = reverse_dns_lookup(ip)
        print(f"Reverse DNS lookup for {ip}: {host or 'Not found'}")

    jobs = []
    if tcp:
        jobs += [("TCP", port) for port in ports]
    if udp:
        jobs += [("UDP", port) for port in ports]

    def scan(job):
        protocol, port = job
        scanner = tcp_scan if protocol == "TCP" else udp_scan
        return job if scanner(family, ip, port) else None

    open_ports = []
    executor = ThreadPoolExecutor(max_workers=SPEED_WORKERS[speed])
    try:
        for result in executor.map(scan, jobs):
            if result:
                protocol, port = result
                open_ports.append(result)
                print(f"Scanned open port on {port}/{protocol}")
                if banner and protocol == "TCP":
                    text = banner_grab(family, ip, port, target)
                    print(f"Banner for {target}:{port}: {text}" if text
                          else f"Could not grab banner for {target}:{port}")
    finally:
        # On Ctrl+C, drop the ports that have not been scanned yet instead of waiting for them
        executor.shutdown(wait=False, cancel_futures=True)

    duration = time.time() - start_time
    if not open_ports:
        print("Scanner didn't find any open ports")
    else:
        port_word = "port" if len(open_ports) == 1 else "ports"
        print(f"\nMDF done: {len(open_ports)} open {port_word} found in {duration:.2f} seconds")
    return open_ports


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        ports = parse_ports(args.port, args.all)
    except ValueError as e:
        parser.error(str(e))

    tcp = args.tcp or not args.udp
    try:
        port_scan(args.target, ports, tcp, args.udp, args.speed, args.banner, args.reverse_dns)
    except socket.gaierror:
        print(f"Could not resolve target: {args.target}")
        return 1
    except KeyboardInterrupt:
        print("\nExiting..")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
