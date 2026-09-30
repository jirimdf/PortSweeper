# PortSweeper

A lightweight, multi-threaded port scanner written in Python. It scans TCP and/or UDP ports on a target IPv4/IPv6 address or hostname, with optional banner grabbing and reverse DNS lookup.

## Features

- Scan a target by IPv4, IPv6 or hostname
- Scan specific ports, a port range, or all ports (0–65535)
- TCP, UDP or both
- Adjustable scan speed (1–5)
- Banner grabbing on open TCP ports
- Reverse DNS lookup
- Multi-threaded for faster scans

## Tech stack

- Python 3 (standard library only: `socket`, `threading`, `argparse`)

## Installation

No external dependencies are required.

```bash
git clone https://github.com/jirimdf/PortSweeper.git
cd PortSweeper
```

## Usage

```bash
python main.py <target> [-p PORT [PORT ...]] [-t] [-u] [-a] [-s SPEED] [-r] [-b]
```

| Argument | Description |
|---|---|
| `target` | Target IP address (IPv4/IPv6) or hostname |
| `-p`, `--port` | Port(s) to scan: a single port or a range (`20 80`) |
| `-t`, `--tcp` | Scan TCP ports |
| `-u`, `--udp` | Scan UDP ports |
| `-a`, `--all` | Scan all ports (0–65535) |
| `-s`, `--speed` | Scan speed from 1 (slowest) to 5 (fastest) |
| `-r`, `--reverse-dns` | Perform a reverse DNS lookup |
| `-b`, `--banner` | Grab banners from open TCP ports |
| `-h`, `--help` | Show help |

### Examples

Scan TCP and UDP ports 20–80 on `example.com` with banner grabbing and reverse DNS lookup:

```bash
python main.py example.com -p 20 80 -t -u -r -b
```

Scan all TCP ports on `10.10.110.28`:

```bash
python main.py 10.10.110.28 -t -a
```

### Example output

```
$ python main.py 127.0.0.1 -p 130 140 -t
Starting MDF scanner v0.1.0 ( https://github.com/jirimdf ) at 2026-09-30 23:19:36
Scanning target 127.0.0.1 on port 130 to 140

Scanned open port on 135/TCP

MDF done: 1 open port found in 1.01 seconds
```

## Notes

- Tested on Windows and Linux.
- This tool is intended for learning and authorized security testing only. Only scan systems you own or have explicit permission to test.

## License

This project is licensed under the [MIT License](LICENSE).
