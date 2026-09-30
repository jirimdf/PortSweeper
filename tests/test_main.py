import socket
import threading

import pytest

import main


def free_port(kind=socket.SOCK_STREAM):
    with socket.socket(socket.AF_INET, kind) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen()

    def serve():
        while True:
            try:
                conn, _ = server.accept()
            except OSError:
                return
            with conn:
                try:
                    conn.recv(1024)
                    conn.sendall(b"HTTP/1.1 200 OK\r\nServer: test\r\n\r\n")
                except OSError:
                    pass

    threading.Thread(target=serve, daemon=True).start()
    yield server.getsockname()[1]
    server.close()


@pytest.fixture
def udp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("127.0.0.1", 0))

    def serve():
        while True:
            try:
                _, addr = server.recvfrom(1024)
                server.sendto(b"pong", addr)
            except OSError:
                return

    threading.Thread(target=serve, daemon=True).start()
    yield server.getsockname()[1]
    server.close()


def test_parse_single_port():
    assert main.parse_ports([80]) == [80]


def test_parse_range():
    assert main.parse_ports([20, 25]) == [20, 21, 22, 23, 24, 25]


def test_parse_list():
    assert main.parse_ports([443, 22, 80]) == [22, 80, 443]


def test_parse_all():
    ports = main.parse_ports(None, scan_all=True)
    assert ports[0] == 1 and ports[-1] == 65535


@pytest.mark.parametrize("ports", [None, [80, 20], [0], [70000]])
def test_parse_invalid(ports):
    with pytest.raises(ValueError):
        main.parse_ports(ports)


def test_tcp_open_and_closed(tcp_server):
    assert main.tcp_scan(socket.AF_INET, "127.0.0.1", tcp_server)
    assert not main.tcp_scan(socket.AF_INET, "127.0.0.1", free_port())


def test_udp_open(udp_server):
    assert main.udp_scan(socket.AF_INET, "127.0.0.1", udp_server)


def test_udp_closed():
    assert not main.udp_scan(socket.AF_INET, "127.0.0.1", free_port(socket.SOCK_DGRAM), timeout=0.3)


def test_banner(tcp_server):
    banner = main.banner_grab(socket.AF_INET, "127.0.0.1", tcp_server, "localhost")
    assert banner.startswith("HTTP/1.1 200 OK")


def test_port_scan_finds_open_port(tcp_server, capsys):
    result = main.port_scan("127.0.0.1", [tcp_server, free_port()])
    assert result == [("TCP", tcp_server)]
    assert f"Scanned open port on {tcp_server}/TCP" in capsys.readouterr().out


def test_cli_without_ports_fails():
    with pytest.raises(SystemExit):
        main.main(["127.0.0.1"])


def test_cli_unknown_host(capsys):
    assert main.main(["host.invalid", "-p", "80"]) == 1
    assert "Could not resolve target" in capsys.readouterr().out
