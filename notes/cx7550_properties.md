# CX7550/01 — Property-Map (Sweep 1, 2026-11-26)

Gerät: Smart Tower Fan 7000 Series, type `Babel`, Firmware `0.2.9`.
Methode: Debug-Log des D-Code-Loggers (v0.3.3), jede Funktion einzeln in der
Philips-Air+-App geschaltet, ~30 s Pause pro Schritt.

## Verifiziert

| D-Code | Bedeutung | Werte |
|---|---|---|
| `D03102` | Power | 0 = aus, 1 = an |
| `D0310C` | Modus (Befehl) | 1–10, 81, 82 = manuelle Stufe; 0 = Auto; 17 = Schlaf; 130 = Natürliche Brise (Echo `-126`) |
| `D0310D` | aktuelle Stufe (Rückmeldung) | 1–10, 81 = Stufe 11, 82 = Stufe 12; bei Natürlicher Brise wechselt sie selbstständig (4 → 6 → 8 → 10) |
| `D0320F` | Oszillation | 80 = an (Winkel), 0 = aus |
| `D03110` | Timer | Stunden + 1 (2 = 1 h, 4 = 3 h), 0 = aus |
| `D03211` | Timer-Rest in Minuten (read-only) | 60, 180, zählt runter |
| `D03130` | Piepton | 100 = an, 0 = aus; Schlafmodus setzt ihn automatisch auf 0 |
| `D03224` | Temperatur um das Gerät | Zehntel °C (200 = 20,0 °C) |
| `StatusType` | `control` während eines App-Befehls, sonst `status` | — |

## Beobachtet, Bedeutung offen

| D-Code | Beobachtung |
|---|---|
| `D0312B` | 7 im manuellen Modus, 5 nach Wechsel auf Auto (bleibt 5 in Schlaf/Brise), 7 nach Rückkehr zu manuell |
| `D0312A` | 7, in Sweep 1 unverändert |
| `D03104` | 100, unverändert |
| `D03133` | 1, unverändert |
| `D03240` | 0, unverändert |

## Offen für Sweep 2

- Display niedrig / hell / aus: in Sweep 1 wurden Befehle gesendet
  (`StatusType` → `control`), aber kein sichtbarer D-Code änderte sich. Der Logger
  filterte damals `D03105` als Rauschen; der Wert stand bei `115`. Verdacht:
  `D03105` = Display-Helligkeit. Seit v0.4.0 wird `D03105` geloggt.
- Temperaturfarbe anzeigen, Temperatur im Standby anzeigen, Bevorzugter
  Anzeigeindikator, Aroma (falls vorhanden): noch nicht getestet.
- Timer 12 h (erwartet `D03110` = 13).
