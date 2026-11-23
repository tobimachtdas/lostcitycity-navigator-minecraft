# Update 0.8.1 – Creator Edition

**Lost City Finder – eine Idee von tobimachtdas, entwickelt mit KI-Unterstützung.**

YouTube: https://www.youtube.com/@tobimachtdas

Die App zeigt den Urheber im Fenstertitel und Header und bietet einen direkten YouTube-Button. Plugin-Metadaten enthalten Autor und Website. Suchlogik, Cache und Kartenrenderer bleiben unverändert. Tauri und das erweiterte Plugin sind weiterhin geplante Schritte.

# Update 0.8 – Fernsuche

Mindestabstand rechts über der Fundortliste: 0 (alle), 256 bis 16384 Blöcke; Standard 2048. Filter wirkt sofort auf Karte, Liste und Export, ohne erneuten Scan. Pro Dimension bleiben bevorzugt bestätigte eigene Bauten, danach hohe Scores und Truhenzahlen stehen. Die übrigen Fundorte bleiben erhalten. Es handelt sich um einen Abstandsfilter, nicht um eine exakte Stadtgrenzenerkennung; Truhenzahlen werden nicht summiert. Plugin unverändert.

# 🧭 Lost City Finder — MVP 0.7.2

Neu in 0.7.2: Fundortliste rechts mit Zurück/Weiter, Weltübersicht nach Scan, funktionale Karten-Tabs, Raster-Übersicht und feste Geländekacheln mit RAM-Cache. Beim Ziehen wird das vorhandene Bild verschoben, erst danach neu gerendert.

Diese Version bringt vor allem ein stark überarbeitetes UX-Design für die Desktop-App mit modernerem Kartenfokus, dunklem Emerald-Theme, Statistik-Kacheln, eleganterem Filterbereich und neuer Detailkarte.


Ein lokales, kostenloses Suchwerkzeug für **Minecraft Java Edition** (insbesondere 1.21.8), mit optionalem Spigot-Navigationsplugin. Keine Mods, keine Cloud, kein Zugriff auf den laufenden Server.

## 1. Desktop-App starten (Windows)

1. **Python 3.10 oder neuer** installieren (Option **Add Python to PATH** aktivieren).
2. `desktop/start_windows.bat` doppelklicken oder im Ordner `desktop` `python app.py` aufrufen.
3. **Welt auswählen**: z. B. `%APPDATA%\.minecraft\saves\MeineWelt` oder eine **Kopie** deines Spigot-`world`-Ordners.
4. Radius (standardmäßig 32 Blöcke) und Minimum (4 Truhenblöcke) einstellen.
5. **Welt scannen**. Während des Scans erscheint jetzt ein deutlich sichtbares Overlay direkt auf der Karte mit „Bitte warten“, Fortschritt in Prozent, Anzahl verarbeiteter Regionsdateien und aktuellem Dateinamen. Danach kannst du die Ergebnisliste anklicken, Marker auf der Chunk-Übersicht ansehen und per Doppelklick Teleportkoordinaten kopieren.
6. **Fundorte exportieren** erzeugt `locations.json`.

**Karte:** In der Übersicht werden gespeicherte Chunks und gruppierte Fundortmarker angezeigt. Beim Heranzoomen bzw. Auswählen eines Fundorts wird eine lokale, vereinfachte Blockfarben-Draufsicht aus gespeicherten Chunks geladen. Zoom per Mausrad, Verschieben per Ziehen. Die Y-Koordinate ist in Smart-Suchprofilen ein Platzhalter (64), in der klassischen Suche die Höhe einer Truhe; **kein garantierter sicherer Teleportpunkt**. Bitte keine unkontrollierten Teleports verwenden.

Die Weltdateien werden **nur gelesen**. Server-Backups verwenden, damit die Kopie konsistent ist. Bei Servern mit separaten Welten (`world_nether`, `world_the_end`) sollten diese Ordner neben dem `world`-Ordner liegen.

### Erkennung

Der Scanner liest `.mca`-Regiondateien, zlib/gzip/uncompressed NBT und externe `.mcc`-Chunkdaten (wenn vorhanden), verarbeitet `block_entities` und ältere `Level.TileEntities`. Er gruppiert Chest-/Trapped-Chest-Blockpositionen im horizontalen Radius; **eine Doppelkiste zählt als zwei Truhenblöcke**. Zusätzliche Block-Entities (z. B. Öfen, Fässer, Schilder) fließen in eine einfache Bewertung ein. Verschiedene Y-Ebenen können sich überlagern. Ein Fundort ist nur ein *Verdacht*, kein Nachweis eines Spielerbaus.

Die Weltkarte zeigt lediglich bereits gespeicherte Chunks, keine ungeöffneten Gebiete. Für riesige Welten ist das MVP noch nicht umfassend optimiert.

### Neu in MVP 0.2

- Deutlich sichtbarer Ladezustand direkt auf der Karte
- Fortschrittsanzeige in Prozent
- Anzeige der aktuell verarbeiteten Regionsdatei
- Untere Fortschrittsleiste für besseres Feedback bei großen Welten

### Neu in MVP 0.3 – Smart Discovery

- Suchprofile: Städte, Basen, Lager, Aktivität, Alle und klassische Truhensuche.
- Mindestscore (Standard 65), regelbasierte Bewertung anhand künstlicher Materialien, Truhen ohne LootTable, Aufenthalt und Strukturreferenzen. Kein Nachweis der Urheberschaft.
- Das Stadtprofil sammelt Hinweise standardmäßig im Radius von 96 Blöcken (dreifacher Suchradius, mindestens 64). Nahe Kandidaten werden unterdrückt; bei anderen Profilen gilt der eingestellte Radius.
- Mindest-Truhenblöcke gilt nur bei der klassischen Truhensuche. Smart-Profile können auch ohne Truhen Fundorte erkennen.
- Heatmap (InhabitedTime): grün = niedrig, gelb = ab 12.000, orange = ab 120.000, rot = ab 720.000 Ticks. Aufenthaltsdauer ist keine direkte Bauaktivität.
- Fundort auswählen: Karte springt zum Ort und lädt die Umgebung im Hintergrund. Beim Zoomen werden lokale Ausschnitte nachgeladen; maximal 24 Ausschnitte im Arbeitsspeicher, kein persistenter Cache. Heatmap ausschalten und Geländevorschau aktivieren, um Blockfarben zu sehen.
- Gruppierte Marker in der Übersicht; Klick wählt den höchstbewerteten Fundort der Gruppe. Namen nur beim ausgewählten Einzelmarker.
- Die Geländevorschau zeigt oberste gespeicherte Blöcke, keine Innenräume; im Nether kann die Bedrock-Decke Bauwerke verdecken. Keine Seed-Neugenerierung. Sehr hohe Zoomstufen sind eingeschränkt.
- Smart-Suche benötigt mehr Zeit als der alte Scanner. Keine Restzeitprognose, kein gespeicherter Scan und keine Windows- oder echte Serverwelt-Validierung in diesem Release.

## 2. Spigot-Plugin installieren (1.21.8)

Dieses ZIP enthält das **Plugin-Quellprojekt**, **noch keine fertig kompilierte JAR**. Zum Bauen Java 21 und Apache Maven installieren und im Ordner `spigot-plugin` ausführen:

```bash
mvn clean package
```

Die kompilierte Datei `target/lostcity-navigator-0.4.0.jar` in `plugins/` kopieren, Server (nach Backup) neu starten.

`locations.json` aus der App nach `plugins/LostCityNavigator/locations.json` kopieren und `/lostcity reload` ausführen.

- `/lostcity compass` — Kompass erhalten (alternativ `/lostcity`).
- `/lostcity list` — Ziele auswählen.
- `/lostcity reload` — Fundorte erneut importieren (Admin).
- `lostcity.use` — Nutzung für Spieler, standardmäßig aktiviert.
- `lostcity.admin` — Alle Fundorte sehen und Import neu laden (standardmäßig OP).

**Datenschutz:** Neu importierte Orte sind **privat**. Admins sehen sie im Spiel; andere Spieler sehen nur explizit freigegebene Orte. Dafür bei gewünschten Einträgen in der JSON-Datei `"public": true` ergänzen und `/lostcity reload` ausführen. Freigabe darf nur der Admin vornehmen. Jeder Spieler erhält eine eigene aktive Zielauswahl. Das Plugin zeigt die Distanz oberhalb der Hotbar an; der Lodestone-Kompass funktioniert für Ziele in derselben Dimension.

### Sicherheit & Limitierungen

- Scannt und liest **offline**, stellt keine Netzwerkverbindung her.
- Die Plugin-Suche ist auf **54 Ziele pro Inventarseite** begrenzt (weitere Seiten folgen später).
- Die Plugin-JAR ist im Paket **nicht vorkompiliert** und wurde nicht gegen einen laufenden Spigot-Server getestet.
- Bei mehreren gleichartigen Welten einer Dimension wird im MVP die erste geladene Welt verwendet.
- Kompassnadel kann im Nether oder End spielmechanisch eingeschränkt sein; die Actionbar zeigt trotzdem Entfernung.
- Generierte Strukturen werden anhand gespeicherter Strukturreferenzen niedriger bewertet; dies ist keine sichere Identifikation. Die Geländevorschau unterstützt moderne Java-Blockpaletten, keine originalen Texturen.

## Dateien

- `desktop/scanner.py`: NBT-Parser, Region-Scan, Clustering, Export
- `desktop/app.py`: Windows-freundliche Tkinter-Desktop-Oberfläche
- `desktop/start_windows.bat`: Startdatei
- `spigot-plugin/`: Java-/Maven-Plugin-Quellprojekt
- `tests/`: synthetischer Test einer Minecraft-Regiondatei

## Neu in 0.4
- Modernisierte helle Desktop-Oberfläche mit Ergebnisübersicht, Detailbereich und farbigen Score-Markern.
- Truhen-Schwellen 10/20/40/60/100, optionaler Smart-Truhenfilter, LootTable-Abwertung und Strukturhinweise. Score ist keine statistische Wahrscheinlichkeit. Doppelkisten zählen weiterhin als zwei Blöcke; exakte Paarzählung fehlt.
- Plugin zeigt Score an und verwendet die Spigot-Actionbar-API statt der Paper-spezifischen Methode. Zielplattform Spigot/Paper 1.21.8; neuere Versionen sind nur angestrebt, nicht getestet. Maven und Serverlaufzeittest fehlen.
- Python-Scanner bleibt erhalten; native Migration und persistenter Cache sind noch nicht enthalten.

## Neu in 0.7 (Schritte 0.5 und 0.7)

- Fundort auswählen, Bewertung im Auswahlfeld unter der Karte setzen und speichern. Fehlalarme und generierte Strukturen können ausgeblendet werden. Bewertungen sind je Weltordner und Fundort-ID dauerhaft gespeichert; bei geänderten Suchradien kann sich die ID ändern. Kein automatisches ML-Training.
- Bis zu acht separate Python-Prozesse analysieren Regionsdateien parallel. SQLite speichert analysierte Merkmale pro Region im lokalen Benutzerprofil (`%LOCALAPPDATA%/LostCityFinder` unter Windows).
- Folgescans nutzen den Cache, sofern Dateigröße und Änderungszeit (auch externe MCC-Dateien) unverändert sind. Bei kopierten oder manipulierten Zeitstempeln Vollscan erzwingen. Bei Änderungen an der Welt immer mit einem konsistenten Backup arbeiten.
- Die Statusleiste zeigt Cache-Treffer, neu analysierte Regionen, Gesamtdauer und Fehler. Der erste Scan kann weiterhin dauern; reale Beschleunigung hängt von CPU, Datenträger und Weltgröße ab.
- Der Geländevorschau-Cache bleibt im RAM; Rust, dauerhaft gerenderte Kartenkacheln und Plugin-JAR sind noch nicht enthalten. Das bisherige Plugin bleibt kompatibel zum JSON-Export; ausgeblendete Fundorte werden nicht exportiert.
- Tests: `python tests/test_cache.py`, `python tests/test_scanner.py`, `python tests/test_smart.py`, `python tests/test_confidence.py`. Windows und echter Server noch nicht getestet.

## Hotfix 0.7.1

Scan-Button korrekt als Widget gespeichert. GUI-Regressionstest startet einen echten Scan einer synthetischen Welt und prüft die erneute Aktivierung des Buttons.

## Version 0.8.2 – neues Web-Frontend / Tauri-Vorschau

Die bewährte 0.8.1-Tkinter-App bleibt unter `desktop/start_windows.bat` unverändert verfügbar. Der neue Web-Client nutzt denselben Python-Scanner, dieselbe SQLite-Datenbank und exakt dieselbe Fernsuche. Das Plugin bleibt unverändert. Kein Rust-Scanner und kein React: Das Frontend verwendet HTML/CSS/JavaScript und Canvas, damit es ohne npm-Installation läuft.

**Sofort ausprobieren:** `start_web_windows.bat` doppelklicken (Python mit Tkinter erforderlich). Der lokale Dienst öffnet die Oberfläche im Standardbrowser. Das Konsolenfenster während der Nutzung offen lassen; mit Strg+C beenden. Der Dienst bindet nur an 127.0.0.1, mit zufälligem Port und Sitzungstoken. Kein Upload. Die Welt möglichst als Backup einlesen.

**Tauri-Entwicklerversion:** Rust (https://rustup.rs/), Visual Studio C++ Build Tools und Microsoft Edge WebView2 installieren, dann `start_tauri_windows.bat` starten. Beim ersten Cargo-Build werden Abhängigkeiten heruntergeladen. Der native Wrapper startet den lokalen Python-Dienst und öffnet dessen Oberfläche im WebView. Der Pfad zum Python-Interpreter kann über `LCF_PYTHON` festgelegt werden. Kein fertiger Installer; Build benötigt den Projektordner und Python. Tauri wurde in dieser Umgebung nicht kompiliert oder unter Windows getestet.

Neue Oberfläche: dauerhaft sichtbare Fundortliste, flexible Panels, Canvas-Karte, Maus-Zoom am Cursor, verschiebbare Karte, Gelände-Kacheln mit Speicher-Cache, Heatmap, Abstandsfilter ohne Neuscan, Bewertungen, JSON-Export und YouTube-Branding. Geländevorschau beginnt beim Hineinzoomen; die Übersicht zeigt gespeicherte Chunks. Y-Koordinaten können geschätzt sein. Browser- und Windows-UI-Praxistests stehen aus. Keine Garantie für höhere Scan-Geschwindigkeit, der Scanner ist unverändert.

## Windows-Release-Build (0.8.3)
Siehe [BUILD_ANLEITUNG.md](BUILD_ANLEITUNG.md).
