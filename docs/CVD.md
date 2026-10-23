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

## Nog nodig voor volledige CVD

Deze koppeling repareert geen historische gaten en claimt geen volledige CVD.
Een vervolgstap moet subscription acknowledgements, sessiegrenzen, persistente
watermarks, disconnects, invalid frames en achterstallige berichten registreren.
Een crash moet ook na herstart een onbevestigd tijdvak achterlaten. Reconnects
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

Na merge: controleer de eerstvolgende normale NAS-upload, de cvd_4h-velden en
de Pages-publicatie. De bestaande taak en CVD-collector hoeven niet te veranderen.
