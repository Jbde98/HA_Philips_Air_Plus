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

## Verifiziert in Sweep 2 (Display-Einstellungen)

| D-Code | Bedeutung | Werte |
|---|---|---|
| `D03105` | Display-Helligkeit | 0 = aus, 115 = niedrig, 123 = hell |
| `D03104` | Temperaturfarbe anzeigen | 100 = an, 0 = aus |
| `D03133` | Temperatur im Standby anzeigen | 1 = an, 0 = aus |
| `D0312A` | Bevorzugter Anzeigeindikator (Einstellung) | 7 = Lüfterstufe im manuellen Modus (App-Übersicht: „Automatisch“), 5 = Temperatur immer |
| `D0312B` | aktuell angezeigter Indikator (read-only) | folgt `D0312A`, fällt aber in Auto/Schlaf/Brise auf 5 |

## Beobachtet, Bedeutung offen (Stand nach Sweep 1)

| D-Code | Beobachtung |
|---|---|
| `D03240` | 0, in beiden Sweeps unverändert (evtl. Aroma, in der App nicht schaltbar) |

## Offen (Stand Sweep 1, Display-Punkte inzwischen geklärt)

- Display niedrig / hell / aus: in Sweep 1 wurden Befehle gesendet
  (`StatusType` → `control`), aber kein sichtbarer D-Code änderte sich. Der Logger
  filterte damals `D03105` als Rauschen; der Wert stand bei `115`. Verdacht:
  `D03105` = Display-Helligkeit. Seit v0.4.0 wird `D03105` geloggt.
- Temperaturfarbe anzeigen, Temperatur im Standby anzeigen, Bevorzugter
  Anzeigeindikator, Aroma (falls vorhanden): noch nicht getestet.
- Timer 12 h (erwartet `D03110` = 13).
