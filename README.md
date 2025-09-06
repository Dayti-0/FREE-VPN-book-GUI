#Interface graphique pour le VPN gratuit VPNBook

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📌 Description
FREE VPN book Gui est une application **Python avec interface graphique (Tkinter)** permettant de se connecter facilement aux serveurs **VPNBook (PPTP)** sous Windows.  
Elle propose :
- La sélection d’un pays (France, UK, Allemagne, etc.)
- La connexion/déconnexion rapide au VPN
- L’affichage de la latence en temps réel
- La sauvegarde des logs dans un fichier texte
- L’option pour afficher/masquer le mot de passe
- La récupération automatique du mot de passe depuis le site VPNBook

⚠️ **Attention :**
- Ce projet utilise les identifiants **VPNBook** (gratuits et publics).
- Le mot de passe est enregistré en local dans un fichier `mdp.json`

## 📦 Dépendances

L'application nécessite quelques bibliothèques supplémentaires :

- `requests`
- `Pillow`
- `pytesseract`
- `beautifulsoup4`

Elles peuvent être installées via :

```bash
pip install requests pillow pytesseract beautifulsoup4
```
