import requests
import re
import subprocess
import os
import distro
import argparse
import logging
import json

def parse_version(version_string):
    """Konvertiert einen Versions-String in ein Tupel von Integers."""
    return tuple(map(int, version_string.split('.')))

def setup_logging(debug_mode):
    """Konfiguriert das Logging."""
    level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger()

def check_root():
    """Prüft, ob das Skript mit Root-Rechten ausgeführt wird."""
    if os.geteuid() != 0:
        logging.error("Dieses Skript muss mit Root-Rechten ausgeführt werden.")
        exit(1)
    logging.debug("Root-Rechte bestätigt.")

def get_installed_version():
    """Prüft die installierte Emby-Version."""
    logging.debug("Prüfe installierte Emby-Version...")
    try:
        result = subprocess.run(['dpkg', '-l', 'emby-server'], capture_output=True, text=True)
        output = result.stdout
        match = re.search(r'emby-server\s+(\S+)', output)
        if match:
            version = match.group(1)
            logging.debug(f"Installierte Version gefunden: {version}")
            return version
        logging.warning("Keine installierte Emby-Version gefunden.")
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Fehler beim Abrufen der installierten Version: {e}")
        return None

def get_latest_beta_version():
    """Holt die neueste Emby-Beta-Version von GitHub."""
    logging.debug("Rufe neueste Emby-Beta-Version von GitHub ab...")
    url = "https://api.github.com/repos/MediaBrowser/Emby.Releases/releases"
    headers = {"Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        releases = json.loads(response.text)
        
        # Suche nach dem neuesten Beta-Release (prerelease == True)
        for release in releases:
            if release.get("prerelease", False):
                version = release.get("tag_name")
                logging.debug(f"Neueste Beta-Version gefunden: {version}")
                # Suche nach dem .deb-Asset für amd64
                for asset in release.get("assets", []):
                    if "emby-server-deb" in asset["name"] and "amd64.deb" in asset["name"]:
                        download_url = asset["browser_download_url"]
                        logging.debug(f"Download-URL für Beta-Version {version}: {download_url}")
                        return version, download_url
        logging.warning("Kein Beta-Release mit .deb-Datei gefunden.")
        return None, None
    except requests.RequestException as e:
        logging.error(f"Fehler beim Abrufen der neuesten Beta-Version: {e}")
        return None, None

def get_os_type():
    """Ermittelt, ob es Ubuntu oder Debian ist."""
    logging.debug("Prüfe Betriebssystem...")
    dist = distro.id().lower()
    if dist == 'ubuntu':
        logging.debug("Betriebssystem: Ubuntu")
        return 'ubuntu'
    elif dist == 'debian':
        logging.debug("Betriebssystem: Debian")
        return 'debian'
    else:
        logging.error(f"Nicht unterstütztes Betriebssystem: {dist}")
        return None

def download_and_install(url, debug_mode):
    """Lädt die .deb-Datei herunter und installiert sie (außer im Debug-Modus)."""
    logging.debug(f"Vorbereitung zum Herunterladen und Installieren von {url}")
    filename = url.split('/')[-1]
    logging.info(f"Geplante Datei: {filename}")
    
    if debug_mode:
        logging.debug("Debug-Modus aktiv: Überspringe Download und Installation.")
        logging.debug(f"Simuliere Download von {url}")
        logging.debug(f"Simuliere Installation von {filename} mit 'dpkg -i {filename}'")
        logging.debug(f"Simuliere Bereinigung: Entferne {filename}")
        return True
    
    try:
        # Download der Datei
        logging.info(f"Lade {filename} herunter...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.debug(f"Download abgeschlossen: {filename}")
        
        # Installation mit dpkg
        logging.info(f"Installiere {filename}...")
        subprocess.run(['dpkg', '-i', filename], check=True)
        logging.debug(f"Installation abgeschlossen: {filename}")
        
        # Aufräumen
        logging.debug(f"Entferne temporäre Datei: {filename}")
        os.remove(filename)
        logging.info("Update erfolgreich abgeschlossen.")
        return True
    except (requests.RequestException, subprocess.CalledProcessError) as e:
        logging.error(f"Fehler beim Herunterladen oder Installieren: {e}")
        return False

def main():
    # Argument-Parser für Debug- und Dry-Run-Modus
    parser = argparse.ArgumentParser(description="Emby Server Beta Updater")
    parser.add_argument('--debug', action='store_true', help="Debug-Modus: Simuliert den Ablauf ohne Downloads oder Installation")
    parser.add_argument('--dry-run', action='store_true', help="Dry-Run-Modus: Simuliert den Ablauf ohne Downloads oder Installation (identisch mit --debug)")
    args = parser.parse_args()
    
    # Debug-Modus aktivieren, wenn entweder --debug oder --dry-run angegeben ist
    debug_mode = args.debug or args.dry_run
    
    # Logging einrichten
    logger = setup_logging(debug_mode)
    logger.info("Emby Beta Updater gestartet...")
    
    # Root-Rechte prüfen
    check_root()
    
    # Prüfe Betriebssystem
    os_type = get_os_type()
    if os_type not in ['ubuntu', 'debian']:
        logger.error("Nur Ubuntu und Debian werden unterstützt.")
        exit(1)
    
    logger.info(f"Erkanntes Betriebssystem: {os_type.capitalize()}")
    
    # Prüfe installierte Version
    installed_version = get_installed_version()
    if not installed_version:
        logger.error("Emby-Server ist nicht installiert oder konnte nicht erkannt werden.")
        exit(1)
    
    logger.info(f"Installierte Version: {installed_version}")
    
    # Prüfe neueste Beta-Version
    latest_version, download_url = get_latest_beta_version()
    if not latest_version or not download_url:
        logger.error("Konnte die neueste Beta-Version nicht abrufen.")
        exit(1)
    
    logger.info(f"Neueste verfügbare Beta-Version: {latest_version}")
    
    # Vergleiche Versionen
    if parse_version(installed_version) >= parse_version(latest_version):
        logger.info("Die installierte Version ist aktuell. Kein Update erforderlich.")
        return
    
    logger.info("Eine neue Beta-Version ist verfügbar. Starte Update...")
    
    # Download und Installation
    if download_and_install(download_url, debug_mode):
        logger.info(f"Emby wurde erfolgreich auf Beta-Version {latest_version} aktualisiert.")
    else:
        logger.error("Update fehlgeschlagen.")

if __name__ == "__main__":
    main()
