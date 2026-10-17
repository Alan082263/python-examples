# Network Scanner & Asset Manager

A lightweight network scanner and asset inventory tool, built with Python
and Tkinter. It wraps Nmap to discover hosts, detect open ports and
services, and (where privileges allow) guess the operating system — then
lets you export the results to CSV or Excel.

## Features

- Host discovery and port scanning for a single IP, hostname, or CIDR
  range (e.g. `192.168.1.0/24`)
- Service and version detection (`-sV`)
- OS fingerprinting (`-O`), with automatic fallback to a plain scan if
  your OS/privileges don't allow it (OS detection needs elevated
  privileges on most systems — see below)
- Running asset inventory: results from multiple scans accumulate into
  one table, keyed by IP address
- Export the current inventory to CSV or a formatted XLSX workbook
- Simple Tkinter GUI — no browser or server required

## Requirements

- Python 3.9+
- **Nmap** installed and on your system `PATH` — this tool calls the real
  `nmap` binary, it doesn't bundle one:
  - macOS: `brew install nmap`
  - Ubuntu/Debian: `sudo apt install nmap`
  - Windows: download the installer from [nmap.org](https://nmap.org/download.html)

## Setup

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Usage

1. Enter a target — a single IP (`192.168.1.10`), hostname, or a CIDR
   range (`192.168.1.0/24`) to scan a whole subnet
2. Optionally adjust the port range (defaults to `1-1024`)
3. Toggle **Detect OS** and **Detect services** as needed
4. Click **Start Scan** — results stream into the table as they complete
5. Repeat with other targets; results accumulate into one inventory
   (re-scanning the same IP updates its row)
6. Click **Export CSV** or **Export XLSX** to save the current inventory

### About OS detection

Nmap's OS fingerprinting (`-O`) sends raw packets and requires
administrator/root privileges on most systems. If you run this tool as a
normal user, OS detection will silently be skipped for that scan (a
status message will say so) rather than the whole scan failing — port
and service detection don't require elevated privileges and will still
work normally.

To get OS detection working:
- **macOS/Linux:** run `sudo python main.py`
- **Windows:** run your terminal/IDE as Administrator

## Project layout

```
network_scanner/
├── main.py            # Tkinter GUI — entry point
├── scanner.py          # NetworkScanner: wraps python-nmap, returns plain data
├── asset_manager.py    # AssetManager: in-memory inventory + CSV/XLSX export
└── requirements.txt
```

## Notes

- Only scan networks and hosts you own or have explicit permission to
  scan — unauthorized port scanning can violate laws or acceptable-use
  policies depending on where you are and what you're scanning.
- This is a from-scratch implementation, not a copy of any particular
  existing scanner — built to cover the core feature set (Nmap-backed
  scanning, OS detection, service detection, CSV/XLSX export, Tkinter
  GUI) without the platform-specific packaging tooling (`.exe` builds,
  installers, splash screens), which wasn't relevant on macOS.

## Finding every device (macOS)

Without administrator rights, nmap misses devices that don't run a web
server or that ignore connections (bulbs, cameras, phones). The scanner
finds hosts in this order:

1. **Administrator ARP sweep** — `sudo -n nmap -sn -n -oG - 10.0.0.0/24`.
   Finds every device in a few seconds. Needs this sudoers rule, which
   allows only that exact command without a password:

   ```
   # /etc/sudoers.d/netscanner  (check with: sudo visudo -cf <file>)
   alan ALL=(root) NOPASSWD: /opt/homebrew/bin/nmap -sn -n -oG - 10.0.0.0/24
   ```

   Remove with `sudo rm /etc/sudoers.d/netscanner`.
2. **Fallback (no rule, or a different target):** a normal `nmap -sn`
   sweep, a 5-second pause, then the macOS ARP cache (`arp -an`).
   Works without root but misses sleepy devices; results vary per run.

Run the app by double-clicking `run_scanner.command`, or with
`source .venv/bin/activate && python main.py`. Zed (or whichever app
runs it) needs **System Settings → Privacy & Security → Local Network**.
