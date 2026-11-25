# 🧭 Lost City Finder – Finde deine vergessenen Minecraft-Städte wieder!

**Du hast irgendwann eine Base, ein großes Lager oder sogar eine ganze Stadt in Minecraft gebaut – und findest sie einfach nicht mehr?**

Wer kennt es nicht? Man steckt Stunden in eine kleine oder riesige Base, baut Häuser, Lager und Straßen, fliegt später einmal quer durch die Welt und verliert irgendwann die Orientierung. Vielleicht hat man zwischendurch eine neue Base angefangen, weil die alte einfach nicht mehr auffindbar war. Und selbst wenn man sie nach langer Suche doch noch entdeckt, war es oft reine Glückssache.

Dann geht die Sucherei los: stundenlang über Wälder, Berge und Ozeane fliegen, die Welt kreuz und quer absuchen und nach irgendwelchen Anhaltspunkten Ausschau halten – vielleicht einem Turm, einem besonderen Gebäude oder einer Straße, die man früher selbst gebaut hat. Gerade auf riesigen, über Jahre gewachsenen Welten kann das ganz schön frustrierend werden.

**Genau dieses Problem hatte ich selbst immer wieder.** Ich kannte keine einfache Lösung, mit der ich meine alten Städte zuverlässig wiederfinden konnte. Also kam mir die Idee, selbst ein Tool dafür zu entwickeln: **Lost City Finder**.

Mit dem Lost City Finder kannst du deine gespeicherte Minecraft-Java-Welt durchsuchen und dir Orte anzeigen lassen, an denen sich mit hoher Wahrscheinlichkeit eine alte Base, ein Lager oder eine selbst gebaute Stadt befindet. Ich konnte damit tatsächlich meine lange gesuchten eigenen Städte wiederfinden! 🎉

> **Eine Idee von [tobimachtdas](https://www.youtube.com/@tobimachtdas) – entwickelt mit KI-Unterstützung.** Das Projekt läuft lokal: Deine Minecraft-Welt muss dafür nicht hochgeladen werden.

![Lost City Finder – Screenshot der Desktop-App](desktop-app/docs/screenshot.jpg)

## 🔎 Wie findet Lost City Finder deine alten Bauwerke?

Die Idee hinter der Suche ist ziemlich einfach: **An Orten, an denen Spieler viel gebaut und gelagert haben, gibt es oft auffällig viele Truhen und weitere Hinweise auf Bauaktivität.** Statt die gesamte Welt von Hand abzufliegen, analysiert das Tool die gespeicherten Weltdateien und sucht solche Stellen automatisch.

1. **Welt auswählen:** Du öffnest eine lokale Minecraft-Java-Welt oder eine Kopie deiner Serverwelt. Der Scanner liest die gespeicherten Regionsdateien.
2. **Truhengruppen erkennen:** Das Tool sucht nach vielen Truhen auf engem Raum. Doppelkisten werden als zwei Truhenblöcke berücksichtigt. Besonders große Lager können starke Hinweise auf eine Spielerbasis sein.
3. **Weitere Merkmale auswerten:** Baumaterialien, Aktivitätsdaten gespeicherter Chunks und Hinweise auf natürlich generierte Strukturen fließen in die Bewertung ein.
4. **Fundorte bewerten:** Jeder Kandidat erhält einen **Erkennungsscore**, damit du interessante Orte priorisieren kannst. Das ist eine Orientierungshilfe – **keine mathematisch garantierte Wahrscheinlichkeit** und kein sicherer Nachweis, wer dort gebaut hat.
5. **Nahe Treffer zusammenfassen:** Besonders wichtig ist die **Fernsuche mit einstellbarem Mindestabstand**. So werden nicht zehn Häuser derselben Stadt als zehn voneinander unabhängige Städte angezeigt. Für weit entfernte Siedlungen kannst du den Mindestabstand deutlich erhöhen.
6. **Auf der Karte überprüfen:** Eine zoombare Geländeansicht zeigt die gespeicherte Landschaft und mögliche Gebäude. So kannst du viel schneller einschätzen, ob du den gesuchten Ort wiedererkennst.
7. **Wieder hinfinden:** Du kannst die Fundorte als `locations.json` exportieren. Mit dem optionalen **Lost City Navigator** auf einem Paper-Server wählst du Ziele im Spiel aus und lässt dich per Kompass dorthin führen – mit entsprechender Berechtigung auch per Teleport.

### 🧰 Was kann das Projekt?

| Desktop-App: Lost City Finder | Server-Plugin: Lost City Navigator |
| --- | --- |
| Lokaler Welt-Scan ohne Cloud | Zielauswahl im Minecraft-Inventar |
| Truhenerkennung und Erkennungsscore | Navigationskompass und Entfernungsanzeige |
| Fernsuche mit großem Mindestabstand | Übersicht der Fundorte in der Sidebar |
| Geländeansicht, Heatmap und Fundortliste | Zielwechsel und optionaler Teleport |
| SQLite-Cache für spätere Scans | Rechte für Spieler und Administratoren |
| JSON-Export für den Server | Import der gefundenen Orte |

➡️ **[Desktop-App, Screenshots und Startanleitung](desktop-app/)**  
➡️ **[Paper-Plugin: Installation und Befehle](#bedienung)**

## ❤️ Weitere kostenlose Projekte von tobimachtdas

Wenn du Lust auf weitere Minecraft-Tools, kleine Apps, lokale KI-Projekte und Vibe-Coding-Experimente hast, würde ich mich riesig freuen, wenn du auf meinem YouTube-Kanal vorbeischaust. Vielleicht ist auch das nächste Projekt etwas für dich!

🎬 **[YouTube: Tobi macht das (@tobimachtdas)](https://www.youtube.com/@tobimachtdas)**

Auf meinem Kanal kannst du verfolgen, wie ich neue Software-Ideen umsetze. Ich möchte auch künftig immer wieder **kleinere Projekte kostenlos anbieten und hier auf GitHub veröffentlichen**. Wenn dir Lost City Finder hilft, freue ich mich sehr über ein Abo, einen Kommentar oder eine Empfehlung. Danke für deinen Support! ❤️

---

## 🧪 Neuer In-Game-Scanner (geplant für Version 1.0)

**Städte direkt im Minecraft-Spiel finden – ohne Desktop-Export.** Im Feature-Branch `feature/in-game-chunk-scanner` befindet sich ein erster Server-Scanner zum Testen auf **Paper 1.21.8**. Die Veröffentlichung ist **noch kein nachgewiesen funktionierender Release**.

### Direkt im Minecraft-Menü

Mit `/lostcity list` (oder Rechtsklick mit dem Navigator-Kompass) öffnest du das Menü. Als OP erscheinen zusätzlich **„Städte suchen“ (Fernrohr)** und **„Scan-Fortschritt“ (Uhr)**. Der Suchknopf startet den Scan mit dem Standardradius.

### Admin-Befehle

- `/lostcity scan start` – Scan um deine Spielerposition mit Standardradius (1.024 Blöcke) starten
- `/lostcity scan start 2048` – Suchradius in Blöcken selbst angeben
- `/lostcity scan status` – Fortschritt, geprüfte Chunkpositionen, Truhen und Fehler
- `/lostcity scan stop` – aktiven Scan abbrechen, ohne unfertige Ergebnisse zu speichern
- `/lostcity list` – gefundene Orte ansehen; Kompass und Teleport bleiben erhalten

Nur OPs bzw. Spieler mit **`lostcity.scan`** dürfen scannen. Gesucht wird in der aktuellen Welt, nur in bereits generierten Chunks. Es werden keine neuen Landschaften erzeugt.

### Suchlogik

Der Scanner liest Tile-Entities (`CHEST`/`TRAPPED_CHEST`) aus bereits gespeicherten Chunks, gruppiert Truhen nach Nähe, verwirft schwache Gruppen und filtert nahe Treffer anhand eines Mindestabstands. Der Erkennungsscore ist eine **grobe Heuristik** aus der Truhenanzahl und keine echte Wahrscheinlichkeit. Es handelt sich bewusst erst um einen **Truhen-Scanner**, nicht um die vollständige Bauwerkserkennung der Desktop-App. Fässer, Endertruhen und weitere Baumerkmale werden noch nicht ausgewertet.

Die Ergebnisse werden in `plugins/LostCityNavigator/scanned-locations.json` gespeichert und beim Neustart zusammen mit einer eventuell vorhandenen `locations.json` geladen. **Ein vollständig abgeschlossener neuer Scan ersetzt nur die bisherigen Scan-Ergebnisse**, nicht den Desktop-Export. Neue Treffer bleiben standardmäßig privat.

### Performance und Einschränkungen

- Maximal **4 Chunk-Abfragen pro Tick** und **2 gleichzeitige Chunk-Ladevorgänge** (konfigurierbar).
- Maximalradius standardmäßig 8.192 Blöcke. Starte mit **512–1.024 Blöcken** und beobachte die Server-TPS.
- Der Scan kann alte Chunks von der Festplatte nachladen und damit den Server belasten. Für erste Tests eine **Server-/Weltkopie** nutzen.
- Die Orientierung basiert auf Truhenstandorten. Bereits gefundene Städte ohne große Lager können übersehen werden, natürliche Strukturen können Fehlfunde verursachen.
- Die Ergebnisse werden als Koordinaten gespeichert, aber die aktuelle Zielwelt-Zuordnung setzt bei mehreren gleichartigen Welten eine passende Einstellung unter `worlds:` voraus.
- Die getestete Hauptversion **0.9.3** ist weiterhin die stabile Ausgangsbasis. Die neue Scanner-Variante muss zuerst per GitHub Actions kompiliert und auf dem Server getestet werden.

---

## 🧩 Lost City Navigator – Paper-Plugin 0.9.3

## Was ist neu?

- **Rechte Minecraft-Sidebar**: zeigt das ausgewählte Ziel, Distanz sowie bis zu fünf nahe Fundorte aus der aktuellen Dimension. Ein-/ausblenden mit `/lostcity map` oder über das Navigator-Menü. Technisch ist es ein Scoreboard, **noch keine grafische Geländekarte**. Die Sidebar übernimmt nur die Anzeige, solange keine andere Plugin-Sidebar gesetzt wurde.
- **Navigator-Menü**: Rechtsklick mit dem Spezialkompass oder `/lostcity list`. Bis zu 36 Ziele pro Seite, Navigation mit den Papier-Buttons in Slot 8 und 9.
- **Ziel wechseln**: Klick auf einen Fundort, Schaltflächen Vorheriges/Nächstes oder `/lostcity prev` und `/lostcity next`.
- **Teleport**: Ziel auswählen und im Menü auf die Enderperle klicken oder `/lostcity tp` ausführen. **Standardmäßig nur für OPs** (`lostcity.teleport`). Das Plugin sucht einen freien Oberflächenpunkt nahe den Fundkoordinaten; findet es keinen, wird der Teleport abgebrochen. Der Punkt ist nicht garantiert gefahrlos – unbedingt zunächst auf einer Testwelt ausprobieren.
- **Berechtigungen**: `lostcity.use` (alle), `lostcity.admin` (OP), `lostcity.teleport` (OP). Nicht freigegebene Fundorte bleiben privat.
- **config.yml**: Sidebar ein-/ausschaltbar; Teleport global deaktivierbar; optional Dimensionen konkreten Welt-Namen zuordnen.

## Bedienung

`/lostcity compass` – Navigator erhalten  
`/lostcity list` – Fundortauswahl öffnen  
`/lostcity map` – rechte Übersicht umschalten  
`/lostcity next` / `/lostcity prev` – anderes Ziel  
`/lostcity tp` – zum ausgewählten Ziel teleportieren (OP)  
`/lostcity reload` – `locations.json` neu laden (OP)

**Hinweis:** Die Liste in der rechten Sidebar dient nur zur Übersicht. Einträge einer Minecraft-Scoreboard-Sidebar sind nicht anklickbar. Fundorte wechselst du mit dem Navigator-Menü bzw. den Befehlen.

## 📥 Fertige Plugin-JAR herunterladen und installieren

**Du musst das Plugin nicht selbst kompilieren und auch keine GitHub Actions starten.** Die fertige JAR-Datei liegt direkt in diesem Repository:

👉 **[LostCityNavigator-0.9.3.jar herunterladen](LostCityNavigator-0.9.3.jar)** · [GitHub-Dateiansicht](https://github.com/tobimachtdas/lostcitycity-navigator-minecraft/blob/main/LostCityNavigator-0.9.3.jar)

### Installation auf deinem Minecraft-Server

1. Verwende einen **Paper-Server mit Minecraft Java 1.21.8**. Diese Kombination wurde bisher praktisch getestet; andere Versionen sind noch nicht verifiziert. **Vanilla** unterstützt dieses Plugin nicht.
2. Erstelle vorsichtshalber ein Backup deiner Serverwelt und **stoppe den Server**.
3. Lade die JAR herunter (auf der GitHub-Dateiseite gegebenenfalls **Download raw file** anklicken).
4. Kopiere `LostCityNavigator-0.9.3.jar` in den Ordner `plugins/` deines Paper-Servers.
5. Falls du ältere LostCityNavigator-JAR-Dateien hast, entferne sie aus `plugins/`, damit nicht mehrere Versionen gleichzeitig geladen werden.
6. Starte den Server neu. Prüfe in der Konsole, ob **LostCityNavigator** ohne Fehlermeldung aktiviert wurde.
7. Nutze im Spiel `/lostcity compass`, um den Navigator zu erhalten.

### Eigene Fundorte aus der Desktop-App importieren

1. Scanne deine Minecraft-Welt mit **[Lost City Finder](desktop-app/)**.
2. Exportiere deine gefundenen Orte als `locations.json`.
3. Kopiere die Datei nach `plugins/LostCityNavigator/locations.json` auf deinem Server (den Plugin-Ordner gegebenenfalls nach dem ersten Start erstellen lassen).
4. Gib als Administrator **`/lostcity reload`** ein.
5. Öffne mit dem Spezialkompass per Rechtsklick oder über `/lostcity list` die Fundortauswahl.

**Privatsphäre:** Importierte Ziele sind nicht automatisch für alle Spieler freigegeben. Teleportieren dürfen standardmäßig nur OPs beziehungsweise Spieler mit `lostcity.teleport`. Der Teleportpunkt ist nicht garantiert ungefährlich – teste dies zuerst auf einer Serverkopie.

### Für Entwickler (optional)

Wer den Quellcode verändern möchte, kann mit Java 21 und Maven `mvn clean package` ausführen oder den GitHub-Actions-Workflow **Build Lost City Navigator (Paper 1.21.8)** verwenden. Für die normale Installation ist das **nicht erforderlich**.


## Sicherheit

Das Plugin ist nur für deine eigene oder ausdrücklich freigegebene Serverwelt vorgesehen. Private Ziele werden normalen Spielern nicht angezeigt und Standardspieler dürfen sich nicht teleportieren. Vor dem ersten Test Serverbackup anfertigen. Wenn du andere Scoreboard-Plugins verwendest, blendet der Navigator seine Sidebar zurückhaltend aus, statt deren Anzeige zu überschreiben.


---

## Desktop-App und Quellcode

Die lokale Desktop-App inklusive Scanner, Karte, Fernsuche und Build-Anleitung findest du unter **[desktop-app/](desktop-app/)**. Der Plugin-Quellcode befindet sich im Repository-Hauptverzeichnis.
