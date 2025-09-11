# -*- coding: utf-8 -*-
"""Fonctions réseau pour l'application VPNBook GUI."""

import time
import re
from io import BytesIO

import requests
from PIL import Image, ImageTk
from bs4 import BeautifulSoup
from tkinter import messagebox

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


def _ensure_dir(url: str) -> str:
    """Force le slash final pour que urljoin traite l'URL comme un répertoire."""
    return url if url.endswith("/") else url + "/"


def _get_base_href(soup: BeautifulSoup, fallback_url: str) -> str:
    """Retourne la base utilisée pour résoudre les URLs relatives."""
    base = soup.find("base", href=True)
    if base and base["href"].strip():
        return _ensure_dir(base["href"].strip())
    return _ensure_dir(fallback_url)


def _extract_password_paths_from_scripts(soup: BeautifulSoup):
    """Cherche dans les <script> une mention de 'password.php'."""
    paths = []
    for sc in soup.find_all("script"):
        txt = sc.string or getattr(sc, "text", "") or ""
        for m in re.finditer(r"""['"]([^'"]*password\.php)['"]""", txt, re.I):
            paths.append(m.group(1))
    seen = set(); out = []
    for p in paths:
        if p not in seen:
            out.append(p); seen.add(p)
    return out


def fetch_vpnbook_password_image():
    """Télécharge l'image du mot de passe VPNBook et retourne un PhotoImage."""
    from urllib.parse import urlencode, urljoin, urlsplit

    try:
        r = SESSION.get(PAGE_URL, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        node = soup.select_one("img.pwdimg") or soup.select_one("img[src*='password.php']")
        base_for_join = _get_base_href(soup, r.url)
        rel_paths = []
        if node and (node.get("src") or "").strip():
            rel_paths.append(node["src"].strip())
        rel_paths += _extract_password_paths_from_scripts(soup)
        if "password.php" not in " ".join(rel_paths):
            rel_paths.append("password.php")
        seen = set()
        rel_paths = [p for p in rel_paths if not (p in seen or seen.add(p))]
        bg = (node.get("data-bg") or "").strip() if node else ""
        if not bg.isdigit():
            bg = ""
        t_sec = str(int(time.time()))
        t_ms = str(int(time.time() * 1000))
        t_ym = time.strftime("%Y%m%d%H%M")
        qs_variants = []
        if bg:
            qs_variants += [
                {"t": t_sec, "bg": bg},
                {"t": t_ms, "bg": bg},
                {"t": t_ym, "bg": bg},
                {"bg": bg},
            ]
        qs_variants += [
            {"t": t_sec},
            {"t": t_ms},
            {"t": t_ym},
            {},
        ]
        uniq_qs = []
        seen_qs = set()
        for d in qs_variants:
            key = tuple(sorted(d.items()))
            if key not in seen_qs:
                uniq_qs.append(d); seen_qs.add(key)
        urls = []
        for rel in rel_paths:
            for qs in uniq_qs:
                query = ("?" + urlencode(qs)) if qs else ""
                urls.append(urljoin(base_for_join, rel) + query)
        origin = f"{urlsplit(r.url).scheme}://{urlsplit(r.url).netloc}/"
        for qs in uniq_qs:
            query = ("?" + urlencode(qs)) if qs else ""
            urls.append(urljoin(origin, "password.php") + query)
        seen = set()
        urls = [u for u in urls if not (u in seen or seen.add(u))]
        headers = SESSION.headers.copy()
        headers["Accept"] = "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"
        headers["Referer"] = PAGE_URL
        last_err = None
        for u in urls:
            try:
                resp = SESSION.get(u, headers=headers, timeout=TIMEOUT)
                resp.raise_for_status()
                data = resp.content
                img = Image.open(BytesIO(data))
                return ImageTk.PhotoImage(img)
            except Exception as ex:  # pragma: no cover - tentative jusqu'au succès
                last_err = ex
                continue
        raise RuntimeError(f"Aucune URL candidate valide. Dernière erreur: {last_err}")
    except Exception:
        messagebox.showerror("Erreur", "Impossible de récupérer l'image du mot de passe.")
        return None
