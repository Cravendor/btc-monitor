# BTC-monitor — NAS-metingen elk halfuur

## Verder werken / nieuwe agentsessie

Lees eerst [AGENTS.md](AGENTS.md), het [overdrachtsdossier](docs/HANDOVER.md),
[projectstatus](docs/PROJECT_STATUS.md) en [gemaakte keuzes](docs/DECISIONS.md).
Daar staan ook bestaande NAS-taken, herstelwerk, open PRs en wat nog niet actief
is. Controleer daarna de actuele code, data en runs: een oude chat of geplande
functie bewijst geen live implementatie. Oudere installatie- en methodepassages
hieronder hebben hun eigen scope en worden door de actuele overdracht geduid.

## Starten op GitHub

1. Maak een lege **Public** repository, bijvoorbeeld `btc-monitor`. De code en marktdata worden openbaar. Standaard GitHub-hosted runners zijn gratis voor openbare repositories; private repositories hebben planlimieten.
2. Pak het ZIP-bestand uit. Upload de inhoud van `btc-monitor` naar de hoofdmap van de repository. Let op: `.github/workflows/btc.yml` is een verborgen map/bestand; controleer dat het daadwerkelijk op GitHub staat. Je kunt via **Add file → Create new file** de volledige bestandsnaam `.github/workflows/btc.yml` invoeren en de inhoud plakken.
3. Zorg dat de bestanden op de standaardbranch staan. Open **Actions → BTC market snapshots → Run workflow** en voer een eerste run uit.
4. Controleer de samenvatting van de run en de nieuwe JSON onder `data/JJJJ/MM/DD/`. Een rode run kan bewust betekenen dat een bron een fout gaf: de foutstatus is dan wel opgeslagen.

De workflow heeft alleen `contents: write` nodig om de gegevens in deze repository te bewaren. GitHub geeft daarvoor automatisch een tijdelijk token. Geen beursaccount, API-key, handmatig token of trading permissions nodig. Deel geen sleutels in de chat. Branchbescherming of organisatiebeleid kan de opslag blokkeren; gebruik dan bij voorkeur een aparte datarepository waar deze workflow mag schrijven.

## Huidige collector en uitbreiding

De bestaande Bitget futuresprijs, OI en funding blijven intact. De collector voegt afgesloten Bitget 4H-candles, futuresorderboek (100 niveaus), Bitget spotprijs, Coinbase/Bitget-premiumproxy, perpetual mark/index-premium en USDT/USDC USD-prijzen toe. Elke bron heeft status, URL en observatietijd. Afgeleide metrics bewaren hun bronresultaten. `data/latest.json` behoudt de bestaande feedvorm en de nieuwste 14 snapshots. Fouten blijven null en worden wel opgeslagen; de workflow meldt onvolledige verzameling als fout.

Orderboekbanden 0,1%, 0,5% en 1% bevatten notional en imbalance; `*_band_covered=false` betekent slechts een ondergrens uit de teruggegeven niveaus. Stablecoinmetingen tonen uitsluitend prijs en depeg, geen totale supply of exchange flows. De Coinbase-premium is expliciet een Bitget-vergelijkingsproxy met USDT/USD-correctie; bronnen ouder dan drie minuten of meer dan twee minuten uiteen worden afgewezen. Futuresbasis betekent hier perpetual mark/index-premium, geen geannualiseerde termijnbasis.

`index.html` leest de openbare `main/data/latest.json` rechtstreeks, zodat snapshots zichtbaar worden zonder elke vier uur een Pages-build. De periodieke marktcollector draait primair op de NAS. GitHub behoudt een handmatige collector en krijgt via de watchdog een automatische reserve voor verouderde of ontbrekende opgeslagen metingen. Codewijzigingen starten de GitHub-tests, niet de collector. Activeer in de repository Settings → Pages → Source: GitHub Actions en start **BTC dashboard Pages** eenmaal handmatig. Publicatie en een succesvolle eerste Actions-run zijn nog vereist. De workflow gebruikt uitsluitend standaard publieke runners en slaat private repositories over; geen betaalde dienst of betaalde runner wordt gestart.

De bestaande NAS-traderecorder wordt alleen-lezen gekoppeld: zie [CVD-waarnemingen en dekkingsbeperkingen](docs/CVD.md). Spot- en futuresdelta’s uit opgeslagen trades zijn gedeeltelijke waarnemingen, geen gevalideerde volledige CVD.

## Planning en beperkingen

De NAS-taak **BTC NAS Collect Publish** is ingesteld op dagelijks iedere 30 minuten van 00:00 tot 23:30 **Europe/Amsterdam**. De GitHub-marktcollector heeft alleen `workflow_dispatch`; automatische cron-, push- en archiefvervolgtriggers zijn verwijderd. De afzonderlijke GitHub-4H-archivering (minuut 17/47 UTC) en watchdog (minuut 13/43 UTC) blijven actief. Alleen geplande of handmatig gestarte watchdog-controles mogen bij meer dan één uur oude of ontbrekende opgeslagen metingen een reservemeting uitvoeren. GitHub kan runs vertragen of overslaan. Openbare repositories kunnen na 60 dagen zonder repositoryactiviteit hun planning verliezen; controleer Actions als er geen nieuwe bestanden verschijnen. Een geheel niet gestarte run kan zelf geen foutbestand schrijven. Controleer dus ook gaten tussen tijdstempels. Er wordt niet achteraf aangevuld.

Een beurs kan GitHub-runner-IP's of regio's blokkeren (bijvoorbeeld HTTP 451/403). De eerste handmatige run moet bevestigen welke bronnen bereikbaar zijn. De workflow probeert zulke beperkingen niet te omzeilen. De verzameling draait pas nadat je de bestanden op GitHub hebt gezet.

### Geen 4H CVD uit vijf aggTrades

4H CVD vereist volledige trade-data over het gekozen vieruursinterval, met koop-/verkoopagressorrichting en consistente volume-eenheden. Vijf recente aggTrades zijn slechts een klein fragment en leveren geen geldige 4H CVD op. Daarvoor zijn volledige gepagineerde trade-data (of een aantoonbaar volledige trade-stream/archief) nodig, met controle op tijdgrenzen, gaten en dubbelen. Een cumulatieve reeks vereist daarnaast een gekozen beginpunt. Deze versie houdt `cvd_4h.value` expliciet op `null` en `coverage_verified=false`. Met een leesbaar NAS-journal staan gedeeltelijke delta’s apart onder `cvd_4h.markets`; zonder configuratie blijft de status `not_collected`. Geen geregistreerde gaten bewijst nog geen volledige dekking.

## Lokaal controleren

Python 3, geen externe pakketten: `python3 -m unittest discover -s tests`.
Een echte meting: `python3 scripts/collect.py` (schrijft naar `data/`).

## Bronnen

- [Binance spot marktdata](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market)
- [Binance futures marktdata](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)
- [GitHub Actions kosten](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [GitHub geplande workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

## Kostengrens

Budget: **€0 per maand**. Geen betaalde API's, cloudservers, proefabonnementen, grotere runners of upgrades activeren. De nieuwe workflows weigeren uitvoering in een private repository. CVD-waarnemingen komen uit de bestaande NAS; volledige intervaldekking is nog niet bewezen.

## Aanvullende bronnen

- https://www.bitget.com/docs/catalog/classic-contract-market/classic-contract-market
- https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-ticker

De API-responses zijn lokaal getest; bereikbaarheid vanaf GitHub-hosted runners moet nog met workflow_dispatch worden bevestigd.


## Historische dekking en mobiel dashboard (PR #32)

De signaaltijdlijn toont ook gedeeltelijke geschiedenis voor 24 uur, 7 dagen en
30 dagen, steeds eindigend bij de laatste opgeslagen meting (UTC). De watchdog
meet de laatste 24 uur tot zijn controletijd. Elk venster bestaat uit
rechtsgesloten tijdvakken van 30 minuten `(start, eind]`, vanaf het venstereinde
teruggerekend; dit zijn geen exacte GitHub-cronslots. Extra of dubbele runs
verhogen de dekking van een tijdvak niet. Dekking is archiefaanwezigheid,
geen geldigheid van signalen, onafhankelijke steekproefgrootte of candledekking.

- **Geschiedenis ontbreekt:** tijdvakken geheel vóór de eerste bewaarde meting.
  Of er vroeger een collector draaide is onbekend.
- **Geen opgeslagen meting na archiefstart:** leeg tijdvak na die grens,
  mogelijk een gemiste collectormeting. Zonder workflowlog bewijst dit geen
  mislukte of overgeslagen run; ook archiefverlies kan een oorzaak zijn.
- **Signaal ontbreekt:** een meting is bewaard, maar een timeframe heeft geen
  geldig label. Dit wordt afzonderlijk geteld en nooit neutraal gemaakt.

`python -m scripts.recover_signal_history` herstelt uitsluitend originele,
reeds opgeslagen labels uit gedateerde Bitget-bronsnapshots van vóór de live
archiefgrens. De eerste minuut bij die grens wordt overgeslagen om dubbele
live-metingen te vermijden. Herstel is idempotent, append-only en bewaart
bronpad en oorspronkelijke snapshot-eindtijd als herkomst. Bestaande rijen,
ontbrekende historische prijzen en modelversies worden niet aangevuld;
geen herberekende signalen worden als toenmalige waarneming gepresenteerd.
De herstelde rijen hebben daardoor geen beoordeelbare koersuitkomsten.
De dekkinggrens is de eerste bewaarde meting, niet de bewezen installatiedatum.

De twee timeframepagina's gebruiken horizontaal schuifbare tabellen en
passende tekstgroottes op kleine schermen. Validatie is uitklapbaar per
horizon. Grafieklijnen stoppen bij ontbrekende signalen of meer dan 45 minuten
tussen metingen. De bestaande steekproefdrempels en Wilson-beperkingen blijven
gelden. Oude watchdograpporten krijgen expliciet 'nieuw tijdvakrapport vereist'
tot de volgende watchdogrun schema 3 heeft geschreven. Kosten blijven €0.


## Beoordeelbaarheid van signalen (PR #33)

De validatie telt unieke directionele signalen met status `ok`, een geldige
candle-eindtijd en een bekende modelversie, ook als hun startkoers ontbreekt.
Ongeldige identiteit of ontbrekende sleutelmetadata levert geen identificeerbaar
signaal op. Dubbele waarnemingen verhogen de aantallen niet.

Elke combinatie van timeframe, horizon en oorspronkelijke signaalsterkte krijgt:

- **Beoordeeld:** geldige startkoers en een niet-tegenstrijdige vervolgkoers in
  het venster van horizon tot en met horizon + 30 minuten.
- **Startkoers ontbreekt:** de oorspronkelijke koers is ongeldig of ontbreekt;
  geen reconstructie en geen resultaat in het matchpercentage.
- **Horizon nog niet bereikt:** de laatste opgeslagen observatietijd ligt vóór
  het doelmoment.
- **Koersvenster nog open:** de horizon is bereikt, maar de tolerantie van
  30 minuten is nog niet voorbij en er is nog geen geschikte vervolgkoers.
- **Vervolgkoers ontbreekt:** het hele venster is voorbij volgens de laatste
  opgeslagen observatietijd, maar een bruikbare vervolgkoers ontbreekt.
- **Archieftijd onbekend:** zonder geldige observatietijd kan de fase niet
  worden bepaald. Een aanwezige geldige koersuitkomst blijft wel beoordeelbaar.
- **Horizon niet meetbaar met dit TF:** geen volgende candle-eindtijd van dit
  timeframe past binnen het doelvenster. Bijvoorbeeld 1 uur vooruit met alleen
  4-uurscandles; dit is geen collectorstoring en er wordt niet geïnterpoleerd.
- **Uitgesloten:** tegenstrijdige oorspronkelijke labels/koersen, of een vlakke
  uitkomst. Conflicten worden vóór selectie per signaalsterkte vastgesteld.

Voorrang: conflict, onmeetbare horizon, ontbrekende startkoers, vervolgens
koersuitkomst of wacht-/ontbreekstatus. Per groep geldt:
`unieke signalen = beoordeeld + vier vervolgkoersstatussen + startkoers ontbreekt
+ horizon niet meetbaar + uitgesloten`. Een labelconflict wordt bij elke
betrokken oorspronkelijke signaalsterkte uitgesloten; groepen mogen daarom
niet als onafhankelijke totaaltellingen worden opgeteld.

`pending_forward_price` blijft als compatibele subtelling van de vier
vervolgkoersstatussen bestaan. De pagina toont ze afzonderlijk. De archiefklok
bepaalt de status, niet de klok van de bezoeker of buildmachine: een stilgevallen
collector wekt zo geen schijn dat de toekomst al is waargenomen. Candle-eindtijden
na hun eigen opgeslagen observatietijd worden afgewezen. Alleen beoordeelde,
niet-vlakke uitkomsten tellen mee voor percentages en Wilson-intervallen;
de grenzen van 10/30 waarnemingen en alle statistische beperkingen blijven gelden.


## Watchdograpporten publiceren (PR #34)

Een afgeronde `BTC market snapshots`-run start nu ook een onafhankelijke
`BTC collector health check`, ongeacht of de collector is geslaagd, mislukt,
geannuleerd of gestopt door de tijdslimiet. De bestaande halfuurplanning blijft
als onafhankelijke terugval bestaan. Wijzigingen aan de watchdog/dekkingscode
op `main` starten ook een controle, zodat nieuwe rapportschema's niet op een
vertraagde cronrun hoeven te wachten.

De watchdog bewaart zijn rapport vóór de stap die een verouderde of ontbrekende
meting als fout markeert. Pages start nu ook na een watchdogrun en publiceert
bij een geslaagde, mislukte of door de tijdslimiet gestopte bronworkflow. Zo kan
een rood watchdogresultaat juist de juiste waarschuwing op het dashboard zetten.
Een bronfout kan nog steeds een ouder rapport opleveren; de bestaande zichtbare
ouderdomscontrole blijft daarom gelden. Een dashboardpublicatie is geen bewijs
dat marktdata actueel of geldig zijn.

Beide `workflow_run`-jobs controleren de standaardbranch en dezelfde
bronrepository, gebruiken uitsluitend de huidige standaardbranch bij checkout
en downloaden geen code of artifacts van de activerende run. Er komen geen
nieuwe rechten of betaalde diensten bij. GitHub-planningen en workflows blijven
best-effort; dit is geen continue bewaking.


## Validatie per modelversie (PR #35)

Het archief bevat meerdere heuristiekversies. De validatie op de signaaltijdlijn
splitst daarom eerst per opgeslagen modelversie, daarna per horizon, timeframe
en oorspronkelijke signaalsterkte. Matchpercentages en beschrijvende
Wilson-intervallen gebruiken uitsluitend de aantallen binnen die combinatie.
Twee versies met elk zes uitkomsten halen samen dus niet de drempel van tien;
twee versies met elk twintig halen niet samen de intervaldrempel van dertig.
De groepen zeggen zonder vergelijkbare perioden en afhankelijkheidscorrecties
niet welke versie beter voorspelt.

De versie op het signaal heeft voorrang; alleen als die ontbreekt wordt de
opgeslagen rijversie gebruikt. Onbekende of ongeldige versies worden nooit
stilzwijgend aan het huidige model toegewezen. De historische snapshottabel
vermeldt de modelversies en de grafiek onderbreekt lijnen bij versieovergangen.
De beschrijvende 24u/7d/30d-snapshottellingen kunnen versies combineren en zijn
uitdrukkelijk geen modelvalidatie.

Waargenomen vervolgkoersen zijn feitelijke marktdata en blijven bruikbaar over
versiegrenzen heen; de oorspronkelijke labels en versies veranderen niet.
Koersconflicten worden over alle versies gecontroleerd vóór selectie, zodat een
versiefilter tegenstrijdige marktdata niet kan verbergen. Verschillende labels
van verschillende modellen op dezelfde candle zijn afzonderlijke signalen.
De bestaande behandeling van conflicten binnen één model blijft behouden.

`evaluate_models` levert de gescheiden groepen aan de dashboardrenderer.
`evaluate`, `evaluate_horizons` en `evaluate_by_grade` behouden hun bestaande
geaggregeerde standaarduitvoer voor compatibiliteit; met `selected_model` kan
één model worden geselecteerd. De dashboardpercentages gebruiken uitsluitend
de gescheiden route. Geen bestaande signalen, koersen of modelversies worden
achteraf aangepast en er worden geen betaalde bronnen toegevoegd.


## Telling zonder overlappende evaluatieperioden (PR #36)

Elke modelversie toont twee afzonderlijke validatieweergaven: **Alle unieke
signalen** en **Zonder overlappende evaluatieperioden**. De standaard-API-uitvoer
blijft de volledige telling. Met `sample_policy="non_overlapping"` kiest de
validator per timeframe en modelversie het chronologisch eerste directionele
signaal. Dat reserveert het gesloten interval vanaf zijn candle-eindtijd tot
horizon + 30 minuten daarna. Het volgende signaal wordt alleen gekozen als
zijn candle-eindtijd strikt ná dat interval ligt. Selectie gebeurt voor elke
horizon opnieuw, vóór splitsing naar oorspronkelijke signaalsterkte.

De selectie gebruikt alleen kandidaatidentiteit en tijd, nooit de koersuitkomst,
prijsbeschikbaarheid, of het feit dat een signaal later beoordeelbaar blijkt.
Ook een kandidaat met ontbrekende startkoers of een label-/prijsconflict
reserveert de periode. Neutrale snapshots zijn geen directionele kandidaten.
Niet-gekozen signalen en hun waargenomen koersen worden niet uit het archief
verwijderd; die koersen mogen nog steeds een gekozen signaal helpen beoordelen.
Alle bestaande validiteits- en conflictcontroles blijven actief.

Elke groep toont unieke kandidaten, wegens overlap overgeslagen kandidaten en
geselecteerde signalen. Daarbij geldt `kandidaten = overgeslagen + geselecteerd`;
de bestaande uitkomststatussen tellen op tot de geselecteerde signalen.
De drempels van 10 beoordeelde uitkomsten voor percentages en 30 voor
beschrijvende Wilson-intervallen worden binnen elke afzonderlijke weergave,
versie, horizon, timeframe en signaalsterkte toegepast. De grotere volledige
steekproef kan de drempel voor de selectie niet vrijgeven.

Niet-overlap is geen onafhankelijkheidsgarantie en geen correctie voor alle
statistische onzekerheid: autocorrelatie, gedeelde regimes en selectiebias kunnen
blijven bestaan. Modellen, timeframes, horizons en groepen mogen ook niet als
onafhankelijke experimenten worden opgeteld. Oudere herstelde kandidaatrecords
kunnen de chronologische selectie opnieuw faseren; dit is een reproduceerbare
archiefselectie, geen vooraf vastgelegde prospectieve proef. Geen marktdata,
modellen, kosten of workflows worden gewijzigd.


## Validatietabellen filteren (PR #37)

Boven de historische validatie staan filters voor modelversie, timeframe,
horizon en telling (alle unieke signalen of zonder overlappende perioden).
Een gerichte selectie opent de relevante uitklapbare tabellen. De statusregel
telt geselecteerde tabelregels, geen beoordeelde of onafhankelijke signalen.
Filters wijzigen uitsluitend zichtbaarheid: steekproefselectie, koersuitkomsten,
percentages, conflicten en Wilson-intervallen worden niet herberekend.

De adresbalk bewaart de selectie in `v_model`, `v_tf`, `v_horizon` en `v_sample`,
zodat dezelfde weergave via de URL opnieuw kan worden geopend. Alleen waarden
uit de weergegeven keuzelijsten worden overgenomen; onbekende waarden worden
per filter genegeerd. `Alle filters wissen` zet alle keuzen terug op Alle en
verwijdert uitsluitend deze vier parameters; andere parameters en het fragment
blijven behouden. Filteren gebeurt lokaal in de browser; er is geen extra opslagdienst, account
of dependency voor het dashboard nodig.

Zonder JavaScript blijven alle tabellen en uitklappers beschikbaar; de
filterbediening wordt pas zichtbaar als deze is geïnitialiseerd. De langere
werkwijze en statistische beperkingen staan in een aparte uitklapper, met een
korte beschrijvende-validatiewaarschuwing direct naast de filters.

Validatie omvat een client-side rooktest met Node en een kleine DOM-adapter
op de daadwerkelijk gegenereerde HTML: gecombineerde selectie, gedeelde URL,
onbekende waarden, reset, intacte overige URL-onderdelen en ongewijzigde
gegevenscellen. Dit vervangt geen visuele browser-, touch- of toegankelijkheids-
controle; die blijft apart nodig. De bestaande GitHub-runner heeft Node; zonder
Node slaat de lokale Python-testsuite alleen deze client-side rooktest over.


## Marktverzameling op de NAS

De NAS publiceert marktmetingen en native signaalhistorie naar dezelfde GitHub-feed.
De uploads op 23 oktober om 14:00 en 14:30 Europe/Amsterdam hadden voor alle tien
meetonderdelen status ok en geslaagde Pages-publicaties. De NAS-CVD-export leest gedeeltelijke waarnemingen uit het bestaande journal. De
aparte 4H-contextarchivering is nog niet overgezet. Zie [NAS-installatie,
bevestigde uitvoering en herstel](docs/NAS.md). Eerdere implementatienotities
hierboven beschrijven de oorspronkelijke wijzigingen; de actuele marktcollector
start uitsluitend handmatig op GitHub, terwijl NAS, archivering, watchdog en
Pages hun afzonderlijke taken behouden. Budget blijft €0.



## Automatische GitHub-reserve bij uitval van de NAS

De bestaande `BTC collector health check` controleert op minuut 13/43 UTC de
aanwezigheid van opgeslagen metingen. Alleen `schedule` en een expliciete
`workflow_dispatch` mogen bij stale/missing data de marktcollector uitvoeren.
De grens blijft strikt meer dan 3600 seconden sinds de nieuwste geldige
archieftijd. Precies een uur oud is nog current. Dit is een aanwezigheidscheck,
geen bewijs van geldige marktmetrics of van een fysiek offline NAS.

Voor en na de reservemeting haalt de job de nieuwste repositoryreferentie op.
Een inmiddels hervatte NAS-upload heeft voorrang. Verse gegevens voorkomen een
reservemeting; na geslaagde fallback zijn ze eveneens weer current. De reserve
verzamelt dus niet standaard elk halfuur. Bij voortdurende uitval volgen nieuwe
pogingen zodra de opgeslagen meting weer ouder dan een uur is, op een volgende
uitgevoerde watchdog-controle. Planning op GitHub blijft best-effort.

Nieuwe snapshots vermelden `collection_source`: nas, github_fallback, github_manual
of local. Het hoofddashboard toont die bron; oude snapshots zonder metadata tonen
bron niet vastgelegd. Het watchdograpport bewaart alleen de uitkomst van zijn eigen
controle onder `recovery`; NAS-healthrapporten kunnen die tijdelijke metadata later
vervangen. Het snapshotarchief behoudt de bronvermelding.

De GitHub-reserve heeft geen toegang tot het NAS-journal: zijn `cvd_4h` blijft
not_collected/null. Hij vult geen verloren trades aan, neemt geen continue
WebSocketverbinding over en bevestigt geen historische CVD-dekking. De NAS blijft
de primaire collector. Geen AWS, nieuwe sleutels, inkomende NAS-poorten of betaalde
diensten nodig. Zie [werkwijze en gelijktijdige uploads](docs/NAS.md).

## Grafische swingmeters en niveauhistorie

De hoofdpagina toont BNB-marktrichting, scenario-gebonden SHB en Fear & Greed onder elkaar,
met inklapbare uitleg en een afzonderlijk datakwaliteitslabel. Swing gebruikt
dagzones, langere posities weekzones; 4H kan de reactie helpen bevestigen.
Per horizon staan vier vooraf beschreven routes, van sterk bearish tot sterk
bullish. De analyses worden onveranderd opgeslagen en na 7, 30 en 90 dagen
beoordeeld. SHB volgt standaard een automatisch voorstel; alternatieven zijn selecteerbaar.
De uiterste getoonde route blijft afhankelijk van iedere tussenliggende zone.
Geen positietracking, persoonlijke stops of automatische orderuitvoering.
Zie [methodiek, kwaliteitscontrole en beperkingen](docs/MARKET_GAUGES.md).
