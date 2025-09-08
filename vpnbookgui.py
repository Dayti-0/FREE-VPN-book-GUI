import tkinter as tk
from tkinter import messagebox
import subprocess
import json
import os
import threading
import tkinter.ttk as ttk
import time
import re
import requests
from io import BytesIO
from PIL import Image, ImageTk
from bs4 import BeautifulSoup

NOM_CONNEXION = "VPN_PPTP"
IDENTIFIANT = "vpnbook"
MDP_FILE = 'mdp.json'

SERVERS = {
    'France': 'FR200.vpnbook.com',
    'UK': 'UK205.vpnbook.com',
    'Allemagne': 'DE20.vpnbook.com',
    'Pologne': 'PL134.vpnbook.com',
    'Canada': 'CA149.vpnbook.com',
    'USA': 'US16.vpnbook.com'
}

# Logos ASCII par pays (extraits du bloc donné)
ASCII_LOGOS = {
    'France': r"""
###
  ## ##
   #      ######    ####    #####     ####     ####
 ####      ##  ##      ##   ##  ##   ##  ##   ##  ##
  ##       ##       #####   ##  ##   ##       ######
  ##       ##      ##  ##   ##  ##   ##  ##   ##
 ####     ####      #####   ##  ##    ####     #####
""",

    'UK': r"""
           ###
           ##
 ##  ##    ##  ##
 ##  ##    ## ##
 ##  ##    ####
 ##  ##    ## ##
  ######   ##  ##
""",

    'Allemagne': r"""
           ###      ###
            ##       ##
  ####      ##       ##      ####    ##  ##    ####     ### ##  #####     ####
     ##     ##       ##     ##  ##   #######      ##   ##  ##   ##  ##   ##  ##
  #####     ##       ##     ######   ## # ##   #####   ##  ##   ##  ##   ######
 ##  ##     ##       ##     ##       ##   ##  ##  ##    #####   ##  ##   ##
  #####    ####     ####     #####   ##   ##   #####       ##   ##  ##    #####
                                                       #####
""",

    'Pologne': r"""
                                                                           ###
                     ##
 ######    ####      ##      ####     ### ##  #####     ####
  ##  ##  ##  ##     ##     ##  ##   ##  ##   ##  ##   ##  ##
  ##  ##  ##  ##     ##     ##  ##   ##  ##   ##  ##   ######
  #####   ##  ##     ##     ##  ##    #####   ##  ##   ##
  ##       ####     ####     ####        ##   ##  ##    #####
 ####                                #####
""",

    'Canada': r"""
                                         ###
                                         ##
  ####     ####    #####     ####        ##    ####
 ##  ##       ##   ##  ##       ##    #####       ##
 ##        #####   ##  ##    #####   ##  ##    #####
 ##  ##   ##  ##   ##  ##   ##  ##   ##  ##   ##  ##
  ####     #####   ##  ##    #####    ######   #####
""",

    'USA': r"""
  
 ##  ##    #####
 ##  ##   ##
 ##  ##    #####
 ##  ##        ##
  ######  ######
"""
}

stop_ping_thread = False
ping_thread = None
show_password = False

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

def fetch_vpnbook_password_image():
    """Télécharge l'image du mot de passe VPNBook et retourne un objet PhotoImage."""
    try:
        page = requests.get('https://www.vpnbook.com/freevpn', timeout=10)
        page.raise_for_status()
        soup = BeautifulSoup(page.text, 'html.parser')
        img = soup.find('img', src=re.compile('password.png'))
        if not img or not img.get('src'):
            raise ValueError("Image du mot de passe introuvable")
        img_url = img['src']
        if not img_url.startswith('http'):
            img_url = requests.compat.urljoin('https://www.vpnbook.com/freevpn', img_url)
        img_resp = requests.get(img_url, timeout=10)
        img_resp.raise_for_status()
        image = Image.open(BytesIO(img_resp.content))
        return ImageTk.PhotoImage(image)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de récupérer l'image du mot de passe : {e}")
        return None

def est_connecte():
    try:
        output = subprocess.check_output('rasdial', shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        return NOM_CONNEXION in output
    except subprocess.CalledProcessError:
        return False

def deconnecter_vpn():
    try:
        subprocess.check_output(f'rasdial "{NOM_CONNEXION}" /disconnect', shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        return True
    except subprocess.CalledProcessError:
        return False

def creer_ou_mettre_a_jour_vpn(ip):
    check_cmd = f'powershell -Command "Get-VpnConnection -Name \'{NOM_CONNEXION}\'"'
    try:
        subprocess.check_output(check_cmd, shell=True, stderr=subprocess.STDOUT)
        # Mise à jour de l'adresse
        set_cmd = f'powershell -Command "Set-VpnConnection -Name \'{NOM_CONNEXION}\' -ServerAddress \'{ip}\' -Force"'
        subprocess.check_output(set_cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        # Création
        add_cmd = (
            f'powershell -Command "Add-VpnConnection -Name \'{NOM_CONNEXION}\' '
            f'-ServerAddress \'{ip}\' -TunnelType \'Pptp\' '
            f'-AuthenticationMethod \'MSChapv2\' -EncryptionLevel \'Optional\' -Force"'
        )
        subprocess.check_output(add_cmd, shell=True, stderr=subprocess.STDOUT)

def connecter_vpn(mot_de_passe):
    commande_connect = f'rasdial "{NOM_CONNEXION}" {IDENTIFIANT} {mot_de_passe}'
    subprocess.check_output(commande_connect, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
    return True

def connecter():
    ajouter_log("Tentative de connexion...")
    progress.config(mode='indeterminate')
    progress.start()
    bouton_connecter.config(state='disabled')
    threading.Thread(target=connecter_thread).start()

def connecter_thread():
    ip = SERVERS[selected_country.get()]
    mot_de_passe = entry_mdp.get()

    # Déconnecter si déjà connecté
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
        
        # Afficher le logo du pays sélectionné
        country = selected_country.get()
        if country in ASCII_LOGOS:
            ajouter_log(ASCII_LOGOS[country])

        # Lancer le thread de ping après connexion
        lancer_ping_thread(ip)

    except subprocess.CalledProcessError as e:
        fenetre.after(0, stop_progress)
        fenetre.after(0, lambda: messagebox.showerror("Erreur", f"Échec de la connexion : {e.output}"))
        ajouter_log(f"Échec de la connexion : {e.output}")

def stop_progress():
    progress.stop()
    progress.config(mode='determinate', value=0)
    bouton_connecter.config(state='normal')

def deconnecter_action():
    global stop_ping_thread
    stop_ping_thread = True  # On arrête le thread de ping
    ajouter_log("Tentative de déconnexion...")
    if deconnecter_vpn():
        messagebox.showinfo("Déconnexion", "Vous avez été déconnecté du VPN.")
        ajouter_log("Déconnexion réussie.")
        label_latency.config(text="Latence : N/A")
    else:
        messagebox.showerror("Erreur", "Échec de la déconnexion ou aucune connexion n'était active.")
        ajouter_log("Échec de la déconnexion ou aucune connexion active.")

def ping_serveur(ip):
    global stop_ping_thread
    stop_ping_thread = False
    while not stop_ping_thread:
        if est_connecte():
            try:
                output = subprocess.check_output(f'ping -n 1 {ip}', shell=True, universal_newlines=True)
                # On essaie d'extraire la latence avec une regex
                match = re.search(r'(?:temps=|time=)\s*<?\s*(\d+)\s*ms', output, re.IGNORECASE)
                if match:
                    latence_ms = match.group(1)
                    fenetre.after(0, lambda: label_latency.config(text=f"Latence : {latence_ms} ms"))
                else:
                    fenetre.after(0, lambda: label_latency.config(text="Latence : N/A"))
            except subprocess.CalledProcessError:
                fenetre.after(0, lambda: label_latency.config(text="Latence : N/A"))
        else:
            fenetre.after(0, lambda: label_latency.config(text="Latence : N/A"))
        time.sleep(2)

def lancer_ping_thread(ip):
    global ping_thread
    if ping_thread and ping_thread.is_alive():
        pass
    ping_thread = threading.Thread(target=ping_serveur, args=(ip,), daemon=True)
    ping_thread.start()

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

# ------------------- Interface graphique -------------------
fenetre = tk.Tk()
fenetre.title("Connexion VPN")
fenetre.geometry('500x600')
fenetre.minsize(500, 600)

label_server = tk.Label(fenetre, text="Sélectionnez un pays :")
label_server.pack(pady=5)

selected_country = tk.StringVar(fenetre)
selected_country.set('France')
option_menu = tk.OptionMenu(fenetre, selected_country, *SERVERS.keys())
option_menu.pack(pady=5)

label_id = tk.Label(fenetre, text="Identifiant :")
label_id.pack(pady=5)
entry_id = tk.Entry(fenetre)
entry_id.insert(0, IDENTIFIANT)
entry_id.config(state='disabled')
entry_id.pack(pady=5)

label_mdp = tk.Label(fenetre, text="Mot de passe :")
label_mdp.pack(pady=5)
label_mdp_img = tk.Label(fenetre)
label_mdp_img.pack(pady=5)
entry_mdp = tk.Entry(fenetre, show='*')
entry_mdp.pack(pady=5)
# Préremplit avec l'ancien mot de passe si présent
ancien_mdp = charger_mot_de_passe()
if ancien_mdp:
    entry_mdp.insert(0, ancien_mdp)
# Affiche l'image du mot de passe actuel
mdp_image = fetch_vpnbook_password_image()
if mdp_image:
    label_mdp_img.config(image=mdp_image)
    label_mdp_img.image = mdp_image

bouton_show_mdp = tk.Button(fenetre, text="Afficher le mot de passe", command=toggle_mot_de_passe)
bouton_show_mdp.pack(pady=5)

bouton_connecter = tk.Button(fenetre, text="Se connecter", command=connecter)
bouton_connecter.pack(pady=10)

bouton_deconnecter = tk.Button(fenetre, text="Se déconnecter", command=deconnecter_action)
bouton_deconnecter.pack(pady=10)

progress = ttk.Progressbar(fenetre, orient="horizontal", mode="determinate", maximum=100, value=0)
progress.pack(pady=10)

label_latency = tk.Label(fenetre, text="Latence : N/A")
label_latency.pack(pady=10)

# Zone de logs
frame_logs = tk.Frame(fenetre)
frame_logs.pack(fill='both', expand=True, pady=10)

label_logs = tk.Label(frame_logs, text="Logs :")
label_logs.pack()

text_log = tk.Text(frame_logs, state='disabled', wrap='word', height=10)
text_log.pack(fill='both', expand=True)

bouton_sauvegarde_logs = tk.Button(fenetre, text="Sauvegarder les logs", command=sauvegarder_logs)
bouton_sauvegarde_logs.pack(pady=5)

fenetre.mainloop()
