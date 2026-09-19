"""
Network Scanner & Asset Manager — Tkinter GUI entry point.

Run with:
    python main.py
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from scanner import NetworkScanner, NmapNotFoundError
from asset_manager import AssetManager

APP_TITLE = "Network Scanner & Asset Manager"
ACCENT = "#C0392B"


class ScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x600")
        self.minsize(760, 480)

        self.asset_manager = AssetManager()
        self._scanner: NetworkScanner | None = None
        self._scan_thread: threading.Thread | None = None

        self._build_ui()

    # ---------- UI construction ----------

    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Accent.TButton", background=ACCENT, foreground="white")
        style.map("Accent.TButton", background=[("active", "#a93226")])

        # --- Top control bar ---
        top = ttk.Frame(self, padding=10)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="Target:").grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.target_var = tk.StringVar(value="127.0.0.1")
        target_entry = ttk.Entry(top, textvariable=self.target_var, width=28)
        target_entry.grid(row=0, column=1, sticky="w")

        ttk.Label(top, text="Ports:").grid(row=0, column=2, sticky="w", padx=(12, 4))
        self.ports_var = tk.StringVar(value="1-1024")
        ttk.Entry(top, textvariable=self.ports_var, width=14).grid(row=0, column=3, sticky="w")

        self.os_detect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="Detect OS", variable=self.os_detect_var).grid(
            row=0, column=4, padx=(12, 4)
        )

        self.service_detect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="Detect services", variable=self.service_detect_var).grid(
            row=0, column=5, padx=(4, 4)
        )

        self.scan_button = ttk.Button(
            top, text="Start Scan", style="Accent.TButton", command=self._on_scan_clicked
        )
        self.scan_button.grid(row=0, column=6, padx=(16, 0))

        top.columnconfigure(7, weight=1)

        # --- Status bar ---
        self.status_var = tk.StringVar(value="Ready.")
        status = ttk.Label(self, textvariable=self.status_var, padding=(10, 0), anchor="w")
        status.pack(side=tk.TOP, fill=tk.X)

        # --- Results table ---
        table_frame = ttk.Frame(self, padding=(10, 4))
        table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        columns = ("ip", "hostname", "status", "os", "vendor", "ports")
        headings = {
            "ip": "IP Address",
            "hostname": "Hostname",
            "status": "Status",
            "os": "OS Guess",
            "vendor": "Vendor",
            "ports": "Open Ports",
        }
        widths = {"ip": 120, "hostname": 160, "status": 80, "os": 220, "vendor": 140, "ports": 200}

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Bottom action bar ---
        bottom = ttk.Frame(self, padding=10)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)

        self.count_var = tk.StringVar(value="0 assets tracked")
        ttk.Label(bottom, textvariable=self.count_var).pack(side=tk.LEFT)

        ttk.Button(bottom, text="Export CSV", command=self._on_export_csv).pack(
            side=tk.RIGHT, padx=(6, 0)
        )
        ttk.Button(bottom, text="Export XLSX", command=self._on_export_xlsx).pack(
            side=tk.RIGHT, padx=(6, 0)
        )
        ttk.Button(bottom, text="Clear Inventory", command=self._on_clear).pack(
            side=tk.RIGHT, padx=(6, 0)
        )

    # ---------- Scan handling ----------

    def _on_scan_clicked(self):
        target = self.target_var.get().strip()
        ports = self.ports_var.get().strip()
        if not target:
            messagebox.showwarning(APP_TITLE, "Enter a target IP, hostname, or CIDR range.")
            return

        self.scan_button.configure(state="disabled")
        self._set_status(f"Starting scan of {target}...")

        self._scan_thread = threading.Thread(
            target=self._run_scan,
            args=(target, ports, self.os_detect_var.get(), self.service_detect_var.get()),
            daemon=True,
        )
        self._scan_thread.start()

    def _run_scan(self, target: str, ports: str, detect_os: bool, detect_services: bool):
        try:
            if self._scanner is None:
                self._scanner = NetworkScanner()

            results = self._scanner.scan_target(
                target=target,
                ports=ports or "1-1024",
                detect_os=detect_os,
                detect_services=detect_services,
                progress_callback=lambda msg: self.after(0, self._set_status, msg),
            )
            self.after(0, self._on_scan_complete, results)
        except NmapNotFoundError as e:
            self.after(0, self._on_scan_error, str(e))
        except Exception as e:  # noqa: BLE001 - surface any scan failure to the user
            self.after(0, self._on_scan_error, f"Scan failed: {e}")

    def _on_scan_complete(self, results):
        self.asset_manager.add_results(results)
        self._refresh_table()
        self._set_status(f"Scan complete — {len(results)} host(s) found.")
        self.scan_button.configure(state="normal")

    def _on_scan_error(self, message: str):
        self._set_status("Scan failed.")
        self.scan_button.configure(state="normal")
        messagebox.showerror(APP_TITLE, message)

    def _set_status(self, message: str):
        self.status_var.set(message)

    # ---------- Table / export ----------

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for host in self.asset_manager.all_hosts():
            self.tree.insert(
                "",
                tk.END,
                values=(
                    host.ip,
                    host.hostname,
                    host.status,
                    f"{host.os_name} {host.os_accuracy}".strip(),
                    host.vendor,
                    host.open_ports_summary,
                ),
            )
        self.count_var.set(f"{len(self.asset_manager)} asset(s) tracked")

    def _on_clear(self):
        if len(self.asset_manager) == 0:
            return
        if messagebox.askyesno(APP_TITLE, "Clear the current asset inventory?"):
            self.asset_manager.clear()
            self._refresh_table()
            self._set_status("Inventory cleared.")

    def _on_export_csv(self):
        self._export(extension="csv")

    def _on_export_xlsx(self):
        self._export(extension="xlsx")

    def _export(self, extension: str):
        if len(self.asset_manager) == 0:
            messagebox.showinfo(APP_TITLE, "Nothing to export yet — run a scan first.")
            return

        filetypes = [("CSV files", "*.csv")] if extension == "csv" else [("Excel files", "*.xlsx")]
        path = filedialog.asksaveasfilename(
            defaultextension=f".{extension}",
            filetypes=filetypes,
            initialfile=f"assets.{extension}",
        )
        if not path:
            return

        try:
            if extension == "csv":
                self.asset_manager.export_csv(path)
            else:
                self.asset_manager.export_xlsx(path)
            self._set_status(f"Exported {len(self.asset_manager)} asset(s) to {path}")
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(APP_TITLE, f"Export failed: {e}")


if __name__ == "__main__":
    app = ScannerApp()
    app.mainloop()
