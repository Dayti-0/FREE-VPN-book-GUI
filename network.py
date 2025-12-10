# -*- coding: utf-8 -*-
"""Fonctions réseau pour l'application VPNBook GUI."""

import requests
from bs4 import BeautifulSoup

from constants import PAGE_URL

try:
    import cloudscraper
    _HAS_CF = True
except Exception:  # pragma: no cover - dépendance optionnelle
    _HAS_CF = False


def make_session():
    """Crée une session HTTP adaptée à VPNBook."""
    if _HAS_CF:
        s = cloudscraper.create_scraper()
    else:
        s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr,fr-FR;q=0.9,en-US;q=0.8,en;q=0.7",
    })
    return s


SESSION = make_session()
TIMEOUT = 12


def fetch_vpnbook_password():
    """Récupère le mot de passe VPNBook depuis la page web (texte).

    Returns:
        str: Le mot de passe ou None en cas d'erreur.
    """
    try:
        r = SESSION.get(PAGE_URL, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Chercher le mot de passe dans <code class="font-mono...">
        code_elem = soup.select_one("code.font-mono")
        if code_elem:
            password = code_elem.get_text(strip=True)
            if password:
                return password

        # Fallback: chercher tout élément code contenant un mot de passe potentiel
        for code in soup.find_all("code"):
            text = code.get_text(strip=True)
            # Le mot de passe VPNBook est généralement alphanumérique, 6-10 caractères
            if text and 5 <= len(text) <= 15 and text.isalnum():
                return text

        return None
    except Exception as e:
        print(f"Erreur lors de la récupération du mot de passe: {e}")
        return None
