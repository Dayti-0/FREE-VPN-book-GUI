# -*- coding: utf-8 -*-
"""Fonctions liées aux opérations VPN et à la mesure de latence."""

import queue
import re
import subprocess

from constants import NOM_CONNEXION, IDENTIFIANT, SERVERS, SERVER_CHOICES

# Dictionnaire pour mémoriser les latences mesurées des serveurs
SERVER_LATENCIES = {}

# File pour communiquer les mises à jour de latence entre threads
latency_queue = queue.Queue()


def est_connecte():
    try:
        output = subprocess.check_output(
            'rasdial', shell=True, stderr=subprocess.STDOUT, universal_newlines=True
        )
        return NOM_CONNEXION in output
    except subprocess.CalledProcessError:
        return False


def deconnecter_vpn():
    try:
        subprocess.check_output(
            f'rasdial "{NOM_CONNEXION}" /disconnect',
            shell=True,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def creer_ou_mettre_a_jour_vpn(ip):
    check_cmd = f"powershell -Command \"Get-VpnConnection -Name '{NOM_CONNEXION}'\""
    try:
        subprocess.check_output(check_cmd, shell=True, stderr=subprocess.STDOUT)
        set_cmd = (
            f"powershell -Command \"Set-VpnConnection -Name '{NOM_CONNEXION}' "
            f"-ServerAddress '{ip}' -Force\""
        )
        subprocess.check_output(set_cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        add_cmd = (
            f"powershell -Command \"Add-VpnConnection -Name '{NOM_CONNEXION}' "
            f"-ServerAddress '{ip}' -TunnelType 'Pptp' "
            f"-AuthenticationMethod 'MSChapv2' -EncryptionLevel 'Optional' -Force\""
        )
        subprocess.check_output(add_cmd, shell=True, stderr=subprocess.STDOUT)


def connecter_vpn(mot_de_passe):
    commande_connect = f'rasdial "{NOM_CONNEXION}" {IDENTIFIANT} {mot_de_passe}'
    subprocess.check_output(
        commande_connect, shell=True, stderr=subprocess.STDOUT, universal_newlines=True
    )
    return True


def measure_latency(ip):
    """Mesure la latence vers une IP et renvoie la valeur en ms ou None."""
    try:
        output = subprocess.check_output(
            f'ping -n 1 {ip}',
            shell=True,
            universal_newlines=True,
            stderr=subprocess.STDOUT,
            timeout=5,
        )
        match = re.search(r'(?:temps=|time=)\s*<?\s*(\d+)\s*ms', output, re.IGNORECASE)
        if match:
            return int(match.group(1))
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    return None


def update_server_latencies():
    """Met à jour les latences de tous les serveurs et rafraîchit la liste."""
    new_values = []
    for label, (country, host) in SERVER_CHOICES.items():
        latency = measure_latency(host)
        SERVER_LATENCIES[(country, host)] = latency
        new_values.append(
            f"{country} – {host.split('.')[0]} ({latency if latency is not None else 'N/A'} ms)"
        )
    latency_queue.put(new_values)


def find_fastest_server():
    """Ping tous les serveurs et retourne celui avec la latence minimale."""
    best_country = None
    best_ip = None
    best_latency = None
    for country, hosts in SERVERS.items():
        for host in hosts:
            latency = measure_latency(host)
            if latency is None:
                continue
            if best_latency is None or latency < best_latency:
                best_country = country
                best_ip = host
                best_latency = latency
    return best_country, best_ip, best_latency
