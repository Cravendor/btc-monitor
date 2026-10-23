# CVD-journal op de NAS — budget €0

## Wat nu wordt gekoppeld

De bestaande `/volume1/btc-cvd/bitget_cvd_collector.py` schrijft Bitget BTCUSDT
spot- en USDT-futures-trades naar `trades.sqlite3`. De door de gebruiker aangeleverde
collector en `cvd_store.py` zijn een voorbereidende recorder: `coverage_verified`
wordt altijd false en er is geen controleerbaar sessie-/backfillregister.

`scripts/cvd_export.py` leest deze database alleen-lezen en exporteert voor beide
markten de laatst afgesloten UTC-periode van vier uur: `[start, eind)`, bijvoorbeeld
08:00–12:00 UTC bij een meting om 14:22 UTC. De NAS-runner stelt het bestaande
databasepad in via `BTC_CVD_DB`; buiten die runner is de bron optioneel.
Geen netwerkverzoeken, API-sleutels, nieuwe pakketten of betaalde diensten.

## Betekenis van de velden

- `cvd_4h.status`: partial bij opgeslagen waarnemingen; missing_data bij ontbrekende
  of onleesbare bronnen; invalid_data bij ongeldige trades; not_collected zonder
  geconfigureerde bron. Status per markt is leidend.
- Zonder geslaagde historievalidatie blijven value:null en coverage_verified:false.
  Nul geregistreerde gaten verandert dit niet. Gecontroleerde Bitget-historie kan
  per markt een gevalideerde bron-delta leveren; zie stap 3 hieronder.
- `markets.spot` en `markets.usdt_futures`: afzonderlijke waarnemingen in BTC.
- `observed_buy_btc`, `observed_sell_btc`, `observed_delta_btc`: decimale strings,
  delta = opgeslagen buy-volume minus opgeslagen sell-volume binnen het interval.
  Dit is een intervaldelta, geen doorlopende cumulatieve CVD-reeks en geen
  ondergrens voor de werkelijke netto delta; ontbrekende buys en sells kunnen
  beide richtingen op vertekenen. Een ontbrekend interval blijft null.
- `trade_count`, `first_trade_at`, `last_trade_at`: alleen opgeslagen intervaltrades.
  De bestaande primaire sleutel `(market, trade_id)` voorkomt replay-dubbelen.
- `unresolved_overlapping_gaps`: aantal geregistreerde onopgeloste gaten waarvan
  de grenzen het interval raken; `open_overlapping_gaps` telt de gaten zonder
  eindtijd. Een oud OPEN-marker telt ook in latere intervallen. Dit is geen
  aantal bewezen nieuwe onderbrekingen en geen duur of dekkingspercentage.
- `latest_journal_trade_at`, `latest_journal_trade_age_seconds`,
  `journal_trade_status`: ouderdom van de nieuwste opgeslagen brontijd per markt,
  recent tot 300 seconden, daarna stale. Dit bewijst geen levend collectorproces
  of complete tradelevering. Toekomstige tijden >60 seconden worden afgewezen.

SQLite SUM zou floating point gebruiken; de exporter rekent met Decimal en
publiceert alleen aggregaten. Gedeeltelijke data geven geen bull/bear-score of
bevestiging van absorptie, distributie of whale-intentie. De native heuristiek en
het 4H-contextarchief blijven CVD als onbevestigd behandelen.

## Behoud en fouten

Eén read-transactie geeft beide markten een consistent databasebeeld terwijl
de bestaande WAL-collector doorgaat. Geen migratie, journalcopy, gapwijziging,
restart of ingestelde `resolved=1`. De oude OPEN-markers blijven auditgegevens.
Alleen bekende openbare snapshotbestanden worden gecommit; het journal, logs,
credentials, private paden en ruwe trades worden niet geëxporteerd.

Een ongeldige trade onderdrukt de hele delta van die markt. Een onleesbare of
incompatibele bron wordt missing_data. De overige marktmetingen blijven werken.
Het algemene snapshotlabel ok betreft de marktmetrics, niet de CVD-dekking.
`index.html` toont de twee waargenomen delta’s met een expliciet gedeeltelijk
label, gapmetadata en brontijd; oude feeds zonder deze velden tonen Ontbreekt.

## Sessieregistratie (stap 1, op de NAS geïnstalleerd)

`scripts/bitget_cvd_collector.py` en `scripts/cvd_store.py` bevatten een optionele
opvolger van de aangeleverde recorder. De halfuurlijkse snapshottaak installeert
deze bestanden niet. Op 23 oktober 2026 is de recorder handmatig geïnstalleerd
via een aparte versiemap en een atomisch vervangen startbestand op het bestaande
pad. De watchdog, opstarttaak, collector.lock en oorspronkelijke database blijven
in gebruik. Een online SQLite-backup is vooraf gecontroleerd. De gebruiker heeft
de 17 sessietests op Python 3.8.12 en echte ontvangst voor beide markten bevestigd.

De opvolger gebruikt dezelfde trades/gaps-tabellen en voegt `cvd_sessions` en
`cvd_owned_gaps` toe. Per verbindingspoging worden markt, BTCUSDT, start,
gevalideerde subscription acknowledgement, laatste opgeslagen frame-/tradetijd,
afsluiting, reden en aantallen opgeslagen. Een frame met zijn trades en checkpoint
wordt als één SQLite-transactie opgeslagen. Identieke replays worden gededupliceerd;
een afwijkende inhoud bij hetzelfde trade-ID breekt de sessie af en rolt het hele
frame terug. Spot en futures blijven gescheiden.

Na een crash krijgt een onafgesloten sessie bij herstart de status interrupted.
Het onbevestigde tijdvak begint uiterlijk bij het laatste duurzame checkpoint;
de crash wordt niet achteraf gedateerd alsof de collector tot de herstart werkte.
Een disconnect, verkeerd kanaal/symbool, ongeldig frame, klokregressie of ontbrekende
acknowledgement beëindigt de poging. Applicatie-pings blijven ook bij een drukke
tradefeed actief; een stille verbinding en een ontbrekende acknowledgement hebben
afzonderlijke deadlines. Een gestorven worker laat het hoofdproces falen zodat
de bestaande watchdog dit kan opmerken.

De nieuwe recorder begrenst uitsluitend zijn eigen OPEN-markers bij een volgende
gevalideerde acknowledgement. Alle blijven resolved=0: opnieuw verbonden betekent
geen herstelde trades. Oude legacy-markers worden nooit gewijzigd. Nieuwe gapgrenzen
zijn ontvangst-/transporttijden, geen bewezen exchange-tijdgrenzen. Een laat of
ongeldig bericht kan oudere trades betreffen; sessies zijn daarom geen complete
event-time-dekkingskaart of exchange-watermark.

De sessierecorder-health-export houdt coverage_verified=false en cvd_4h=null. Het extra veld
transport_session toont het laatst opgeslagen checkpoint, geen live-status of
volledigheidsgarantie. Een pong bewijst uitsluitend dat een frame is ontvangen.
Er is nog geen provider-sequentiecontrole, volledige backfill of 4H-validatie.

Deze stap gebruikt het aangeleverde V2-wireformaat. De echte NAS-test ontving voor
beide markten een acknowledgement en 50 trades in een tijdelijke database.
Na installatie namen de opgeslagen trades in een 30-secondencontrole toe met
60 voor spot en 189 voor futures. Dit bevestigt ontvangst, geen 4H-volledigheid.
Er worden geen nieuwe afhankelijkheden, sleutels, diensten of abonnementen toegevoegd.

## Historische herstelkandidaten (stap 2)

`scripts/cvd_backfill.py` haalt per handmatige opdracht één volledig afgesloten
UTC-interval van vier uur voor één markt op via publieke fills-history. Er zijn
geen API-sleutels nodig. De oorspronkelijke journal wordt met SQLite mode=ro
aangekoppeld. Historische trades gaan naar een APARTE lokale SQLite-database,
buiten de repository; nooit rechtstreeks naar de draaiende recorder. Dit voorkomt
conflicten tussen historische en live tijdstempels bij hetzelfde trade-ID.

De standaardlimieten zijn 400 pagina's en een zachte tijdsbegroting van 180 seconden,
met maximaal 1000 trades per pagina, maximaal 1 MiB per antwoord en 0,2 seconden
pauze tussen verzoeken. De begroting wordt vóór en na elk verzoek gecontroleerd;
dit is geen harde procesdeadline voor langzame socketreads of SQLite-werk.
Er zijn maximaal drie pogingen per idempotent verzoek bij timeouts,
verbindingsfouten en HTTP 500/502/503/504, met 1 en 2 seconden backoff binnen
dezelfde tijdsbegroting. Geen retry bij HTTP 429, toegangsblokkades, TLS-controlefouten
of ongeldige data. Foutredenen onderscheiden netwerk-timeout, HTTP-status,
TLS-validatie, SQLite, OS/opslag en antwoordverwerking, zonder fouttekst of
private URL's in het rapport op te nemen. Geen achtergrondtaken of installatie.
Een mislukte run bewaart reeds gevalideerde pagina's voor inspectie. Een nieuwe
run begint opnieuw; --resume vervolgt expliciet een bestaande incomplete run.

Trade-ID's moeten strikt aflopen en lager zijn dan de vorige cursor; ID's hoeven
niet opeenvolgend te zijn. Symbool, richting, positieve Decimal-prijs/hoeveelheid
en tijd binnen [start,eind) worden gecontroleerd. Ook na een korte pagina volgt
een verzoek om een expliciet lege eindpagina. Een herhaalde cursor, fout antwoord,
tijdslimiet of paginalimiet levert incomplete op, nooit complete CVD.

Pagina's blijven inclusief ruwe antwoorden, cursor en SHA-256 lokaal bewaard.
De som van BTC-volume én prijs maal BTC-volume moet exact overeenkomen met de
afgesloten handelscandle (geen index- of mark-price-candle). Er is bewust geen
tolerantie om verschillen groen te maken. Afronding door de provider kan daarom
ook een onterecht negatieve uitkomst geven; die vraagt onderzoek.

De koppeling wordt in beide richtingen met het live-journal vergeleken:
ontbrekende lokale IDs zijn herstelkandidaten; tegenstrijdige bestaande trades
of journal-IDs die ontbreken in de historie blokkeren provider_consistent.
Alleen voor spot is de gedocumenteerde secondeprecisie toegestaan als de
historische tijd exact op een seconde valt en de live tijd in dezelfde seconde
ligt. Zulke matches worden geteld; oorspronkelijke tijdstempels blijven intact.
Dit is een expliciete vergelijkingsregel, geen onafhankelijk bewezen timestampconversie.

provider_consistent betekent dat deze controles slagen, niet dat alle beursdata
onafhankelijk bewezen compleet zijn. De herstelrapporten zelf houden
coverage_verified:false en value:null. De afzonderlijke validator hieronder moet
de opgeslagen bewijsgegevens eerst opnieuw controleren voordat de exporter een
delta met gecontroleerde Bitget-brondekking kan gebruiken.
Ook legacy OPEN-gaten blijven ongewijzigd. Een candle-volumecontrole kan de
buy/sell-richting niet zelfstandig bewijzen. Er is nog een bewijs- en integratiestap
nodig voordat CVD door monitors als bevestigd mag worden gebruikt.

Na merge en actualiseren van de NAS-checkout, eerst handmatig testen op Python 3.8.12:

```sh
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR=/volume1/btc-monitor/tmp
cd /volume1/btc-monitor/repo
/volume1/btc-cvd/venv/bin/python -m unittest discover -s tests -p test_cvd_backfill.py -v
```

Daarna één markt per keer, met lokale kandidaten buiten de repository:

```sh
/volume1/btc-cvd/venv/bin/python -m scripts.cvd_backfill \
  --journal /volume1/btc-cvd/trades.sqlite3 \
  --store /volume1/btc-cvd/backfill/candidates.sqlite3 \
  --market spot
```

Gebruik daarna --market usdt_futures voor futures. --end-ms kan een expliciete
afgesloten UTC-4H-grens vastzetten zodat beide runs hetzelfde interval gebruiken.
Exit 0 is uitsluitend provider_consistent; incomplete geeft exit 1. Bewaar en
inspecteer het JSON-resultaat; publiceer de private kandidaatdatabase niet.

### Hervatten zonder opnieuw te downloaden

Een echte spotrun heeft 51.547 trades over het gesloten interval
1792756800000–1792771200000 opgehaald, met exacte BTC- en quote-volumeovereenkomst
en nul ontbrekende/extra/conflicterende journal-IDs. De daaropvolgende futuresrun
is na 249 pagina's / 249.000 trades afgebroken met de oude algemene foutmelding.
Die oude melding bewijst niet of netwerk, opslag of antwoordverwerking de oorzaak
was. De bewaarde data kunnen met de nieuwe hervatroute worden vervolgd:

```sh
/volume1/btc-cvd/venv/bin/python -m scripts.cvd_backfill \
  --journal /volume1/btc-cvd/trades.sqlite3 \
  --store /volume1/btc-cvd/backfill/candidates.sqlite3 \
  --market usdt_futures --resume 118b420de68341fd842e00ae273fad0a
```

Hervatten houdt run-ID, markt en interval vast. Een expliciete andere eindtijd,
verkeerde markt, onbekende run of al geslaagde run wordt geweigerd. Alle bewaarde
pagina's worden opnieuw gecontroleerd op opeenvolgende paginanummers, cursor-keten,
payload-hash, geldige trade-inhoud en exacte overeenstemming tussen payload en
kandidaatrijen. Voortgang wordt afgeleid uit duurzaam opgeslagen paginatransacties,
ook als het rapport door een crash nog oudere tellers bevat. Een al opgeslagen
lege eindpagina wordt niet opnieuw gedownload: dan volgen alleen de candle- en
journalcontroles. Losse kandidaatrijen of veranderde pagina's blokkeren hervatten.

De pagina- en tijdslimieten gelden per aanroep; bij --resume zijn maximaal
--max-pages extra pagina's toegestaan. request_attempts en transient_retries
tellen alleen de huidige aanroep; resume_count telt voortzettingen.
De CLI gebruikt een exclusieve, niet-blokkerende lock naast de kandidaatdatabase,
zodat twee herstelopdrachten die database niet tegelijk wijzigen. Dit is een
afzonderlijke lock en raakt de live collector.lock of publish.lock niet.
De SHA-controle is een lokale integriteitscontrole, geen cryptografisch bewijs
van authenticiteit van de provider. De herstelrapporten blijven false/null;
de hieronder beschreven validator verleent uitsluitend de expliciete bron-scope.

De hervatte futuresrun is op de NAS geslaagd met 262.345 trades / 264 pagina's,
exacte BTC- en quote-volumeovereenkomst en nul ontbrekende, extra of conflicterende
journal-trades. Kandidaatdelta's voor hetzelfde afgesloten interval:
spot -29.700067 BTC en futures -26.1303 BTC. Deze runs vormen de eerste echte
acceptatiegegevens; oude run-ID's worden niet vast in de exporter opgenomen.

## Gecontroleerde bron-delta en automatische export (stap 3)

`scripts/cvd_coverage.py` leest kandidaatdatabase en journal uitsluitend read-only,
binnen één SQLite-readtransactie. Voor precies het gevraagde afgesloten interval
worden de volledige pagina-/cursor-keten, hashes, ruwe payloads, opgeslagen trades,
lege eindpagina, aantallen en Decimal BTC-/quote-volumes opnieuw gecontroleerd.
De vergelijking met het journal loopt opnieuw in beide richtingen. Een opgeslagen
groen rapport is geen voldoende bewijs. Gewijzigde data, een andere markt of een
oud/toekomstig interval kunnen geen actuele gevalideerde delta opleveren.

Geslaagde resultaten per markt bevatten status:ok, coverage_verified:true,
coverage_scope:bitget_public_history_only en
coverage_method:bitget_history_exhaustion_and_exact_volume_v1. value en
validated_delta_btc bevatten dezelfde decimale BTC-intervaldelta, buy minus sell
volgens de richting die Bitget rapporteert. recovered_missing_trades telt de
historische trades die het live-journal mist; deze blijven in de aparte bron.
Oude OPEN-gaten worden nooit aangepast of stilzwijgend resolved.

De scope is essentieel: dit controleert de consistentie en uitputting van de
publieke Bitget-historie plus beide candlevolumes. Het is geen onafhankelijk bewijs
van ieder beursbericht, geen marktbrede meting en geen doorlopende cumulatieve CVD.
side_semantics is provider_reported_buy_sell en taker_side_verified blijft false:
de gebruikte V2-marktdata leveren geen onafhankelijke maker/taker-toewijzing.
De expliciete takerdefinitie van een ander protocol (zoals V3/SBE) wordt niet
stilzwijgend op V2 overgedragen. Dus geen bevestigde whale-intentie, absorptie of
bull/bear-score alleen op basis van deze delta. Een CVD-monitor moet deze grenzen
meenemen en uitsluitend exact vergelijkbare gesloten bron-intervallen gebruiken.

validated_at is het tijdstip van de lokale hercontrole, niet van een nieuwe
API-meting. history_response_at toont de provider requestTime van de opgeslagen
laatste historiepagina indien beschikbaar. evidence_sha256 identificeert het
lokaal gecontroleerde bewijs; ruwe pagina's/trades en bestandspaden blijven privé.

`scripts/cvd_export.py` behoudt zijn gedeeltelijke journalvelden en vult alleen
een geslaagde markt aan met deze bron-delta. Beide markten moeten slagen voor
top-level status:ok/coverage_verified:true. Spot en futures worden nooit opgeteld;
top-level value blijft null omdat er geen gezamenlijke delta is. Bij één geslaagde
markt is de algemene status partial; de status per markt blijft leidend. Een oud
gecontroleerd interval wordt nooit als waarde voor een nieuw interval gebruikt.

`nas/collect_publish.sh --run` stelt BTC_CVD_BACKFILL_STORE standaard in op
/volume1/btc-cvd/backfill/candidates.sqlite3 en start scripts.cvd_pipeline vóór
de normale marktmeting. De pipeline controleert bestaande voltooide bewijsgegevens
zonder nieuwe API-verzoeken. Voor een nieuw interval wordt per markt begrensd
opgehaald of een onderbroken netwerk-/budgetrun hervat: 180 seconden zachte begroting
en 400 extra pagina's per markt, normale retryregels. In de eerste minuut na een
UTC-4H-grens wordt nog gewacht op afwikkeling door de provider: de upload publiceert
dan beschikbare waarnemingen, niet het oude interval als nieuw. De volgende
halfuurlijkse run probeert het actuele interval opnieuw. Als een proces over een
nieuwe 4H-grens heen loopt, gebruikt de exporter altijd zijn actuele doelinterval;
resultaten voor het vorige interval worden niet hernoemd of overgenomen.

De kandidaatdatabase heeft een eigen exclusieve schrijverslock. De marktverzameling
blijft onder publish.lock; de continue recorder gebruikt zijn eigen collector.lock.
Een incomplete CVD-pipeline blokkeert de tien gewone marktmetrics of upload niet.
Een defect voltooid bewijs wordt als inspectiepunt gemeld. Private kandidaatdata
blijven buiten GitHub; alleen aggregaten met methode en scope worden gepubliceerd.
Bewijsdata nemen schijfruimte in; deze wijziging verwijdert geen historische gegevens.
--check doet nog steeds geen herstel, migratie of netwerkverzameling.

De dashboardkaarten tonen 'Bitget-dekking gecontroleerd · buy−sell volgens bron'
uitsluitend met de juiste methode/scope en een eindige delta. De beperkingen op
taker-toewijzing en cumulatieve CVD staan zichtbaar bij die kaarten. Cloud/manual
runs nemen geen NAS-kandidaatpad uit de omgeving over; de GitHub-reserve verwijdert
zowel BTC_CVD_DB als BTC_CVD_BACKFILL_STORE.

Primaire bronnen, geraadpleegd 23 oktober 2026:
- [Bitget Classic Spot Market API](https://www.bitget.com/docs/catalog/classic-spot-market/classic-spot-market)
- [Bitget Classic Contract Market API](https://www.bitget.com/docs/catalog/classic-contract-market/classic-contract-market)

## Nog nodig voor volledige CVD

De provider-scoped intervaldelta is implementeerbaar met bovenstaande controles.
Onafhankelijke taker-attributie en eventuele marktbrede conclusies zijn daarmee
niet bewezen. Cumulatieve CVD vereist daarnaast een zichtbare baseline en expliciete
onderbrekingen bij onbekende dekking. Deze wijziging bouwt geen cumulatieve reeks,
verzint geen geschiedenis en verandert geen bestaande heuristische biasgraden.

## Controleren

`python3 -m unittest discover -s tests` omvat echte SQLite-tests voor precisie,
marktisolatie, replay, tijdgrenzen, oude OPEN-gaten, lege/ongeldige brondata,
WAL-concurrentie, feedintegratie en dashboardweergave. De JavaScript-test gebruikt
Node indien aanwezig en vervangt geen visuele mobiele controle.

`tests/test_cvd_sessions.py` controleert daarnaast een echte abrupte subprocess-crash,
additieve schema-upgrade, marktisolatie, atomische rollback, conflicterende replay,
out-of-order trades, ACK-deadline, ongeldige frames en pings tijdens een drukke feed.
De tests gebruiken nagebootste sockets, zonder netwerk of websocket-client-installatie;
zij vervangen geen echte Bitget-protocoltest of volledige dekkingscontrole.

Na merge: actualiseer de NAS-checkout onder publish.lock en voer daarna de bestaande
NAS-runner buiten die buitenste lock uit. Die draait de tests, verwerkt de actuele
historiestatus en publiceert de snapshot. Controleer daarna cvd_4h en Pages.
De bestaande sessierecorder blijft actief; een repository-update vervangt de
geïnstalleerde versiemap niet automatisch.

