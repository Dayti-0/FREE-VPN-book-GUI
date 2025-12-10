# -*- coding: utf-8 -*-
"""Interface graphique moderne pour l'application VPNBook GUI."""

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
from network import fetch_vpnbook_password_image
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

# Configuration du thème
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Couleurs personnalisées
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_card": "#16213e",
    "accent_blue": "#0f3460",
    "accent_green": "#4ecca3",
    "accent_red": "#e94560",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0a0",
    "button_hover": "#1e5f74",
}

stop_ping_thread = False
ping_thread = None
show_password = False


class VPNApp(ctk.CTk):
    """Application principale VPN avec interface moderne."""

    def __init__(self):
        super().__init__()

        self.title("VPNBook - Connexion VPN Gratuite")
        self.geometry("700x850")
        self.minsize(650, 750)

        # Configuration de la grille principale
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=0)  # Server section
        self.grid_rowconfigure(2, weight=0)  # Auth section
        self.grid_rowconfigure(3, weight=0)  # Options section
        self.grid_rowconfigure(4, weight=0)  # Actions section
        self.grid_rowconfigure(5, weight=1)  # Logs section

        self._create_header()
        self._create_server_section()
        self._create_auth_section()
        self._create_options_section()
        self._create_actions_section()
        self._create_logs_section()

        # Démarrer la mise à jour des latences
        threading.Thread(target=update_server_latencies, daemon=True).start()
        self.after(100, self._process_latency_queue)

    def _create_header(self):
        """Crée l'en-tête de l'application."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Titre principal
        title_label = ctk.CTkLabel(
            header_frame,
            text="VPNBook",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS["accent_green"]
        )
        title_label.pack(pady=(0, 5))

        # Sous-titre
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Connexion VPN gratuite et sécurisée",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"]
        )
        subtitle_label.pack()

        # Indicateur de statut
        self.status_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        self.status_frame.pack(pady=(10, 0))

        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color=COLORS["accent_red"]
        )
        self.status_indicator.pack(side="left", padx=(0, 5))

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Déconnecté",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"]
        )
        self.status_label.pack(side="left")

    def _create_server_section(self):
        """Crée la section de sélection du serveur."""
        server_card = ctk.CTkFrame(self, corner_radius=15)
        server_card.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Titre de section
        section_title = ctk.CTkLabel(
            server_card,
            text="Sélection du serveur",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        section_title.pack(padx=20, pady=(15, 10), anchor="w")

        # Combobox serveur
        self.selected_server = ctk.StringVar(value=list(SERVER_CHOICES.keys())[0])
        self.server_combobox = ctk.CTkComboBox(
            server_card,
            variable=self.selected_server,
            values=list(SERVER_CHOICES.keys()),
            width=400,
            height=40,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12),
            corner_radius=10,
            state="readonly"
        )
        self.server_combobox.pack(padx=20, pady=(0, 5), fill="x")

        # Label latence
        self.label_latency = ctk.CTkLabel(
            server_card,
            text="Latence : En attente...",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.label_latency.pack(padx=20, pady=(5, 15), anchor="w")

    def _create_auth_section(self):
        """Crée la section d'authentification."""
        auth_card = ctk.CTkFrame(self, corner_radius=15)
        auth_card.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Titre de section
        section_title = ctk.CTkLabel(
            auth_card,
            text="Authentification",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        section_title.pack(padx=20, pady=(15, 10), anchor="w")

        # Frame pour identifiant
        id_frame = ctk.CTkFrame(auth_card, fg_color="transparent")
        id_frame.pack(padx=20, pady=5, fill="x")

        id_label = ctk.CTkLabel(
            id_frame,
            text="Identifiant",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        id_label.pack(anchor="w")

        self.entry_id = ctk.CTkEntry(
            id_frame,
            height=38,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            state="disabled"
        )
        self.entry_id.pack(fill="x", pady=(3, 0))
        self.entry_id.configure(state="normal")
        self.entry_id.insert(0, IDENTIFIANT)
        self.entry_id.configure(state="disabled")

        # Frame pour mot de passe
        pwd_frame = ctk.CTkFrame(auth_card, fg_color="transparent")
        pwd_frame.pack(padx=20, pady=10, fill="x")

        pwd_label = ctk.CTkLabel(
            pwd_frame,
            text="Mot de passe",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        pwd_label.pack(anchor="w")

        # Image du mot de passe
        self.label_mdp_img = ctk.CTkLabel(pwd_frame, text="")
        self.label_mdp_img.pack(pady=8)

        # Charger l'image du mot de passe
        self._load_password_image()

        self.entry_mdp = ctk.CTkEntry(
            pwd_frame,
            height=38,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            show="●"
        )
        self.entry_mdp.pack(fill="x", pady=(3, 0))

        # Charger le mot de passe enregistré
        ancien_mdp = self._charger_mot_de_passe()
        if ancien_mdp:
            self.entry_mdp.insert(0, ancien_mdp)

        # Boutons mot de passe
        btn_frame = ctk.CTkFrame(pwd_frame, fg_color="transparent")
        btn_frame.pack(pady=10, fill="x")

        self.bouton_show_mdp = ctk.CTkButton(
            btn_frame,
            text="Afficher",
            width=120,
            height=32,
            corner_radius=8,
            fg_color=COLORS["accent_blue"],
            hover_color=COLORS["button_hover"],
            command=self._toggle_mot_de_passe
        )
        self.bouton_show_mdp.pack(side="left", padx=(0, 10))

        self.bouton_refresh = ctk.CTkButton(
            btn_frame,
            text="Rafraîchir image",
            width=140,
            height=32,
            corner_radius=8,
            fg_color=COLORS["accent_blue"],
            hover_color=COLORS["button_hover"],
            command=self._rafraichir_image_mdp
        )
        self.bouton_refresh.pack(side="left")

    def _create_options_section(self):
        """Crée la section des options."""
        options_card = ctk.CTkFrame(self, corner_radius=15)
        options_card.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Titre de section
        section_title = ctk.CTkLabel(
            options_card,
            text="Options",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        section_title.pack(padx=20, pady=(15, 10), anchor="w")

        # Split tunneling
        self.split_tunneling_var = ctk.BooleanVar(value=False)

        split_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        split_frame.pack(padx=20, pady=(0, 5), fill="x")

        self.split_checkbox = ctk.CTkCheckBox(
            split_frame,
            text="Activer le split tunneling",
            variable=self.split_tunneling_var,
            font=ctk.CTkFont(size=13),
            corner_radius=5,
            checkbox_width=22,
            checkbox_height=22
        )
        self.split_checkbox.pack(anchor="w")

        split_note = ctk.CTkLabel(
            options_card,
            text="Activé : seul le trafic VPN passe par le tunnel. Désactivé : tout le trafic passe par le VPN.",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            wraplength=600,
            anchor="w",
            justify="left"
        )
        split_note.pack(padx=20, pady=(0, 15), anchor="w")

    def _create_actions_section(self):
        """Crée la section des actions."""
        actions_card = ctk.CTkFrame(self, corner_radius=15)
        actions_card.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # Frame pour les boutons
        btn_frame = ctk.CTkFrame(actions_card, fg_color="transparent")
        btn_frame.pack(padx=20, pady=15, fill="x")

        # Bouton Connecter
        self.bouton_connecter = ctk.CTkButton(
            btn_frame,
            text="Se connecter",
            width=180,
            height=45,
            corner_radius=10,
            fg_color=COLORS["accent_green"],
            hover_color="#3ba583",
            text_color="#000000",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._connecter
        )
        self.bouton_connecter.pack(side="left", padx=(0, 10))

        # Bouton VPN rapide
        self.bouton_fastest = ctk.CTkButton(
            btn_frame,
            text="VPN le plus rapide",
            width=180,
            height=45,
            corner_radius=10,
            fg_color=COLORS["accent_blue"],
            hover_color=COLORS["button_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._connecter_plus_rapide
        )
        self.bouton_fastest.pack(side="left", padx=(0, 10))

        # Bouton Déconnecter
        self.bouton_deconnecter = ctk.CTkButton(
            btn_frame,
            text="Se déconnecter",
            width=180,
            height=45,
            corner_radius=10,
            fg_color=COLORS["accent_red"],
            hover_color="#c73e54",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._deconnecter_action
        )
        self.bouton_deconnecter.pack(side="left")

        # Barre de progression
        self.progress = ctk.CTkProgressBar(
            actions_card,
            width=400,
            height=8,
            corner_radius=4,
            progress_color=COLORS["accent_green"]
        )
        self.progress.pack(padx=20, pady=(0, 15), fill="x")
        self.progress.set(0)

    def _create_logs_section(self):
        """Crée la section des logs."""
        logs_card = ctk.CTkFrame(self, corner_radius=15)
        logs_card.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="nsew")

        # Configuration de la grille
        logs_card.grid_columnconfigure(0, weight=1)
        logs_card.grid_rowconfigure(1, weight=1)

        # Header des logs
        logs_header = ctk.CTkFrame(logs_card, fg_color="transparent")
        logs_header.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="ew")

        section_title = ctk.CTkLabel(
            logs_header,
            text="Journal d'activité",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        section_title.pack(side="left")

        self.bouton_save_logs = ctk.CTkButton(
            logs_header,
            text="Sauvegarder",
            width=110,
            height=30,
            corner_radius=8,
            fg_color=COLORS["accent_blue"],
            hover_color=COLORS["button_hover"],
            font=ctk.CTkFont(size=12),
            command=self._sauvegarder_logs
        )
        self.bouton_save_logs.pack(side="right")

        # Zone de texte des logs
        self.text_log = ctk.CTkTextbox(
            logs_card,
            corner_radius=10,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            state="disabled"
        )
        self.text_log.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="nsew")

    # -------------------- Utilitaires --------------------

    def _ajouter_log(self, texte):
        """Ajoute une ligne de log dans la zone de texte."""
        self.text_log.configure(state="normal")
        self.text_log.insert("end", texte + "\n")
        self.text_log.see("end")
        self.text_log.configure(state="disabled")

    def _charger_mot_de_passe(self):
        if os.path.exists(MDP_FILE):
            with open(MDP_FILE, "r") as f:
                data = json.load(f)
                return data.get("mot_de_passe", "")
        return ""

    def _enregistrer_mot_de_passe(self, mot_de_passe):
        with open(MDP_FILE, "w") as f:
            json.dump({"mot_de_passe": mot_de_passe}, f)

    def _load_password_image(self):
        """Charge l'image du mot de passe en arrière-plan."""
        def worker():
            mdp_image = fetch_vpnbook_password_image()
            if mdp_image:
                self.after(0, lambda: self._set_password_image(mdp_image))
        threading.Thread(target=worker, daemon=True).start()

    def _set_password_image(self, image):
        """Met à jour l'image du mot de passe."""
        self.label_mdp_img.configure(image=image)
        self.label_mdp_img.image = image

    def _update_status(self, connected):
        """Met à jour l'indicateur de statut."""
        if connected:
            self.status_indicator.configure(text_color=COLORS["accent_green"])
            self.status_label.configure(text="Connecté")
        else:
            self.status_indicator.configure(text_color=COLORS["accent_red"])
            self.status_label.configure(text="Déconnecté")

    def _formater_message_erreur(self, output):
        """Retourne un message plus explicite en cas d'échec rasdial."""
        if not output:
            return "Échec de la connexion : aucune sortie fournie par rasdial."

        texte = output if isinstance(output, str) else str(output)
        texte_clean = texte.replace("\r", "").strip()

        if "807" in texte_clean:
            return (
                "Erreur 807 : la connexion a été interrompue (latence élevée ou serveur saturé).\n"
                "Essayez un autre serveur VPN ou réessayez dans quelques instants.\n\n"
                f"Détails rasdial : {texte_clean}"
            )

        if "619" in texte_clean:
            return (
                "Erreur 619 : impossible d'établir la session.\n"
                "Vérifiez vos identifiants, le réseau ou désactivez temporairement votre antivirus.\n\n"
                f"Détails rasdial : {texte_clean}"
            )

        return f"Échec de la connexion : {texte_clean}"

    # -------------------- Actions VPN --------------------

    def _connecter(self):
        self._ajouter_log("Tentative de connexion...")
        self._start_progress()
        self.bouton_connecter.configure(state="disabled")
        self.bouton_fastest.configure(state="disabled")
        threading.Thread(target=self._connecter_thread).start()

    def _connecter_plus_rapide(self):
        self._ajouter_log("Recherche du serveur le plus rapide...")
        self._start_progress()
        self.bouton_connecter.configure(state="disabled")
        self.bouton_fastest.configure(state="disabled")
        threading.Thread(target=self._connecter_plus_rapide_thread).start()

    def _connecter_plus_rapide_thread(self):
        country, ip, latency = find_fastest_server()
        if not ip:
            self.after(0, self._stop_progress)
            self.after(0, lambda: messagebox.showerror("Erreur", "Aucun serveur joignable."))
            self.after(0, lambda: self._ajouter_log("Impossible de déterminer le serveur le plus rapide."))
            return
        self.after(0, lambda: self._ajouter_log(f"Serveur choisi : {ip} ({country}) - Latence : {latency} ms"))
        self.after(0, lambda: self._ajouter_log("Tentative de connexion..."))
        threading.Thread(target=self._connecter_thread, args=(country, ip)).start()

    def _connecter_thread(self, country=None, ip=None):
        global stop_ping_thread

        if ip is None or country is None:
            label = self.selected_server.get()
            label = re.sub(r"\s*\(.*?ms\)", "", label).strip()
            country, ip = SERVER_CHOICES[label]

        mot_de_passe = self.entry_mdp.get()
        split_tunneling_enabled = self.split_tunneling_var.get()

        if est_connecte():
            self._ajouter_log("Déconnexion de la session VPN existante...")
            deconnecter_vpn()

        try:
            if split_tunneling_enabled:
                self._ajouter_log("Split tunneling activé : seul le trafic VPN passera par le tunnel.")
            else:
                self._ajouter_log("Split tunneling désactivé : tout le trafic passera par le VPN.")

            self._ajouter_log(f"Création ou mise à jour de la connexion vers {ip}...")
            creer_ou_mettre_a_jour_vpn(ip, split_tunneling=split_tunneling_enabled)

            self._ajouter_log("Connexion au VPN...")
            connecter_vpn(mot_de_passe)
            self._enregistrer_mot_de_passe(mot_de_passe)

            self.after(0, self._stop_progress)
            self.after(0, lambda: self._update_status(True))
            self.after(0, lambda: messagebox.showinfo("Succès", "Connexion établie avec succès."))
            self._ajouter_log("Connexion établie avec succès.")

            if country in ASCII_LOGOS:
                self._ajouter_log(ASCII_LOGOS[country])

            self._lancer_ping_thread(ip)

        except subprocess.CalledProcessError as e:
            message = self._formater_message_erreur(getattr(e, "output", ""))
            self.after(0, self._stop_progress)
            self.after(0, lambda: self._update_status(False))
            self.after(0, lambda: messagebox.showerror("Erreur", message))
            self._ajouter_log(message)

    def _start_progress(self):
        """Démarre l'animation de la barre de progression."""
        self._progress_running = True
        self._animate_progress()

    def _animate_progress(self):
        """Animation de la barre de progression."""
        if hasattr(self, "_progress_running") and self._progress_running:
            current = self.progress.get()
            if current >= 1:
                self.progress.set(0)
            else:
                self.progress.set(current + 0.02)
            self.after(50, self._animate_progress)

    def _stop_progress(self):
        """Arrête la barre de progression."""
        self._progress_running = False
        self.progress.set(0)
        self.bouton_connecter.configure(state="normal")
        self.bouton_fastest.configure(state="normal")

    def _deconnecter_action(self):
        global stop_ping_thread
        stop_ping_thread = True
        self._ajouter_log("Tentative de déconnexion...")
        if deconnecter_vpn():
            self._update_status(False)
            messagebox.showinfo("Déconnexion", "Vous avez été déconnecté du VPN.")
            self._ajouter_log("Déconnexion réussie.")
            self.label_latency.configure(text="Latence : N/A")
        else:
            messagebox.showerror("Erreur", "Échec de la déconnexion ou aucune connexion n'était active.")
            self._ajouter_log("Échec de la déconnexion ou aucune connexion active.")

    def _measure_and_update_latency(self, ip):
        latence_ms = measure_latency(ip)
        if latence_ms is not None:
            self.after(0, lambda: self.label_latency.configure(text=f"Latence : {latence_ms} ms"))
        else:
            self.after(0, lambda: self.label_latency.configure(text="Latence : N/A"))

    def _ping_serveur(self, ip):
        global stop_ping_thread
        stop_ping_thread = False
        while not stop_ping_thread:
            if est_connecte():
                self._measure_and_update_latency(ip)
            else:
                self.after(0, lambda: self.label_latency.configure(text="Latence : N/A"))
            time.sleep(2)

    def _lancer_ping_thread(self, ip):
        global ping_thread
        if ping_thread and ping_thread.is_alive():
            return
        ping_thread = threading.Thread(target=self._ping_serveur, args=(ip,), daemon=True)
        ping_thread.start()

    def _process_latency_queue(self):
        try:
            new_values = latency_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            self.server_combobox.configure(values=new_values)
            if new_values:
                self.server_combobox.set(new_values[0])
        finally:
            self.after(100, self._process_latency_queue)

    def _toggle_mot_de_passe(self):
        global show_password
        show_password = not show_password
        if show_password:
            self.entry_mdp.configure(show="")
            self.bouton_show_mdp.configure(text="Masquer")
        else:
            self.entry_mdp.configure(show="●")
            self.bouton_show_mdp.configure(text="Afficher")

    def _sauvegarder_logs(self):
        """Sauvegarde le contenu des logs dans un fichier texte."""
        with open("vpn_logs.txt", "w", encoding="utf-8") as f:
            contenu = self.text_log.get("1.0", "end").strip()
            f.write(contenu)
        messagebox.showinfo("Sauvegarde", "Les logs ont été sauvegardés dans vpn_logs.txt")

    def _rafraichir_image_mdp(self):
        """Recharge l'image du mot de passe et met à jour le label."""
        def worker():
            img = fetch_vpnbook_password_image()
            if img:
                self.after(0, lambda: self._set_password_image(img))
        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    app = VPNApp()
    app.mainloop()
