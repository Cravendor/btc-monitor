# Swing- en langetermijnmeters

## Doel en grenzen

Het dashboard beoordeelt de markt rond prijsniveaus. Het geeft geen persoonlijke
koop-/verkoopopdracht, volgt geen modelposities en vraagt niet om echte trades.
De vroegere experimentele 4H-actieregel is vervangen door een **niveaucheck**.

Er zijn twee modi met steeds drie zichtbare wijzermeters:

- Swing: dagcandles bepalen momentum en de zone-ankers.
- Positie: weekcandles bepalen momentum en de zone-ankers.
- De drie meters zijn momentum, niveaucheck en een aparte Fear & Greed-dagindex.

Vier-uurscandles kunnen de reactie bij de dag-/weekzone helpen toetsen; zij
worden niet als dag-/weekhistorie hernoemd. Ontbreekt geldige 4H-invoer, dan wordt
de niveaucheck op de gesloten dag-/weekcandle gedaan en staat dat erbij.
Ontbrekende dagdata maken weekdata niet automatisch onbruikbaar, of omgekeerd.
Het datalabel is geen voorspelnauwkeurigheid. Er verschijnt geen wijzer bij
ontbrekende data; verlopen metingen worden ook in een open browser verborgen.
De horizonselectie wordt lokaal onthouden zonder persoonlijke handelsgegevens.

## Momentum en niveaucheck

Momentum hergebruikt `multi_tf_evidence_v0.2`: de prijs versus de 20 eerdere
candles en de verandering over 6 candles moeten dezelfde richting tonen
(buiten ±0,5%). Sterk vereist tevens meer dan ±2% afwijking van het gemiddelde
en relatief volume ≥1,2. Het zijn gecorreleerde prijsmetingen, geen onafhankelijke
bevestigingen. Model en grenzen zijn nog niet historisch gekalibreerd.

De niveaucheck toetst elke daadwerkelijk geraakte zone tegen het vorige en
laatste gesloten bevestigingsslot, met een buffer van 0,1 dag-/week-ATR:

- Eerder eronder, nu erboven: slot boven de zone.
- Eerder erboven, nu eronder: slot onder de zone.
- Eerder eronder, test maar slot eronder: afwijzing.
- Eerder erboven, test maar slot erboven: steun gehouden.
- Anders onbeslist; niet geraakte zones worden niet beoordeeld.

De wijzer toont de geteste zone het dichtst bij de actuele referentieprijs.
Alle overige zonechecks blijven in een uitklapbare tabel zichtbaar. Als de
actuele prijs aan de andere kant staat dan de slotreactie, wordt de wijzer
gemengd. Volgende hogere en lagere niveaus blijven **voorwaardelijke**
referenties. Bullish betekent niet dat de volgende Fib-zone zeker wordt bereikt.

Prijsreferentie: Bitget BTCUSDT USDT-futures, in USDT. Geen BTC/USD-spot,
uitgevoerde order of persoonlijk rendement.

## Vier vooraf beschreven routes

`scripts/swing_scenarios.py`, model `four_routes_daily_weekly_v1`, bouwt per
modus sterk bearish, bearish, bullish en sterk bullish. De 20 referentiecandles
sluiten de beoordeelde candle uit. Steun is hun laagste low, weerstand hun
hoogste high. ATR14 is het eenvoudige gemiddelde van 14 true ranges, geen
Wilder-ATR. De buffer is 0,1 ATR.

- Bearish: slot onder range-midden minus buffer en bearish momentum.
- Sterk bearish: slot onder steun minus buffer, bearish momentum en volume ≥1,2.
- Bullish: slot boven range-midden plus buffer en bullish momentum.
- Sterk bullish: slot boven weerstand plus buffer, bullish momentum en volume ≥1,2.

De grotere voorwaarde krijgt alleen voorkeur als die werkelijk voldoet.
Bij tegenstrijdigheid of geen richting: afwachten, geen geforceerde voorkeur.
Elke route heeft een oorspronkelijke trigger, slotgebaseerde ongeldigverklaring,
range-/ATR-vervolgniveaus en afzonderlijke Fibonacci-zones. Het zijn technische
routes: de pagina noemt ze niet psychologisch of volledig Elliott-bevestigd.

## Fibonacci, Elliott en psychologie

Fibonacci gebruikt de extremen van de vorige 20 native candles, op lineaire
schaal met zichtbare ankerprijzen en candle-openingen. Een onbekende volgorde
binnen één candle geeft geen gerichte Fib-berekening. Range-extremen zijn niet
automatisch de dominante Elliott-swing. 50% is halvering, geen Fibonacci-ratio.
Retracements en tweepunts-extensies hebben verschillende bases en functies.
ATR-projecties worden niet als Fibonacci-doelen weergegeven. Voor iedere zone
zijn afstanden vanaf de referentieprijs en mogelijke terugvalpercentages vanaf
de geteste zone gescheiden.

`scripts/elliott_rules.py` zoekt maximaal twee volgens een vaste methode
gekozen historische standaardimpulskandidaten uit strikte bevestigde pivots.
Pivot-high/low in dezelfde candle wordt overgeslagen wegens onbekende
intraperiodevolgorde. Regels: richtingen, golf 2 versus begin 1, golf 3 voorbij
1 en niet de kortste van 1/3/5, geen overlap van 4 met 1. Absolute prijslengtes
worden consequent gebruikt. Intermediate extrema worden ook gecontroleerd;
het begin van een pivotcandle wordt niet zonder bewijs ná zijn extremum gezet.
Geen automatische eis dat golf 5 voorbij 3 eindigt: mogelijke truncatie
vereist verdere structuur. Een geschonden standaardregel verwerpt de kandidaat;
geen diagonalen/futuresuitzondering verzinnen om haar te redden.

Zes pivots leveren GEEN bewezen interne 5-3-5-3-5. Die controle blijft **niet
toetsbaar** zonder geschikte subgolven. De huidige golf wordt niet automatisch
ingevuld. Deze kandidaatzoeker is geen volledige Elliott-patroonherkenner.

Wall Street-fasen blijven hypotheses, geen stip die uit de koersvorm alleen
wordt afgeleid. De pagina verwijst naar actuele oorspronkelijke daily-,
market-risk- en psychology-rapporten als die in het archief valideerbaar zijn.
`scripts/report_context.py` controleert de opgeslagen tekst/hash en datum; dat
is geen herverificatie van alle nieuwsclaims. Nieuws wordt niet zonder
controle tot een numerieke stem in de meter gemaakt. Ontbrekende context is
zichtbaar en verhoogt de score niet. Een volledige automatische koppeling van
gevalideerde huidige golftellingen en geverifieerde nieuwsgebeurtenissen is nog
geen onderdeel van deze eerste versie.

Primaire methodereferenties:
https://www.elliottwave.com/waveopedia/impulse/ en
https://www.elliottwave.com/waveopedia/fibonacci-relationships/ .

## Oorspronkelijke analyses en evaluatie

De collector bewaart `scenario_snapshot` in iedere NIEUWE gedateerde snapshot,
met beide horizons, vier routes, niveauchecks, kwaliteitschecks, formuleversie,
ankers en een inhouds-ID. Geen oude adviezen terugrekenen of eerdere bestanden
herschrijven. Het bestaande NAS-/GitHub-snapshotpad publiceert deze velden;
er is geen nieuwe verzamelaar, rekening of betaald abonnement nodig.

`python -m scripts.scenario_evaluation data _site` bouwt de niveau- en
scenariohistorie (`btc-action-history.html/json`, bestandsnaam behouden voor
koppelingen). Evaluatie na 7, 30 en 90 dagen. De eerste gepubliceerde set per
modus/model/broncandle is de steekproef; alle vier routes worden beoordeeld,
niet achteraf alleen het passende scenario. Die vensters kunnen overlappen;
de aantallen zijn dus niet automatisch onafhankelijk.

Latere gesloten candles toetsen de OORSPRONKELIJKE triggers en grenzen.
Geen targettreffer op dezelfde candle die de route activeert, geen reeds bij
registratie gepasseerd doel als nieuwe toekomstige treffer. Ontbrekende
opvolgcandles en conflicten geven geen succes. Nog niet verstreken horizons
blijven wachtend. Het resultaat meet gesloten-candle-scenario’s, niet intrabar
executies, echte trade-uitkomsten of gekalibreerde slagingskansen. Niveauchecks
zelf blijven met hun oorspronkelijke bronmoment in de snapshots beschikbaar.

## Quality & Improvement

Tijdens verwerking: bronidentiteit, actualiteit, native sluiting, gaten,
duplicaten, getalvaliditeit, ankers en inhouds-ID toetsen. Alle scenario’s en
hun beperkingen moeten zichtbaar blijven. Tijdens de geplande controles:

- Maand: datakwaliteit, bron-/opslagfouten, kleine verbeterpunten.
- Kwartaal: terugkerende foutpatronen en vooraf toetsbare modelhypotheses.
- Jaar: volledige keten, methodiek, versiebeheer en aantoonbare bruikbaarheid.

Geen automatische gewichtsaanpassing of oorspronkelijke labels herschrijven.
Een wijziging krijgt een nieuwe versie en wordt op toekomstige ongebruikte
data vergeleken; bij onvoldoende bewijs wordt dat expliciet gerapporteerd.
De kwaliteitscontrole beoordeelt analyses, geen persoonlijke handelsbeslissingen.
