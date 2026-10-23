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
- `value: null` en `coverage_verified: false`: volledige interval-CVD is niet
  vastgesteld. Dit verandert niet bij nul geregistreerde gaten.
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

De health-export houdt coverage_verified=false en cvd_4h=null. Het extra veld
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
Geen automatische retries, achtergrondtaken of installatie. Een mislukte run
bewaart de reeds gevalideerde pagina's voor inspectie; een nieuwe run begint
opnieuw en vervangt de oude run niet.

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
onafhankelijk bewezen compleet zijn. coverage_verified blijft false, value blijft
null, en de bestaande exporter/het dashboard gebruiken de kandidaten nog niet.
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

Primaire bronnen, geraadpleegd 23 oktober 2026:
- [Bitget Classic Spot Market API](https://www.bitget.com/docs/catalog/classic-spot-market/classic-spot-market)
- [Bitget Classic Contract Market API](https://www.bitget.com/docs/catalog/classic-contract-market/classic-contract-market)

## Nog nodig voor volledige CVD

Deze koppeling repareert geen historische gaten en claimt geen volledige CVD.
De sessieregistratie is geïnstalleerd; de herstelkandidaten moeten nog op een echt
afgesloten interval worden getest. Daarna ontbreken exchange-dekkingsbewijs,
event-time-watermarks en afhandeling
van achterstallige berichten. Reconnects
vereisen aantoonbaar volledige backfill of een expliciet ongeldig interval;
alleen opnieuw verbinding maken of oude markers sluiten is geen bewijs.

Voor een status ok moet de bewijsroute voor het hele gesloten interval controleerbaar
zijn, met consistente marktidentiteit/eenheden, tijdgrenzen, deduplicatie en
verificatie van ontbrekende trades. Zonder dat bewijs blijft volledige CVD null.
Cumulatieve CVD vereist daarnaast een zichtbare baseline en een expliciete
onderbreking bij onbekende dekking. Er wordt geen geschiedenis verzonnen.

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

Na merge: controleer de normale NAS-upload en voer de nieuwe backfill-tests en
herstelopdracht eerst handmatig uit. De bestaande sessierecorder blijft actief;
een repository-update vervangt de geïnstalleerde versiemap niet automatisch.
De halfuurlijkse taak en het dashboard gebruiken de herstelkandidaten nog niet.

