# -*- coding: utf-8 -*-
"""Interface graphique principale pour l'application VPNBook GUI."""

import tkinter as tk
from tkinter import messagebox
import json
import os
import subprocess
import threading
import queue
import tkinter.ttk as ttk
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

stop_ping_thread = False
ping_thread = None
show_password = False


# -------------------- Utilitaires / Logs --------------------
def ajouter_log(texte):
    """Ajoute une ligne de log dans la zone de texte."""
    text_log.config(state='normal')
    text_log.insert('end', texte + '\n')
    text_log.see('end')
    text_log.config(state='disabled')


def charger_mot_de_passe():
    if os.path.exists(MDP_FILE):
        with open(MDP_FILE, 'r') as f:
            data = json.load(f)
            return data.get('mot_de_passe', '')
    return ''


def enregistrer_mot_de_passe(mot_de_passe):
    with open(MDP_FILE, 'w') as f:
        json.dump({'mot_de_passe': mot_de_passe}, f)


# -------------------- Connexion / VPN --------------------
def connecter():
    ajouter_log("Tentative de connexion...")
    progress.config(mode='indeterminate')
    progress.start()
    bouton_connecter.config(state='disabled')
    bouton_fastest.config(state='disabled')
    threading.Thread(target=connecter_thread).start()


def connecter_plus_rapide():
    ajouter_log("Recherche du serveur le plus rapide...")
    progress.config(mode='indeterminate')
    progress.start()
    bouton_connecter.config(state='disabled')
    bouton_fastest.config(state='disabled')
    threading.Thread(target=connecter_plus_rapide_thread).start()


def connecter_plus_rapide_thread():
    country, ip, latency = find_fastest_server()
    if not ip:
        fenetre.after(0, stop_progress)
        fenetre.after(0, lambda: messagebox.showerror("Erreur", "Aucun serveur joignable."))
        fenetre.after(0, lambda: ajouter_log("Impossible de déterminer le serveur le plus rapide."))
        return
    fenetre.after(0, lambda: ajouter_log(f"Serveur choisi automatiquement : {ip} ({country}) avec une latence de {latency} ms"))
    fenetre.after(0, lambda: ajouter_log("Tentative de connexion..."))
    threading.Thread(target=connecter_thread, args=(country, ip)).start()


def connecter_thread(country=None, ip=None):
    if ip is None or country is None:
        label = selected_server.get()
        label = re.sub(r"\s*\(.*?ms\)", "", label).strip()
        country, ip = SERVER_CHOICES[label]
    mot_de_passe = entry_mdp.get()

    if est_connecte():
        ajouter_log("Déconnexion de la session VPN existante...")
        deconnecter_vpn()

    try:
        ajouter_log(f"Création ou mise à jour de la connexion vers {ip}...")
        creer_ou_mettre_a_jour_vpn(ip)

        ajouter_log("Connexion au VPN...")
        connecter_vpn(mot_de_passe)
        enregistrer_mot_de_passe(mot_de_passe)
        fenetre.after(0, stop_progress)
        fenetre.after(0, lambda: messagebox.showinfo("Succès", "Connexion établie avec succès."))
        ajouter_log("Connexion établie avec succès.")

        if country in ASCII_LOGOS:
            ajouter_log(ASCII_LOGOS[country])

        lancer_ping_thread(ip)

    except subprocess.CalledProcessError as e:  # type: ignore[name-defined]
        fenetre.after(0, stop_progress)
        fenetre.after(0, lambda: messagebox.showerror("Erreur", f"Échec de la connexion : {e.output}"))
        ajouter_log(f"Échec de la connexion : {e.output}")


def stop_progress():
    progress.stop()
    progress.config(mode='determinate', value=0)
    bouton_connecter.config(state='normal')
    bouton_fastest.config(state='normal')


def deconnecter_action():
    global stop_ping_thread
    stop_ping_thread = True
    ajouter_log("Tentative de déconnexion...")
    if deconnecter_vpn():
        messagebox.showinfo("Déconnexion", "Vous avez été déconnecté du VPN.")
        ajouter_log("Déconnexion réussie.")
        label_latency.config(text="Latence : N/A")
    else:
        messagebox.showerror("Erreur", "Échec de la déconnexion ou aucune connexion n'était active.")
        ajouter_log("Échec de la déconnexion ou aucune connexion active.")


def measure_and_update_latency(ip):
    latence_ms = measure_latency(ip)
    if latence_ms is not None:
        fenetre.after(0, lambda: label_latency.config(text=f"Latence : {latence_ms} ms"))
    else:
        fenetre.after(0, lambda: label_latency.config(text="Latence : N/A"))


def ping_serveur(ip):
    global stop_ping_thread
    stop_ping_thread = False
    while not stop_ping_thread:
        if est_connecte():
            measure_and_update_latency(ip)
        else:
            fenetre.after(0, lambda: label_latency.config(text="Latence : N/A"))
        time.sleep(2)


def lancer_ping_thread(ip):
    global ping_thread
    if ping_thread and ping_thread.is_alive():
        return
    ping_thread = threading.Thread(target=ping_serveur, args=(ip,), daemon=True)
    ping_thread.start()


def process_latency_queue():
    try:
        new_values = latency_queue.get_nowait()
    except queue.Empty:
        pass
    else:
        server_combobox.config(values=new_values)
        server_combobox.current(0)
    finally:
        fenetre.after(100, process_latency_queue)


def toggle_mot_de_passe():
    global show_password
    show_password = not show_password
    if show_password:
        entry_mdp.config(show='')
        bouton_show_mdp.config(text="Masquer le mot de passe")
    else:
        entry_mdp.config(show='*')
        bouton_show_mdp.config(text="Afficher le mot de passe")


def sauvegarder_logs():
    """Sauvegarder le contenu des logs dans un fichier texte."""
    with open("vpn_logs.txt", "w", encoding="utf-8") as f:
        contenu = text_log.get('1.0', 'end').strip()
        f.write(contenu)
    messagebox.showinfo("Sauvegarde", "Les logs ont été sauvegardés dans vpn_logs.txt")


def rafraichir_image_mdp():
    """Recharge l'image du mot de passe et met à jour le label."""
    def worker():
        img = fetch_vpnbook_password_image()
        if img:
            fenetre.after(0, lambda: (label_mdp_img.config(image=img), setattr(label_mdp_img, 'image', img)))
    threading.Thread(target=worker, daemon=True).start()


# ------------------- Interface graphique -------------------
fenetre = tk.Tk()
fenetre.title("Connexion VPN")
fenetre.geometry('650x700')
fenetre.minsize(650, 700)

label_server = tk.Label(fenetre, text="Sélectionnez un serveur :")
label_server.pack(pady=(10, 5))

selected_server = tk.StringVar(fenetre)
server_combobox = ttk.Combobox(
    fenetre,
    textvariable=selected_server,
    values=list(SERVER_CHOICES.keys()),
    state='readonly',
    width=60,
)
server_combobox.current(0)
server_combobox.pack(pady=5, padx=10, fill='x', expand=True)

threading.Thread(target=update_server_latencies, daemon=True).start()
fenetre.after(100, process_latency_queue)

label_id = tk.Label(fenetre, text="Identifiant :")
label_id.pack(pady=5)
entry_id = tk.Entry(fenetre)
entry_id.insert(0, IDENTIFIANT)
entry_id.config(state='disabled')
entry_id.pack(pady=5, padx=10, fill='x')

label_mdp = tk.Label(fenetre, text="Mot de passe :")
label_mdp.pack(pady=(12, 5))

label_mdp_img = tk.Label(fenetre)
label_mdp_img.pack(pady=5)

entry_mdp = tk.Entry(fenetre, show='*')
entry_mdp.pack(pady=5, padx=10, fill='x')

ancien_mdp = charger_mot_de_passe()
if ancien_mdp:
    entry_mdp.insert(0, ancien_mdp)

frame_pwd_buttons = tk.Frame(fenetre)
frame_pwd_buttons.pack(pady=6)

bouton_show_mdp = tk.Button(frame_pwd_buttons, text="Afficher le mot de passe", command=toggle_mot_de_passe)
        
# Option pratique : rafraîchir l'image sans relancer l'app
bouton_show_mdp.grid(row=0, column=0, padx=4, pady=2)

tk.Button(frame_pwd_buttons, text="Rafraîchir l'image", command=rafraichir_image_mdp).grid(row=0, column=1, padx=4, pady=2)

mdp_image = fetch_vpnbook_password_image()
if mdp_image:
    label_mdp_img.config(image=mdp_image)
    label_mdp_img.image = mdp_image

bouton_connecter = tk.Button(fenetre, text="Se connecter", command=connecter)
bouton_connecter.pack(pady=10)

bouton_fastest = tk.Button(fenetre, text="VPN le plus rapide", command=connecter_plus_rapide)
bouton_fastest.pack(pady=10)

bouton_deconnecter = tk.Button(fenetre, text="Se déconnecter", command=deconnecter_action)
bouton_deconnecter.pack(pady=10)

progress = ttk.Progressbar(fenetre, orient="horizontal", mode="determinate", maximum=100, value=0)
progress.pack(pady=10, padx=10, fill='x')

label_latency = tk.Label(fenetre, text="Latence : N/A")
label_latency.pack(pady=10)

frame_logs = tk.Frame(fenetre)
frame_logs.pack(fill='both', expand=True, pady=10, padx=10)

label_logs = tk.Label(frame_logs, text="Logs :")
label_logs.pack(anchor='w')

text_log = tk.Text(frame_logs, state='disabled', wrap='word', height=10)
text_log.pack(fill='both', expand=True)

bouton_sauvegarde_logs = tk.Button(fenetre, text="Sauvegarder les logs", command=sauvegarder_logs)
bouton_sauvegarde_logs.pack(pady=5)

fenetre.mainloop()
