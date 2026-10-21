# Voorbereiding CVD — budget €0

Status: ontwerp voorbereid; geen dienst aangemaakt en geen 24/7 collector actief.

De bestaande 4H Actions-verzamelaar blijft actief. Gebruik Actions niet als continu draaiende server.
Een mogelijke kosteloze host is de eigen Synology NAS of een bestaande computer die al 24/7 draait. Nieuwe cloudhosting, abonnementen of betaalde API's worden niet geactiveerd. Stroom- en internetgebruik van eigen apparatuur zijn niet kosteloos; controleer of de apparatuur toch al draait.

## Contract voor de latere collector

- Publieke Bitget spot- en USDT-futures trade-streams, afzonderlijke reeksen, BTC-volume als eenheid. Eerst de actuele publieke WebSocket-documentatie en aggressorbetekenis valideren.
- Per trade: markt, trade-ID, exchange-tijd, ontvangsttijd, prijs, BTC-volume en aggressorrichting. Taker buy positief, taker sell negatief.
- SQLite op persistent volume met unieke sleutel (markt, trade-ID), reconnect met backoff en logboek voor verbindingsgaten. Geen geheime sleutels voor marktdata.
- Aggregeer UTC-intervallen van 4 uur: delta = som(getekend BTC-volume), plus aantal trades, eerste/laatste tijd en expliciete dekkingsstatus. Cumulatieve CVD heeft een vast en zichtbaar startpunt.
- Bij reconnect of start midden in een interval: interval onvolledig tenzij volledigheid aantoonbaar via backfill kan worden hersteld. Nooit een gedeeltelijke delta als volledige 4H-CVD presenteren.
- Streamstilte alleen bewijst geen datagat of volledigheid; vergelijk provider-sequenties indien beschikbaar en documenteer detectiebeperkingen.
- Export via atomisch vervangen JSON. Snapshotcollector leest alleen geldige afgesloten intervallen, met bron, baseline, eenheid en gaten. Geen verzonnen historische CVD.
- Liquidaties uitsluitend als aparte, beperkte feed als de publieke bron die werkelijk levert; geen garantie op marktbrede dekking.

## Acceptatie vóór activering

Controleer dubbelen, reconnect tijdens een interval, herstart na crash, out-of-order trades, UTC-grenzen, schijfvulling en vergelijking van volumes met beurscandles. Kies vervolgens een bestaande host; er is nog geen host gekozen of kostenloze uptime gegarandeerd.
