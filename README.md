# Göttinger Müllkalender (GEB) für Home Assistant

Eine [HACS](https://hacs.xyz)-Integration, die den Abfuhrkalender der
[Göttinger Entsorgungsbetriebe (GEB)](https://www.geb-goettingen.de/abfuhr/)
ausliest und für jede Abfallart (Restmüll, Biomüll, Papier, Gelber Sack, ...)
einen Sensor mit dem nächsten Abholtermin in Home Assistant anlegt.

## Funktionsweise

Die GEB-Webseite erzeugt nach Auswahl von Straße und Hausnummer einen
individuellen, abonnierbaren Kalender (ICS/vCalendar). Diese Integration lädt
genau diesen Kalender-Link in einem einstellbaren Intervall herunter,
erkennt die Abfallart anhand des Termintitels und legt pro erkannter
Abfallart einen Sensor mit Datum der nächsten Abholung an.

Es ist bewusst **keine** feste Adress-Abfrage (Straße/Hausnummer) gegen die
GEB-Webseite eingebaut: Der interne API-Aufruf der Webseite konnte aus dieser
Umgebung heraus nicht eingesehen werden (Netzwerkzugriff auf
geb-goettingen.de war blockiert), sodass geratene Parameter mit hoher
Wahrscheinlichkeit nicht funktioniert hätten. Der Kalender-Link ist dafür
robust gegen Änderungen an der Webseite und lässt sich in wenigen Schritten
selbst besorgen (siehe unten).

## Installation über HACS

1. HACS öffnen → **Integrationen** → Menü (⋮) oben rechts → **Benutzerdefinierte Repositories**.
2. Dieses Repository (`https://github.com/harmonisierend/claude`) als
   Repository-Typ **Integration** hinzufügen.
3. "Göttinger Müllkalender (GEB)" in HACS suchen und installieren.
4. Home Assistant neu starten.
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen** → nach
   "Göttinger Müllkalender" suchen.

## Deinen Kalender-Link besorgen

1. Seite [geb-goettingen.de/abfuhr](https://www.geb-goettingen.de/abfuhr/)
   öffnen und Straße + Hausnummer auswählen.
2. Nach der Option zum **Exportieren/Abonnieren** des Kalenders suchen
   (z. B. "Kalender exportieren", "Als ICS/vCalendar", "In Kalender-App
   abonnieren"). Den dortigen Link kopieren (beginnt meist mit `http(s)://`
   oder `webcal://`).
3. Bietet die Seite nur einen Datei-Download (`.ics`/`.vcs`) statt eines
   Links an: Datei herunterladen und irgendwo mit öffentlich erreichbarer
   URL bereitstellen, z. B. per Nextcloud-Freigabe, GitHub Gist ("Raw"-Link)
   oder einem eigenen Webserver. Diese URL dann verwenden.
4. Den Link im Konfigurationsdialog der Integration eintragen. Beim
   Einrichten wird der Kalender einmal testweise abgerufen und geparst –
   klappt das nicht, wird ein Fehler mit Grund angezeigt.

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
  zweite Adresse die Integration ein zweites Mal mit einem anderen
  Kalender-Link hinzufügen.
- Die Kategorisierung der Abfallart erfolgt per Schlüsselwortabgleich im
  Termintitel und deckt die bei GEB üblichen Bezeichnungen ab (Restmüll,
  Biomüll, Papier, Gelber Sack/Wertstoff, Sperrmüll, Grün-/Strauchschnitt,
  Schadstoffmobil, Weihnachtsbaum). Unbekannte Titel werden als eigener
  Sensor mit dem Originaltext als Name angelegt.

## Mitentwickeln

Wer den tatsächlichen internen API-Aufruf der GEB-Seite (z. B. per
Browser-Netzwerkanalyse für `preview.php`) kennt, kann gerne einen echten
Straße/Hausnummer-Konfigurationsschritt beisteuern, der den Kalender-Link
automatisch ermittelt.
