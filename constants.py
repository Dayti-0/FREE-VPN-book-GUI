# -*- coding: utf-8 -*-
"""Constantes pour l'application VPNBook GUI."""

NOM_CONNEXION = "VPN_PPTP"
IDENTIFIANT = "vpnbook"
MDP_FILE = 'mdp.json'
PAGE_URL = "https://www.vpnbook.com/freevpn"  # conserver SANS slash final pour éviter 404 à l'ouverture

SERVERS = {
    'France': ['FR200.vpnbook.com', 'FR231.vpnbook.com'],
    'UK': ['UK205.vpnbook.com', 'UK175.vpnbook.com'],
    'Allemagne': ['DE20.vpnbook.com', 'DE21.vpnbook.com'],
    'Pologne': ['PL134.vpnbook.com', 'PL155.vpnbook.com'],
    'Canada': ['CA149.vpnbook.com', 'CA198.vpnbook.com'],
    'USA': ['US16.vpnbook.com', 'US21.vpnbook.com']
}

SERVER_CHOICES = {
    f"{country} – {host.split('.')[0]}": (country, host)
    for country, hosts in SERVERS.items()
    for host in hosts
}

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
""",
}
