import socket
import argparse
import threading
import time
from datetime import datetime

parser = argparse.ArgumentParser(description="PortSweeper v0.1.0 ( https://github.com/jirimdf )")
parser.add_argument("target", help="Target IP address or URL")
parser.add_argument("-p", "--port", nargs="+", help="Port(s) to scan", type=int)
parser.add_argument("-t", "--tcp", action="store_true", help="Scan TCP ports")
parser.add_argument("-u", "--udp", action="store_true", help="Scan UDP ports")
parser.add_argument("-a", "--all", action="store_true", help="Scan all ports")
parser.add_argument("-s", "--speed", type=int, choices=range(1, 6), default=None, help="Scan speed (1-5)")
parser.add_argument("-r", "--reverse-dns", action="store_true", help="Perform reverse DNS lookup")
parser.add_argument("-b", "--banner", action="store_true", help="Grab banner from open TCP ports")
args = parser.parse_args()

open_ports = []


def tcp_scan(target, port):
    global open_ports
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((target, port))
        if result == 0:
            open_ports.append((port, 'TCP'))
            print(f"Scanned open port on {port}/TCP")
            if args.banner:
                banner_grab(target, port)
        sock.close()
    except KeyboardInterrupt:
        print("\nExiting..")
        exit()
    except socket.error:
        print("Couldn't connect to server")


def udp_scan(target, port):
    global open_ports
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        sock.sendto(b"", (target, port))
        data, addr = sock.recvfrom(1024)
        open_ports.append((port, 'UDP'))
        print(f"Scanned open port on {port}/UDP")
    except KeyboardInterrupt:
        print("\nExiting..")
        exit()
    except socket.error:
        print("Couldn't connect to server")
    finally:
        sock.close()


def banner_grab(target, port):
    try:
        sock = socket.socket()
        sock.connect((target, port))
        sock.sendall(b'HEAD / HTTP/1.1\r\nHost: %s\r\n\r\n' % target.encode())
        banner = sock.recv(1024)
        print(f"Banner for {target}:{port}: {banner.decode().strip()}")
        sock.close()
    except:
        print(f"Could not grab banner for {target}:{port}")


def reverse_dns_lookup(ip):
    try:
        host = socket.gethostbyaddr(ip)
        return host[0]
    except socket.herror:
        return None


def port_scan(target, ports, tcp, udp):
    global open_ports
    start_time = time.time()

    if args.all:
        start_port, end_port = 0, 65535
    else:
        start_port, end_port = ports[0], ports[-1]

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"Starting MDF scanner v0.1.0 ( https://github.com/jirimdf ) at {current_time}")
    print(f"Scanning target {target} on port {start_port} to {end_port}\n")

    if args.reverse_dns:
        ip = target
        if not target.replace('.', '').isdigit():
            ip = socket.gethostbyname(target)
        host = reverse_dns_lookup(ip)
        if host:
            print(f"Reverse DNS lookup for {ip}: {host}")
        else:
            print(f"Reverse DNS lookup for {ip}: Not found")

    for port in range(start_port, end_port + 1):
        if tcp:
            t = threading.Thread(target=tcp_scan, args=(target, port))
            t.start()
        if udp:
            t = threading.Thread(target=udp_scan, args=(target, port))
            t.start()
        if args.speed is not None:
            time.sleep(args.speed)

    main_thread = threading.current_thread()
    for t in threading.enumerate():
        if t is not main_thread:
            t.join()

    end_time = time.time()
    duration = end_time - start_time
    port_word = "port" if len(open_ports) == 1 else "ports"
    if not open_ports:
        print("Scanner didn't find any open ports")
    else:
        print(f"\nMDF done: {len(open_ports)} open {port_word} found in {duration:.2f} seconds")


if __name__ == "__main__":
    port_scan(args.target, args.port, args.tcp, args.udp)
