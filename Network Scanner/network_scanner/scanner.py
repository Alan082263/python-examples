"""
Core scanning engine. Wraps python-nmap to run host discovery, port
scanning, service/version detection and OS fingerprinting, and returns
plain Python data structures (no GUI or file-format knowledge here).
"""

from __future__ import annotations

import shutil
import socket
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

        report(f"Scanning {target} (ports {ports})...")
        try:
            self._nm.scan(hosts=target, ports=ports, arguments=arg_string)
        except nmap.PortScannerError as e:
            # OS detection (-O) requires elevated privileges on most systems.
            # Fall back to a scan without it rather than failing outright.
            if detect_os:
                report("OS detection requires elevated privileges — retrying without it.")
                args = [a for a in args if a != "-O"]
                self._nm.scan(hosts=target, ports=ports, arguments=" ".join(args))
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

        report("Scan complete.")
        return results
