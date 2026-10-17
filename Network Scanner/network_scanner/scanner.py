"""
Core scanning engine. Wraps python-nmap to run host discovery, port
scanning, service/version detection and OS fingerprinting, and returns
plain Python data structures (no GUI or file-format knowledge here).
"""

from __future__ import annotations

import ipaddress
import os
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

import nmap


class NmapNotFoundError(RuntimeError):
    """Raised when the nmap binary isn't available on the system PATH."""


@dataclass
class PortResult:
    port: int
    protocol: str
    state: str
    service: str = ""
    product: str = ""
    version: str = ""

    @property
    def service_label(self) -> str:
        parts = [p for p in (self.product, self.version) if p]
        detail = " ".join(parts)
        if self.service and detail:
            return f"{self.service} ({detail})"
        return self.service or detail or "unknown"


@dataclass
class HostResult:
    ip: str
    hostname: str = ""
    status: str = "unknown"
    mac_address: str = ""
    vendor: str = ""
    os_name: str = ""
    os_accuracy: str = ""
    ports: list[PortResult] = field(default_factory=list)
    scanned_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    @property
    def open_ports_summary(self) -> str:
        open_ports = [p for p in self.ports if p.state == "open"]
        if not open_ports:
            return ""
        return ", ".join(str(p.port) for p in open_ports)


class NetworkScanner:
    """
    Thin, GUI-agnostic wrapper around python-nmap.

    scan_target() runs a scan and returns a list[HostResult]. Pass a
    progress_callback(message: str) to receive human-readable status
    updates while a scan is running (nmap itself is blocking, so this
    is best used from a background thread in a GUI).
    """

    def __init__(self):
        if shutil.which("nmap") is None:
            raise NmapNotFoundError(
                "nmap was not found on your system PATH. Install it first "
                "(e.g. 'brew install nmap' on macOS, 'apt install nmap' on "
                "Debian/Ubuntu, or download it from nmap.org on Windows)."
            )
        self._nm = nmap.PortScanner()

    def _discover_hosts(self, target: str) -> list[str]:
        """
        Find live hosts without needing root.

        Every powered-on device answers the Mac's ARP question ("who has
        10.0.0.x?"), even with a firewall, and macOS keeps the answers in
        its ARP cache. So: make the Mac ask about every address, several
        times so sleepy Wi-Fi devices get a chance to wake, then read the
        cache with "arp -an".
        """
        try:
            network = ipaddress.ip_network(target, strict=False)
        except ValueError:
            # Not a network or single IP (e.g. a hostname): trust nmap alone.
            self._nm.scan(hosts=target, arguments="-sn")
            return sorted(self._nm.all_hosts())

        # 0. Best option: an administrator ARP sweep. Finds every device in
        #    seconds. Only works if a sudoers rule allows this exact command
        #    without a password (see README); otherwise fall through.
        admin_hosts = self._admin_sweep(target)
        if admin_hosts is not None:
            found = set(admin_hosts)
            my_ip = self._local_ip(network)
            if my_ip:
                found.add(my_ip)
            return sorted(found, key=ipaddress.ip_address)

        # 1. (Disabled: rapid UDP nudges made macOS mark slow devices
        #    "down" for ~20 s, so the nmap sweep below then skipped them.)
        # self._poke_addresses(network)

        # 2. nmap's own sweep: finds anything that answers on ports 80/443,
        #    and asks every address once more.
        self._nm.scan(hosts=target, arguments="-sn")
        found = set(self._nm.all_hosts())

        # 3. Give late answers a moment to reach the cache.
        time.sleep(5)

        # 4. Read the ARP cache. Lines look like:
        #    ? (10.0.0.1) at 94:83:c4:ab:8d:dc on en0 ifscope [ethernet]
        output = subprocess.run(
            ["arp", "-an"], capture_output=True, text=True
        ).stdout
        for line in output.splitlines():
            # "(incomplete)" = nobody answered; ff:ff:... = broadcast address
            if "incomplete" in line or "ff:ff:ff:ff:ff:ff" in line:
                continue
            words = line.split()
            if len(words) < 2:
                continue
            ip = words[1].strip("()")
            try:
                if ipaddress.ip_address(ip) in network:
                    found.add(ip)
            except ValueError:
                continue  # not an IP address; skip the line

        # 5. This Mac never appears in its own ARP answers, so add it.
        my_ip = self._local_ip(network)
        if my_ip:
            found.add(my_ip)

        return sorted(found, key=ipaddress.ip_address)

    @staticmethod
    def _admin_sweep(target: str) -> Optional[list[str]]:
        """
        Run "nmap -sn" as administrator through sudo, without a password.
        Returns the live IPs, or None if sudo isn't allowed for this exact
        command (sudo -n fails instead of asking for a password).
        """
        nmap_path = shutil.which("nmap")
        if not nmap_path:
            return None
        try:
            result = subprocess.run(
                ["sudo", "-n", nmap_path, "-sn", "-n", "-oG", "-", target],
                capture_output=True, text=True, timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0:
            return None
        # Grepable output lines look like:
        #   Host: 10.0.0.1 ()\tStatus: Up
        hosts = []
        for line in result.stdout.splitlines():
            if line.startswith("Host:") and "Status: Up" in line:
                hosts.append(line.split()[1])
        return hosts

    @staticmethod
    def _poke_addresses(network, rounds: int = 3, gap: float = 1.5) -> None:
        """
        Send one tiny UDP packet to every address, a few rounds apart.
        To send it, the Mac must first ask "who has this address?" (ARP),
        which is what fills the cache. Whether the packet itself arrives
        doesn't matter. Skipped for IPv6 and for very large ranges.
        """
        if network.version != 4 or network.num_addresses > 1024:
            return
        addresses = [str(ip) for ip in network.hosts()] or [str(network.network_address)]
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setblocking(False)
            for _ in range(rounds):
                for ip in addresses:
                    try:
                        sock.sendto(b"\x00", (ip, 9))  # port 9 = "discard"
                    except OSError:
                        pass  # unreachable or not answered yet; that's fine
                time.sleep(gap)

    @staticmethod
    def _local_ip(network) -> str:
        """This Mac's own address on the scanned network, or "" if it isn't on it."""
        if network.version != 4:
            return ""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                # connect() on UDP sends nothing; it just picks the route.
                sock.connect((str(network.network_address), 9))
                ip = sock.getsockname()[0]
        except OSError:
            return ""
        return ip if ipaddress.ip_address(ip) in network else ""

    def scan_target(
        self,
        target: str,
        ports: str = "1-1024",
        detect_os: bool = True,
        detect_services: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> list[HostResult]:
        def report(msg: str):
            if progress_callback:
                progress_callback(msg)

        args = ["-T4"]  # reasonable default timing
        if detect_services:
            args.append("-sV")
        if detect_os:
            args.append("-O")
        arg_string = " ".join(args)

        report(f"Finding live hosts on {target}...")
        hosts = self._discover_hosts(target)
        if not hosts:
            report("No hosts found.")
            return []
        host_list = " ".join(hosts)

        # -Pn: skip nmap's own alive-check. We already know these hosts are
        # up, and that check is what missed firewalled devices.
        args.append("-Pn")
        arg_string = " ".join(args)

        report(f"Scanning {len(hosts)} host(s) (ports {ports})...")
        try:
            self._nm.scan(hosts=host_list, ports=ports, arguments=arg_string)
        except nmap.PortScannerError as e:
            # OS detection (-O) requires elevated privileges on most systems.
            # Fall back to a scan without it rather than failing outright.
            if detect_os:
                report("OS detection requires elevated privileges — retrying without it.")
                args = [a for a in args if a != "-O"]
                self._nm.scan(hosts=host_list, ports=ports, arguments=" ".join(args))
                detect_os = False
            else:
                raise

        results: list[HostResult] = []
        hosts = self._nm.all_hosts()
        report(f"Found {len(hosts)} host(s) responding.")

        for host_ip in hosts:
            host_data = self._nm[host_ip]
            hostname = ""
            if host_data.hostname():
                hostname = host_data.hostname()
            else:
                try:
                    hostname = socket.gethostbyaddr(host_ip)[0]
                except (socket.herror, socket.gaierror):
                    hostname = ""

            mac = ""
            vendor = ""
            if "mac" in host_data["addresses"]:
                mac = host_data["addresses"]["mac"]
                vendors = host_data.get("vendor", {})
                vendor = vendors.get(mac, "")

            os_name = ""
            os_accuracy = ""
            if detect_os and host_data.get("osmatch"):
                best = host_data["osmatch"][0]
                os_name = best.get("name", "")
                os_accuracy = f"{best.get('accuracy', '')}%"

            ports_list: list[PortResult] = []
            for proto in host_data.all_protocols():
                for port in sorted(host_data[proto].keys()):
                    p = host_data[proto][port]
                    ports_list.append(
                        PortResult(
                            port=port,
                            protocol=proto,
                            state=p.get("state", ""),
                            service=p.get("name", ""),
                            product=p.get("product", ""),
                            version=p.get("version", ""),
                        )
                    )

            results.append(
                HostResult(
                    ip=host_ip,
                    hostname=hostname,
                    status=host_data.state(),
                    mac_address=mac,
                    vendor=vendor,
                    os_name=os_name,
                    os_accuracy=os_accuracy,
                    ports=ports_list,
                )
            )

        # Without root, nmap can't see hardware (MAC) addresses. The Mac's
        # ARP cache has them for every host we just scanned, so fill in
        # any blanks from there and look up each maker.
        arp = self._arp_table()
        for host in results:
            if not host.mac_address:
                host.mac_address = arp.get(host.ip, "")
            if host.mac_address and not host.vendor:
                host.vendor = self._vendor_for(host.mac_address)

        report("Scan complete.")
        return results

    # ---------- Hardware address / vendor helpers ----------

    @staticmethod
    def _arp_table() -> dict[str, str]:
        """IP -> MAC address from the macOS ARP cache ("arp -an")."""
        try:
            output = subprocess.run(
                ["arp", "-an"], capture_output=True, text=True
            ).stdout
        except OSError:
            return {}
        table = {}
        for line in output.splitlines():
            words = line.split()
            # ? (10.0.0.1) at 94:83:c4:ab:8d:dc on en0 ...
            if len(words) < 4 or words[2] != "at" or ":" not in words[3]:
                continue
            mac = words[3]
            if mac == "ff:ff:ff:ff:ff:ff":
                continue
            # macOS drops leading zeros ("0:7:a6:..."); put them back.
            mac = ":".join(part.zfill(2) for part in mac.split(":")).upper()
            table[words[1].strip("()")] = mac
        return table

    _vendor_db: Optional[dict[str, str]] = None

    @classmethod
    def _vendor_for(cls, mac: str) -> str:
        """Maker name for a MAC address, from nmap's own prefix list."""
        first_octet = int(mac[:2], 16)
        if first_octet & 0x02:
            # "Locally administered" bit set: a randomised private address,
            # as iPhones and Apple Watches use. No real maker to look up.
            return "(private address)"
        if cls._vendor_db is None:
            cls._vendor_db = cls._load_vendor_db()
        digits = mac.replace(":", "")
        # nmap's list has 6-digit prefixes plus some longer, more specific
        # ones; try the longest first.
        for length in (9, 8, 7, 6):
            vendor = cls._vendor_db.get(digits[:length])
            if vendor:
                return vendor
        return ""

    @staticmethod
    def _load_vendor_db() -> dict[str, str]:
        """Read nmap-mac-prefixes (installed with nmap) into a dict."""
        candidates = []
        nmap_path = shutil.which("nmap")
        if nmap_path:
            real = os.path.realpath(nmap_path)
            candidates.append(os.path.join(os.path.dirname(real), "..", "share", "nmap", "nmap-mac-prefixes"))
        candidates += [
            "/opt/homebrew/share/nmap/nmap-mac-prefixes",
            "/usr/local/share/nmap/nmap-mac-prefixes",
            "/usr/share/nmap/nmap-mac-prefixes",
        ]
        for path in candidates:
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    db = {}
                    for line in f:
                        if line.startswith("#") or " " not in line:
                            continue
                        prefix, name = line.rstrip("\n").split(" ", 1)
                        db[prefix.upper()] = name
                    return db
            except OSError:
                continue
        return {}
