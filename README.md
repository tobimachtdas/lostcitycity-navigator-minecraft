# Lost City Navigator 0.9.3 – Karte & Teleport (Paper 1.21.8)

**by tobimachtdas** — https://www.youtube.com/@tobimachtdas

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

## Paper-JAR über GitHub Actions bauen

1. ZIP entpacken.
2. Inhalt ins bestehende GitHub-Repository hochladen und die Dateien `pom.xml`, `src/main/java/de/lostcity/LostCityNavigator.java`, `src/main/resources/plugin.yml` und `.github/workflows/build-paper.yml` ersetzen; `src/main/resources/config.yml` hinzufügen. Der Inhalt muss **direkt im Repo-Stamm** liegen.
3. Nach dem Commit **Actions → Build Lost City Navigator (Paper 1.21.8)** öffnen.
4. Den erfolgreichen Lauf öffnen und unter **Artifacts** die JAR herunterladen.
5. Auf einer Testkopie des Paper-Servers alte Navigator-JAR entfernen, neue JAR installieren und Server neu starten.
6. Bereits vorhandene `plugins/LostCityNavigator/locations.json` und deine Fundortdaten beibehalten.

Die JAR wird gegen die **echte Paper 1.21.8 API** gebaut; keine nachgebauten Bukkit-Stubs. Der Build ist hier nicht ausgeführt worden, da die Paper-API / Maven in dieser Laufzeit nicht verfügbar sind. Ein echter Paper-Servertest steht ebenfalls noch aus.

## Sicherheit

Das Plugin ist nur für deine eigene oder ausdrücklich freigegebene Serverwelt vorgesehen. Private Ziele werden normalen Spielern nicht angezeigt und Standardspieler dürfen sich nicht teleportieren. Vor dem ersten Test Serverbackup anfertigen. Wenn du andere Scoreboard-Plugins verwendest, blendet der Navigator seine Sidebar zurückhaltend aus, statt deren Anzeige zu überschreiben.


---

## Desktop-App: Lost City Finder

Die lokale Desktop-App mit Welt-Scanner, Fernsuche, Geländekarte und Export liegt jetzt unter **[desktop-app/](desktop-app/)**. Eine echte Vorschau und die Start-/Build-Anleitung findest du dort.

![Lost City Finder Desktop-App](desktop-app/docs/screenshot.jpg)

Projektidee und Creator: **[tobimachtdas](https://www.youtube.com/@tobimachtdas)**.
