# Lidl Discounts

Kleiner, inoffizieller Python-Client für aktuelle Angebote aus physischen Lidl-Filialen über die öffentlichen Lidl-Plus-Endpunkte.

Das Projekt kann als CLI genutzt werden oder direkt als kleiner API-Wrapper in Python-Code. Die Store- und Angebotsrouten benötigen aktuell keinen Account-Login.

## Was macht das Tool?

- Lidl-Filialen per Lidl-Plus-Autocomplete suchen
- bei leerem Autocomplete-Ergebnis im Filialkatalog suchen
- Filialinformationen anzeigen
- aktuelle Lidl-Plus-Angebote für eine Filiale laden
- Ausgabe als einfache CLI-Liste

Beispiel:

```bash
uv run main.py Hamburg
```

Beispielausgabe:

```text
Hamburg - Horn (DE5868)
Hamburg - Horn, Manshardtstraße 74, 22119 Hamburg-Wandsbek
53.55757, 10.10094
Distance: 249172 m
Offers: 50
  Product                                                    |      Offer |    Regular | Deal     | Unit               | Valid
  ---------------------------------------------------------- | ---------- | ---------- | -------- | ------------------ | -----------------------
  DR. OETKER - Dr. Oetker Die Ofenfrische/Pizza Tradizionale |     1.88 € |     3.69 € | -49%     | 1 kg = 4.32/4.5... | 2026-05-03 - 2026-05-09
  Fairtrade Bananen, lose                                    |  1.49 €/kg |  1.69 €/kg | -11%     | Kg-Preis           | 2026-05-03 - 2026-05-09
  Grüne Äpfel, lose                                          |  1.59 €/kg |  1.99 €/kg | -20%     | Kg-Preis           | 2026-05-03 - 2026-05-09
  Dattelcherrytomaten                                        |     1.79 € |     2.29 € | -21%     | 1 kg = 3.58        | 2026-05-03 - 2026-05-09
  Cherrystrauchtomaten, lose                                 |  7.45 €/kg |  9.84 €/kg | -24%     | Kg-Preis (375 g... | 2026-05-03 - 2026-05-09
  Brokkoli                                                   |     1.29 € |     1.79 € | -27%     | 1 kg = 2.58        | 2026-05-03 - 2026-05-09
  Dipladenia Pyramide                                        |     9.99 € |    11.99 € | -16%     | -                  | 2026-04-29 - 2026-05-05
  Weltmeisterbrötchen                                        |     0.78 € |          - | 2+1      | -                  | 2026-05-03 - 2026-05-09
  Ciabatta                                                   |     0.59 € |     0.79 € | -25%     | 1 kg = 1.97        | 2026-05-03 - 2026-05-09
  GRILLMEISTER - Grillmeister Chicken Wings                  |     4.79 € |     5.99 € | -20%     | 1 kg = 4.35        | 2026-05-03 - 2026-05-09
  METZGERFRISCH - Metzgerfrisch Frische Schweine-Minutens... |     2.49 € |     3.19 € | -21%     | 1 kg = 6.23        | 2026-05-03 - 2026-05-09
  BAUER - Bauer Der Große Joghurt                            |     0.59 € |     0.99 € | -40%     | 1 kg = 2.36        | 2026-05-03 - 2026-05-09
  DELUXE - Deluxe Pasta                                      |     1.95 € |     2.29 € | -14%     | 1 kg = 7.80        | 2026-05-03 - 2026-05-09
  WAGNER - Wagner Flammkuchen Elsässer Art/Steinofen Pizz... |     1.79 € |     3.49 € | -48%     | 1 kg = 5.97/5.11   | 2026-05-03 - 2026-05-09
  DULANO - Dulano Mini-Streichzwerge                         |     0.99 € |     1.49 € | -33%     | 1 kg = 7.62        | 2026-05-03 - 2026-05-09
  MILKA - Milka I Love Milka Pralinés                        |     1.29 € |     3.49 € | -63%     | 1 kg = 11.73       | 2026-05-04 - 2026-05-09
  MAGGI - Maggi Würze                                        |     1.99 € |     2.49 € | -20%     | 1 kg = 7.96        | 2026-05-03 - 2026-05-09
  SURIG - Surig Essigessenz                                  |     1.11 € |     1.49 € | -25%     | 1 kg = 2.78        | 2026-05-03 - 2026-05-09
```

Die konkreten Felder hängen vom Lidl-Plus-Antwortformat ab. Das Tool toleriert zusätzliche JSON-Felder und gibt unbekannte Angebotsdetails nicht künstlich vor.

## Installation

Voraussetzung:

- Python 3.12+
- `uv` oder normales `pip`

Mit `uv`:

```bash
uv sync
```

Oder mit `pip`:

```bash
pip install -e .
```

## Konfiguration

Alle Werte sind optional. Ohne `.env` nutzt das Tool Deutschland mit Berliner Koordinaten als Suchkontext.

Unterstützte `.env`-Variablen:

```text
LIDL_COUNTRY=DE
LIDL_LANGUAGE=de-DE
LIDL_LATITUDE=52.52
LIDL_LONGITUDE=13.405
LIDL_TIMEOUT=20
```

Die Defaults enthalten aktuell `DE`, `AT`, `ES`, `FR`, `NL` und `PL`.

## CLI-Nutzung

Eine Filiale suchen und Angebote anzeigen:

```bash
uv run main.py Berlin
```

Nur eine begrenzte Anzahl Angebote anzeigen:

```bash
uv run main.py Berlin --limit 20
```

Anderes Land setzen:

```bash
uv run main.py Wien --country AT --language de-AT
```

Suchkoordinaten überschreiben:

```bash
uv run main.py Farmsen --latitude 53.606 --longitude 10.119
```

## Python-Nutzung

```python
from main import LidlPlus

with LidlPlus(country="DE") as lidl:
    store, offers = lidl.offers_for_store_search("Berlin")

print(store.label)
print(offers.total_offers or len(offers.offers))
```

## Scope

Dieses Repo enthält bewusst nur den kleinen Teil, der für Filial- und Angebotsdaten benötigt wird.

Nicht enthalten sind z.B.:

- Login-Flows und Nutzer-/Profilverwaltung
- Coupons, Guthaben, Partnerbenefits oder Loyalty-Status
- Zahlungen
- Einkaufslisten oder App-Sync
- Scan- oder Self-Checkout-Flows

Das Projekt ist read-only gedacht.

## Hinweise

Das Projekt ist inoffiziell und kann jederzeit nicht mehr funktionieren, wenn Lidl die Lidl-Plus-Endpunkte oder deren Antwortformat ändert.
Bitte keine großen Mengen Requests automatisiert abfeuern. Das Tool ist für kleine lokale Abfragen gedacht.

## Inspiration

Inspiriert durch [`torbenpfohl/rewe-discounts`](https://github.com/torbenpfohl/rewe-discounts).

Ich wollte eine kleine Automation bauen, die mir einen Überblick über aktuelle Angebote aus verschiedenen Märkten in meiner Nähe gibt, ohne dafür mehrere unterschiedliche Apps öffnen zu müssen.

## Lizenz

Dieses Projekt ist unter der Apache-2.0 Lizenz lizenziert. Siehe [LICENSE](LICENSE) für Details.
