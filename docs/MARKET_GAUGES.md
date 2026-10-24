# Swing- en langetermijnmeters

## Doel en grenzen

Het dashboard beoordeelt de markt rond prijsniveaus. SHB toont technische actievoorwaarden binnen een expliciet voorgesteld scenario.
Het dashboard volgt geen posities, kent geen persoonlijke stop-loss en voert
geen orders uit. Er zijn geen privé-tradegegevens nodig.

Er zijn twee modi met steeds drie zichtbare wijzermeters:

- Swing: dagcandles bepalen momentum en de zone-ankers.
- Positie: weekcandles bepalen momentum en de zone-ankers.
- De drie meters zijn BNB (Bear–Neutraal–Bull), scenario-gebonden SHB en een aparte Fear & Greed-dagindex.

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

De niveaucheck beoordeelt alle geraakte zones in de uitklapbare tabel. De
geteste zone het dichtst bij de actuele prijs kan ook een nieuwe BUY-voorwaarde
bij steun/reclaim of SELL-voorwaarde bij afwijzing/steunverlies ondersteunen,
als zij tussen de scenariotrigger en eerste doelzone ligt. Dit is een
reactievoorwaarde, geen uitgevoerde trade. Zonder bevestiging wordt geen
volgende zone als gegarandeerd beschouwd.

## SHB volgt een zichtbaar scenario

Er worden zonder eigen invoer vier voorstellen gedaan. Standaard volgt de
meter de technisch ondersteunde voorkeur; zonder voorkeur toont hij WAIT.
Via de selector of een knop op een routekaart kan een ander voorstel worden
bekeken. De gekozen categorie wordt lokaal onthouden, zonder trades of
persoonlijke gegevens. Het is steeds de actuele meting: nieuw berekende ankers
kunnen wijzigen en worden niet als vergrendeld persoonlijk tradeplan gevolgd.

De scenarioregel `scenario_shb_v1` in `scripts/scenario_actions.py` gebruikt de
zichtbare trigger, eerste doelzone, ongeldigverklaring, native slot/momentum en
waar beschikbaar een afgesloten 4H-reactie. De vaste regels zijn:

- BUY: nieuwe bullish slotbevestiging met passende bronvoorwaarden en actuele
  prijs boven de trigger, vóór de eerste doelzone; of bevestigd steun/reclaim
  bij een tussenliggende zone terwijl de bullish bronvoorwaarden blijven gelden.
- HOLD: geen nieuwe actievoorwaarde binnen een eerder ondersteunde route,
  bevestiging verzwakt zonder overschreden native grens, of eerst een reactie
  beoordelen bij een reeds bereikte doelzone. Dit bevestigt geen positie of stop.
- SELL: bearish voorwaarden bevestigd vóór de neerwaartse doelzone, afwijzing
  bij een tussenliggende/bovenliggende zone binnen een bullish route, of een
  native slot voorbij de grens na een voorgaand slot boven de huidige trigger.
- WAIT: scenario nog niet bevestigd, actuele prijs spreekt triggerbevestiging
  tegen, scenario past niet of geen voorkeur. Zonder geldige actuele prijs
  is er helemaal geen SHB-wijzer.

Een huidige slotvergelijking met huidige vaste ankers bewijst NIET dat destijds
al een BUY werd uitgegeven. Alleen werkelijk opgeslagen oorspronkelijke
SHB-toestanden worden gelogd. Er wordt geen instap, bezit, stopuitvoering,
herinstap of gerealiseerd resultaat afgeleid. Een ongeschonden dag-/weekslotgrens
is een andere toets dan een harde intrabar stop.

Een bereikte eerste doelzone veroorzaakt niet automatisch BUY richting het
verste doel. Binnen elke hoofdroute staan vier mogelijkheden: voortzetting,
terugtest na een eerdere bevestiging, pauze en tegenreactie. De verste getoonde
zone is geen verplichte bestemming of uiterste marktgrens. Een nieuwe meterstand
kan pas volgen nadat gegevens zijn binnengekomen; snelle omslagen kunnen eerder
plaatsvinden. De technische regels zijn voorlopig en niet historisch gekalibreerd.

Prijsreferentie: Bitget BTCUSDT USDT-futures, in USDT. Geen BTC/USD-spot,
uitgevoerde order of persoonlijk rendement.

## Vier vooraf beschreven routes

`scripts/swing_scenarios.py`, model `four_routes_daily_weekly_v2_shb`, bouwt per
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
met beide horizons, vier routes met subroutes, alle oorspronkelijke SHB-toestanden,
niveauchecks, kwaliteitschecks, formuleversie,
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
executies, echte trade-uitkomsten of gekalibreerde slagingskansen. Niveauchecks en alle scenario-gebonden SHB-toestanden blijven met hun oorspronkelijke
bronmoment in de snapshots en evaluatie-JSON beschikbaar. Oude v1-snapshots worden
niet achteraf van SHB voorzien. Bij nieuwe v2-snapshots toetst de validator naast
de inhouds-ID ook of de SHB-beoordeling bij de vastgelegde invoer en regel past.

## Quality & Improvement

### Visueel scenariopad

Bij de geselecteerde SHB-route staat een verticaal pad op prijsvolgorde, ook
voor bearish routes (dalend). Het toont bevestigingszone, tussenliggende
Fibonacci-zones, doelzones en een afzonderlijke marker voor de actuele koers
met bronmoment. De ongeldigverklaringsgrens staat apart, niet als routebestemming.
Dit is geen tijd-as met verwachte aankomstdatums. Afstanden op het scherm zijn
gelijke stappen, geen schaal voor tijd, kans of prijsafstand.

Het beginpunt is zichtbaar: de high voor bearish routes en de low voor bullish
routes, met de openingstijd van de ankercandle en de native tijdschaal. Dit zijn
de bestaande prior20-rangeankers, geen bewezen lifetime-ATH/ATL en ook niet
automatisch de meest recente lokale pivot. Ook de Fib-retracements tussen dat
beginpunt en de bevestigingszone worden getoond: daar kan prijsactie aandacht
vragen voordat de route wordt bevestigd. Historische ankers bewijzen geen
eerdere activatie of doorbraak. Ontbreekt een geldig anker, meld dit expliciet.

Het volgende aandachtspunt is de dichtstbijzijnde zone binnen de bestaande
modelbuffer, anders de eerstvolgende zone in de scenariorichting. Samenvallende
zones worden gecombineerd. Voorbij alle zones: opnieuw beoordelen, geen nieuwe
doelen extrapoleren. Bij ongeldigverklaring op native slotbasis vervalt het
volgende aandachtspunt; een actuele koers voorbij de grens vraagt al aandacht
voor slotbevestiging en het alternatief. De oorspronkelijke SHB-regels veranderen niet.

“Koers voorbij” vergelijkt alleen het huidige prijsniveau met een zone: geen
bewijs van een historische aanraking, succesvolle doorbraak of gevolgde trade.
Selectie zet geen oorspronkelijke route vast; nieuwe metingen kunnen ankers
en zones veranderen. Verlopen brondata verbergen het gehele pad, ook na
scenariowisseling. Controleer bij elke zone richting, SHB en gesloten-candlereactie.

### Geplande controles

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


## Two-route interpretation v1

The public swing/position interface now shows bull and bear routes together,
with five globally directional readings each: strong SELL, SELL, neutral,
BUY and strong BUY. BUY always means upward evidence, including in the bear
route. No personal position, HOLD state or fixed TP percentage is inferred.

Each route uses its own ladder: low + r*(high-low) for bull, high - r*(high-low)
for bear. r is 0, .236, .382, .5, .618, .786, 1, 1.272, 1.618, 2.618. These are
progress fractions from the origin (and conditional extensions beyond 1);
50% is not a Fibonacci ratio. An anchor range is not an Elliott wave count.
The origin remains the prior-20-candle high/low, explicitly not a validated
cycle ATH/low. Replacing that with a justified cycle anchor remains open.

At the nearest route zone, the latest closed confirmation candle and previous
close determine support hold, rejection, reclaim or breakdown, using the same
ATR buffer. No tested reaction means neutral. Contradictory current price
also suppresses a directional reading. A strong reading additionally requires
strong native momentum in the same direction. A possible retest requires the
preceding two closes to cross this same zone, followed by a touch. Candle
resolution cannot establish intrabar event order or future retention.

The ordered bull/bear pair gives one of 25 stable combination IDs. Opposing
signs mean disagreement, not a net directional recommendation. Both extremes
agreeing yield strong agreement; a lone directional reading is limited
confirmation. Shared price evidence is never counted as independent proof.
Not all 25 pairs are necessarily reachable with current geometry.

The complete two_route_assessment is frozen into the new v3 scenario payload,
covered by the existing content hash and recomputed during validation. The
outcome export retains it as original_two_route_assessment. The four earlier
internal definitions and their original SHB assessments are retained for
backward-compatible historical diagnostics; they are not four public routes.
Do not mix v3 combination samples with old route outcome counts: each original
horizon/set ID is one two-route observation, even though legacy outcome rows
repeat the same metadata. New combination-specific 7/30/90-day performance
statistics still need sufficient forward observations and dedicated analysis.

News remains separate context, not part of this version's numerical score.
There is no inferred psychological phase or completed Elliott count. The
existing freshness gate hides expired route readings and paths. Quality review
must examine validity and missingness, disagreements, zone role and retest
proof, duplicate correlated evidence, anchor changes and original versions.

Validation: 337 unit tests pass. Browser visual QA remains pending because the
local Playwright browser executable is unavailable.


## Available-history anchor candidates (v4)

Two-route readings now prefer the highest high in all available contiguous
native candles before the confirmation candle, followed by the lowest low on
a strictly later candle. Equal later highs restart the candidate decline; the
latest equal low is used. Same-candle high/low order is never inferred. Daily
and weekly sources remain separate, so their low candidates can differ.
The native confirmation candle is excluded to prevent it setting its own zone.
This can leave the last closed candle beyond an older anchor: report that
boundary crossing rather than treating an intrabar move as retained support.

History start/end, candle count, high/low dates and a source-boundary flag are
recorded. No lifetime ATH, final cycle bottom or independent Elliott confirmation
is claimed. If there is no later low or the candidate is unavailable, retain the
existing 20-candle range with an explicit fallback label/reason. Do not silently
claim a cycle anchor. No new API requests or paid services are introduced.

The v4 payload freezes the candidate and its time/high/low evidence. Validation
recomputes candidates and readings from that original evidence. Original v3
records continue using v1 two-route rules; historical records are not migrated
or reinterpreted. The full records remain the input to future quality review.

Validation: 343 unit tests pass, including high-then-low chronology, same-candle
ambiguity, no lookahead to the confirmation candle, later equal highs, gaps,
truncated coverage flags, evidence tampering and v3 compatibility. Browser
visual QA remains open. Wider source history and independently justified cycle
selection are still future work; this change does not close those limitations.
