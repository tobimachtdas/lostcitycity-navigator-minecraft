# Lost City Finder 0.8.3 – Windows Build

Dieses Paket enthält Quellcode und Build-Automatisierung, keine bereits kompilierten Windows-EXE-Dateien. Ziel: Windows 10/11 x64. Endnutzer benötigen keine Entwicklungswerkzeuge.

## Einfacher Weg: GitHub Actions
1. Den Inhalt des Ordners LostCityFinder (inklusive verstecktem Ordner `.github`) in ein eigenes GitHub-Repository hochladen. Keine Minecraft-Welten oder privaten Daten hochladen.
2. Actions → Windows EXE and installer → Run workflow. Falls nötig Actions für das Repository aktivieren.
3. Nach einem erfolgreichen Build das Artifact LostCityFinder-Windows-x64 öffnen und herunterladen. Darin befinden sich `LostCityFinder_Portable.exe` (klassische, stabile Tkinter-Oberfläche) und `LostCityFinder_Setup.exe` (modernes Tauri-Frontend, eingebetteter Offline-WebView2-Installer).

## Alternativ: Auf dem eigenen Windows-Build-PC
Nur der Entwickler benötigt Python 3.12 x64 mit py Launcher, Rust (MSVC x64), Visual Studio Build Tools mit Desktopentwicklung mit C++ und Windows SDK, Internet zum Download der Build-Abhängigkeiten. Tauri CLI installieren: `cargo install tauri-cli --version "^2" --locked`. Dann `build_windows.bat` starten. Für nur die klassische EXE: `build_windows.bat -PortableOnly` (kein Rust/C++-Setup nötig).

Ausgabe in `release/`. Die portable App benötigt keine Installation; Cache wird weiterhin im lokalen AppData-Verzeichnis gespeichert. Der Tauri-Installer enthält den Scanner als PyInstaller-Sidecar und installiert WebView2 bei Bedarf offline. Der Installer ist entsprechend größer. Die moderne App ist nicht als einzelne portable EXE vorgesehen.

Vor Veröffentlichung beide Varianten auf einem sauberen Windows-Rechner ohne Python/Rust testen: Start, Weltordner wählen, Erstscan, Cache-Scan, Kartenkacheln, Mindestabstände, Export, Bewertungen, YouTube-Link und Beenden. Unsigned builds können Windows SmartScreen-Warnungen anzeigen; keine Sicherheitsfunktionen deaktivieren. Optional später signieren.

Build-Konfiguration und Windows-Binärdateien wurden in dieser Linux-Umgebung nicht kompiliert oder ausgeführt. Minecraft-Plugin unverändert, weiterhin Maven-Quellprojekt.
