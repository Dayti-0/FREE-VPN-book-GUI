# -*- coding: utf-8 -*-
"""Interface graphique compacte pour VPNBook."""

import customtkinter as ctk
from tkinter import messagebox
import json
import os
import subprocess
import threading
import queue
import time
import re

from constants import IDENTIFIANT, MDP_FILE, SERVER_CHOICES, ASCII_LOGOS
from network import fetch_vpnbook_password
from vpn_ops import (
    est_connecte,
    deconnecter_vpn,
    creer_ou_mettre_a_jour_vpn,
    connecter_vpn,
    update_server_latencies,
    find_fastest_server,
    measure_latency,
    latency_queue,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "green": "#4ecca3",
    "red": "#e94560",
    "blue": "#0f3460",
    "gray": "#a0a0a0",
}

stop_ping_thread = False
ping_thread = None


class VPNApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VPNBook")
        self.geometry("380x420")
        self.minsize(350, 380)
        self.resizable(True, True)

        # Main container
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Header: Title + Status
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(header, text="VPNBook", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=COLORS["green"]).pack(side="left")

        self.status = ctk.CTkLabel(header, text="● Déconnecté", font=ctk.CTkFont(size=11),
                                   text_color=COLORS["red"])
        self.status.pack(side="right")

        # Server selection
        ctk.CTkLabel(main, text="Serveur:", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x")
        self.server_var = ctk.StringVar(value=list(SERVER_CHOICES.keys())[0])
        self.server_combo = ctk.CTkComboBox(main, variable=self.server_var,
                                            values=list(SERVER_CHOICES.keys()),
                                            height=30, state="readonly")
        self.server_combo.pack(fill="x", pady=(2, 8))

        # Password
        pwd_frame = ctk.CTkFrame(main, fg_color="transparent")
        pwd_frame.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(pwd_frame, text="Mot de passe:", font=ctk.CTkFont(size=12)).pack(side="left")

        self.pwd_entry = ctk.CTkEntry(pwd_frame, height=28, width=150, show="●")
        self.pwd_entry.pack(side="left", padx=(8, 5))

        self.show_btn = ctk.CTkButton(pwd_frame, text="👁", width=30, height=28,
                                      command=self._toggle_pwd)
        self.show_btn.pack(side="left")

        ctk.CTkButton(pwd_frame, text="↻", width=30, height=28,
                      command=self._refresh_pwd).pack(side="left", padx=(5, 0))

        # Load saved password or fetch from web
        saved_pwd = self._load_pwd()
        if saved_pwd:
            self.pwd_entry.insert(0, saved_pwd)
        else:
            self._fetch_pwd_async()

        # Action buttons
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x", pady=8)
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(btn_frame, text="Connecter", fg_color=COLORS["green"],
                      text_color="#000", height=35, command=self._connect
                      ).grid(row=0, column=0, padx=(0, 3), sticky="ew")

        ctk.CTkButton(btn_frame, text="Auto", fg_color=COLORS["blue"],
                      height=35, command=self._auto_connect
                      ).grid(row=0, column=1, padx=3, sticky="ew")

        ctk.CTkButton(btn_frame, text="Déco", fg_color=COLORS["red"],
                      height=35, command=self._disconnect
                      ).grid(row=0, column=2, padx=(3, 0), sticky="ew")

        # Progress bar
        self.progress = ctk.CTkProgressBar(main, height=5, progress_color=COLORS["green"])
        self.progress.pack(fill="x", pady=(0, 8))
        self.progress.set(0)

        # Latency label
        self.latency_label = ctk.CTkLabel(main, text="Latence: --",
                                          font=ctk.CTkFont(size=11), text_color=COLORS["gray"])
        self.latency_label.pack(anchor="w")

        # Logs
        self.logs = ctk.CTkTextbox(main, height=120, font=ctk.CTkFont(family="Consolas", size=10),
                                   state="disabled")
        self.logs.pack(fill="both", expand=True, pady=(5, 0))

        # Start latency updates
        threading.Thread(target=update_server_latencies, daemon=True).start()
        self.after(100, self._process_queue)

        self._show_pwd = False

    def _log(self, msg):
        self.logs.configure(state="normal")
        self.logs.insert("end", msg + "\n")
        self.logs.see("end")
        self.logs.configure(state="disabled")

    def _load_pwd(self):
        if os.path.exists(MDP_FILE):
            with open(MDP_FILE) as f:
                return json.load(f).get("mot_de_passe", "")
        return ""

    def _save_pwd(self, pwd):
        with open(MDP_FILE, "w") as f:
            json.dump({"mot_de_passe": pwd}, f)

    def _fetch_pwd_async(self):
        def worker():
            pwd = fetch_vpnbook_password()
            if pwd:
                self.after(0, lambda: self._set_pwd(pwd))
                self.after(0, lambda: self._log(f"Mot de passe: {pwd}"))
            else:
                self.after(0, lambda: self._log("Échec récupération mot de passe"))
        threading.Thread(target=worker, daemon=True).start()

    def _set_pwd(self, pwd):
        self.pwd_entry.delete(0, "end")
        self.pwd_entry.insert(0, pwd)

    def _toggle_pwd(self):
        self._show_pwd = not self._show_pwd
        self.pwd_entry.configure(show="" if self._show_pwd else "●")

    def _refresh_pwd(self):
        self._log("Récupération du mot de passe...")
        self._fetch_pwd_async()

    def _update_status(self, connected):
        if connected:
            self.status.configure(text="● Connecté", text_color=COLORS["green"])
        else:
            self.status.configure(text="● Déconnecté", text_color=COLORS["red"])

    def _start_progress(self):
        self._running = True
        self._animate()

    def _animate(self):
        if getattr(self, "_running", False):
            v = self.progress.get()
            self.progress.set(0 if v >= 1 else v + 0.03)
            self.after(40, self._animate)

    def _stop_progress(self):
        self._running = False
        self.progress.set(0)

    def _connect(self):
        self._log("Connexion...")
        self._start_progress()
        threading.Thread(target=self._connect_thread).start()

    def _auto_connect(self):
        self._log("Recherche serveur rapide...")
        self._start_progress()
        threading.Thread(target=self._auto_thread).start()

    def _auto_thread(self):
        country, ip, lat = find_fastest_server()
        if not ip:
            self.after(0, self._stop_progress)
            self.after(0, lambda: self._log("Aucun serveur disponible"))
            return
        self.after(0, lambda: self._log(f"Serveur: {ip} ({lat}ms)"))
        self._connect_thread(country, ip)

    def _connect_thread(self, country=None, ip=None):
        global stop_ping_thread

        if not ip:
            label = re.sub(r"\s*\(.*?ms\)", "", self.server_var.get()).strip()
            country, ip = SERVER_CHOICES[label]

        pwd = self.pwd_entry.get()

        if est_connecte():
            self._log("Déconnexion en cours...")
            deconnecter_vpn()

        try:
            self._log(f"Connexion à {ip}...")
            creer_ou_mettre_a_jour_vpn(ip, split_tunneling=False)
            connecter_vpn(pwd)
            self._save_pwd(pwd)

            self.after(0, self._stop_progress)
            self.after(0, lambda: self._update_status(True))
            self._log("Connecté!")

            if country in ASCII_LOGOS:
                self._log(ASCII_LOGOS[country])

            self._start_ping(ip)

        except subprocess.CalledProcessError as e:
            out = getattr(e, "output", "")
            msg = "Erreur 807: serveur saturé" if "807" in str(out) else f"Erreur: {out}"
            self.after(0, self._stop_progress)
            self._log(msg)

    def _disconnect(self):
        global stop_ping_thread
        stop_ping_thread = True
        self._log("Déconnexion...")
        if deconnecter_vpn():
            self._update_status(False)
            self._log("Déconnecté")
            self.latency_label.configure(text="Latence: --")
        else:
            self._log("Échec déconnexion")

    def _start_ping(self, ip):
        global ping_thread, stop_ping_thread
        stop_ping_thread = False
        if ping_thread and ping_thread.is_alive():
            return
        ping_thread = threading.Thread(target=self._ping_loop, args=(ip,), daemon=True)
        ping_thread.start()

    def _ping_loop(self, ip):
        global stop_ping_thread
        while not stop_ping_thread:
            if est_connecte():
                lat = measure_latency(ip)
                txt = f"Latence: {lat}ms" if lat else "Latence: --"
                self.after(0, lambda t=txt: self.latency_label.configure(text=t))
            time.sleep(2)

    def _process_queue(self):
        try:
            vals = latency_queue.get_nowait()
            self.server_combo.configure(values=vals)
            if vals:
                self.server_combo.set(vals[0])
        except queue.Empty:
            pass
        self.after(100, self._process_queue)


if __name__ == "__main__":
    VPNApp().mainloop()
