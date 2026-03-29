# Fehlerbehebungen - GC-Setup

## Übersicht der behobenen Probleme

### 1. GNOME Extensions Installation
**Problem:** Ungenaue Fehlermeldung bei fehlender GNOME Shell
**Lösung:** 
- Verbesserte Fehlermeldung: "Could not detect GNOME Shell version. Is GNOME Shell running?"
- Klarere Netzwerkfehler: "Cannot reach extensions.gnome.org" statt generischer Fehlermeldung

**Datei:** `src/installer/extensions.py`

### 2. Firefox Deinstallation
**Problem:** Firefox konnte nicht entfernt werden, wenn es als Flatpak installiert war
**Lösung:** 
- Verbesserte `uninstall_native()` Funktion prüft jetzt, ob Flatpak-Version tatsächlich installiert ist
- Klarere Fehlermeldungen:
  - "No uninstall method available" wenn keine Methode definiert ist
  - "Failed to remove native" wenn native Entfernung fehlschlägt
  - "is not installed" wenn weder native noch Flatpak installiert sind

**Datei:** `src/installer/native.py`

### 3. Microsoft Fonts Installation

**Problem:** 
- **Fedora (dnf):** Direkter rpm-Install von URL kann fehlschlagen
- **Debian/Ubuntu (apt):** EULA-Akzeptierung wurde nicht automatisiert
- **Arch (pacman):** Befehl schlug fehl, wenn weder `yay` noch `paru` installiert waren

**Lösungen:**
- **Fedora:** RPM wird jetzt zuerst heruntergeladen, dann installiert, dann aufgeräumt
- **Debian/Ubuntu:** EULA wird automatisch via `debconf-set-selections` akzeptiert
- **Arch:** Prüft ob AUR-Helper installiert ist und gibt hilfreiche Fehlermeldung

**Datei:** `src/data/catalog.json`

### 4. Bessere Fehlerausgaben für System-Befehle

**Problem:** Bei Fehlschlag wurden nur stderr-Ausgaben gezeigt, manchmal aber relevante Infos in stdout
**Lösung:** 
- Kombiniert stderr und stdout für vollständige Fehlerinfo
- Zeigt Exit-Code wenn keine Ausgabe vorhanden
- Präzisere Timeout-Meldung (5 Minuten)

**Datei:** `src/installer/native.py`

## Testen der Korrekturen

### Extensions testen:
1. Stellen Sie sicher, dass GNOME Shell läuft
2. Versuchen Sie eine Extension zu installieren
3. Bei Fehler sollte nun eine klarere Meldung erscheinen

### Firefox Deinstallation testen:
1. Installieren Sie Firefox (nativ oder als Flatpak)
2. Versuchen Sie die Deinstallation über GC-Setup
3. Die App sollte nun korrekt erkennen, welche Version entfernt werden muss

### Microsoft Fonts testen (Fedora):
1. Wählen Sie "Microsoft Fonts" unter System Tweaks
2. Die Installation sollte nun zuverlässiger laufen
3. Bei Fehler erhalten Sie detaillierte Fehlerinformationen

## Weitere Empfehlungen

### Für Entwickler:
- Erwägen Sie, Logging hinzuzufügen für besseres Debugging
- Implementieren Sie Unit-Tests für die Installer-Module
- Fügen Sie Retry-Logik für Netzwerk-Operationen hinzu

### Für Benutzer:
- Bei Extensions-Fehlern: Prüfen Sie, ob Sie in GNOME Shell eingeloggt sind
- Bei Paket-Fehlern: Prüfen Sie Ihre Internetverbindung
- Bei System-Befehlen: Terminal-Output zeigt jetzt mehr Details
