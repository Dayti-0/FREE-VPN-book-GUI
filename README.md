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

codex/implement-vpn-password-fetching-function-dr8n0s
Vous pouvez installer ces bibliothèques avec la commande suivante (veillez à
utiliser le même interpréteur Python que celui utilisé pour lancer
l'application) :

```bash
python -m pip install requests pillow pytesseract beautifulsoup4
```

> `pytesseract` est seulement une interface Python : le moteur
> [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) doit aussi être
> installé sur votre système.
> - **Windows** : téléchargez l'installateur depuis
>   [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) et assurez-vous
>   que `tesseract.exe` est accessible dans votre `PATH`.
> - **Linux** : `sudo apt install tesseract-ocr`.
=======
Elles peuvent être installées via :

```bash
pip install requests pillow pytesseract beautifulsoup4
```
 main
