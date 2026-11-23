# Lost City Navigator 0.9.2 – Paper 1.21.8

Der bisherige Kompilierungsvorgang mit nachgebildeten Bukkit-Klassen erzeugte falsche Java-Methodendeskriptoren (`NoSuchMethodError`). Dieses Projekt ist zum **Bauen gegen die echte Paper 1.21.8 API** konfiguriert. Der Server benutzt weiterhin seine eigene API zur Laufzeit.

## Fertige JAR erzeugen

1. Diesen Ordner als GitHub-Repository hochladen (inkl. `.github`).
2. Im Reiter **Actions** den Workflow **Build Lost City Navigator (Paper 1.21.8)** manuell starten.
3. Nach erfolgreichem Workflow das Artifact herunterladen und entpacken; `LostCityNavigator-0.9.2.jar` befindet sich darin.
4. Alternativ unter Windows Java 21 und Maven installieren und `build_windows.bat` starten.

## Installation

- Paper-Server vollständig stoppen und Backup erstellen.
- Alte `LostCityNavigator-*.jar` entfernen, nur **eine** Plugin-JAR verwenden.
- Die tatsächlich gegen Paper erstellte JAR in `plugins` kopieren.
- `plugins/LostCityNavigator/locations.json` aus dem Export des Lost City Finders übernehmen.
- Server starten, mit `plugins` und `lostcity compass` prüfen; `lostcity reload` importiert erneut.

Private Fundorte bleiben nur für `lostcity.admin` sichtbar. Für andere Spieler einen Eintrag in `locations.json` mit `"public": true` freigeben.

**Achtung:** Der Build und der vollständige Funktionstest auf einem laufenden Paper-Server müssen noch ausgeführt werden. Es ist keine offizielle Paper-Bibliothek im ZIP enthalten. Es darf nicht die alte Stub-JAR benutzt werden.
