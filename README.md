# Göttinger Müllkalender (GEB) für Home Assistant

Eine [HACS](https://hacs.xyz)-Integration, die den Abfuhrkalender der
[Göttinger Entsorgungsbetriebe (GEB)](https://www.geb-goettingen.de/abfuhr/)
ausliest und für jede Abfallart (Restmüll, Biomüll, Papier, Gelber Sack, ...)
einen Sensor mit dem nächsten Abholtermin in Home Assistant anlegt.

## Funktionsweise

Bei der Einrichtung gibst du nur **Straße und Hausnummer** an. Die
Integration baut daraus automatisch die URL zum persönlichen
iCalendar-Export der GEB:

```
https://abfuhr.geb-goettingen.de/<Jahr>/forward.php?str=<Straße>+&nr=<Hausnummer>&year=<Jahr>
```

Diese URL wird in einem einstellbaren Intervall abgerufen, die Termine
werden anhand des Titels (z.B. "[GEB] Abfuhr der Restmülltonne") einer
Abfallart zugeordnet, und pro Abfallart entsteht ein Sensor mit dem
nächsten Abholdatum. Ab November wird zusätzlich der Kalender des
Folgejahres abgerufen, damit die Sensoren über den Jahreswechsel hinweg
befüllt bleiben.

## Installation über HACS

1. HACS öffnen → **Integrationen** → Menü (⋮) oben rechts → **Benutzerdefinierte Repositories**.
2. Dieses Repository (`https://github.com/harmonisierend/claude`) als
   Repository-Typ **Integration** hinzufügen.
3. "Göttinger Müllkalender (GEB)" in HACS suchen und installieren.
4. Home Assistant neu starten.
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen** → nach
   "Göttinger Müllkalender" suchen.
6. Straße und Hausnummer genau wie auf der GEB-Webseite eingeben (z.B.
   "Lindenweg" und "15"; bei Straßen mit "Str." abgekürzt ggf. auch hier
   abkürzen). Beim Einrichten wird der Kalender einmal testweise
   abgerufen – klappt das nicht, wird ein Fehler mit Grund angezeigt.

> Tipp: Funktioniert die automatische Erkennung der Abfallart für eine
> Terminbezeichnung nicht (z. B. weil GEB den Text ändert), landet der
> Termin trotzdem als eigener Sensor, nur mit dem Rohtext als Namen. Die
> Zuordnung lässt sich in
> `custom_components/goettingen_muellkalender/const.py`
> (`CATEGORY_DEFINITIONS`) um weitere Schlüsselwörter erweitern.

## Erzeugte Entitäten

Pro erkannter Abfallart (z. B. `sensor.restmuell`, `sensor.biomuell`,
`sensor.gelber_sack_wertstoff`, ...) wird ein Sensor angelegt mit:

- **Zustand**: Datum der nächsten Abholung (`device_class: date`)
- **Attribut `days_remaining`**: Tage bis zur nächsten Abholung
- **Attribut `upcoming_dates`**: Liste der nächsten Termine (ISO-Datum)

Sensoren werden dynamisch angelegt – sobald der Kalender eine neue
Abfallart enthält, erscheint automatisch ein neuer Sensor.

## Optionen

Über **Einstellungen → Geräte & Dienste → Göttinger Müllkalender →
Konfigurieren** lässt sich das Abrufintervall (Standard: 12 Stunden)
anpassen.

## Bekannte Einschränkungen

- Es wird nur eine Adresse pro Integrationseintrag unterstützt. Für eine
  zweite Adresse die Integration ein zweites Mal mit einer anderen
  Straße/Hausnummer hinzufügen.
- Die Straßen-Schreibweise muss zur GEB-internen Straßenliste passen
  (z.B. "Fritz-Reuter-Str." statt "Fritz-Reuter-Straße"). Schlägt die
  Einrichtung fehl, auf der GEB-Seite unter „Abfuhrkalender" die
  Autovervollständigung prüfen und die dort vorgeschlagene Schreibweise
  übernehmen.
- Die Kategorisierung der Abfallart erfolgt per Schlüsselwortabgleich im
  Termintitel und deckt die bei GEB üblichen Bezeichnungen ab (Restmüll,
  Biomüll, Papier, Gelber Sack/Wertstoff, Sperrmüll, Grün-/Strauchschnitt,
  Schadstoffmobil, Weihnachtsbaum). Unbekannte Titel werden als eigener
  Sensor mit dem Originaltext als Name angelegt.
- Der URL-Aufbau (`abfuhr.geb-goettingen.de/<Jahr>/forward.php`) wurde
  anhand eines Live-Beispiels ermittelt (öffentliche API-Dokumentation
  gibt es bei GEB nicht) und kann sich bei einer Website-Umstellung
  ändern.
