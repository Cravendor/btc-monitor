# BTC-monitor — elke vier uur

## Starten op GitHub

1. Maak een lege **Public** repository, bijvoorbeeld `btc-monitor`. De code en marktdata worden openbaar. Standaard GitHub-hosted runners zijn gratis voor openbare repositories; private repositories hebben planlimieten.
2. Pak het ZIP-bestand uit. Upload de inhoud van `btc-monitor` naar de hoofdmap van de repository. Let op: `.github/workflows/btc.yml` is een verborgen map/bestand; controleer dat het daadwerkelijk op GitHub staat. Je kunt via **Add file → Create new file** de volledige bestandsnaam `.github/workflows/btc.yml` invoeren en de inhoud plakken.
3. Zorg dat de bestanden op de standaardbranch staan. Open **Actions → BTC market snapshots → Run workflow** en voer een eerste run uit.
4. Controleer de samenvatting van de run en de nieuwe JSON onder `data/JJJJ/MM/DD/`. Een rode run kan bewust betekenen dat een bron een fout gaf: de foutstatus is dan wel opgeslagen.

De workflow heeft alleen `contents: write` nodig om de gegevens in deze repository te bewaren. GitHub geeft daarvoor automatisch een tijdelijk token. Geen beursaccount, API-key, handmatig token of trading permissions nodig. Deel geen sleutels in de chat. Branchbescherming of organisatiebeleid kan de opslag blokkeren; gebruik dan bij voorkeur een aparte datarepository waar deze workflow mag schrijven.

## Huidige collector en uitbreiding

De bestaande Bitget futuresprijs, OI en funding blijven intact. De collector voegt afgesloten Bitget 4H-candles, futuresorderboek (100 niveaus), Bitget spotprijs, Coinbase/Bitget-premiumproxy, perpetual mark/index-premium en USDT/USDC USD-prijzen toe. Elke bron heeft status, URL en observatietijd. Afgeleide metrics bewaren hun bronresultaten. `data/latest.json` behoudt de bestaande feedvorm en de nieuwste 14 snapshots. Fouten blijven null en worden wel opgeslagen; de workflow meldt onvolledige verzameling als fout.

Orderboekbanden 0,1%, 0,5% en 1% bevatten notional en imbalance; `*_band_covered=false` betekent slechts een ondergrens uit de teruggegeven niveaus. Stablecoinmetingen tonen uitsluitend prijs en depeg, geen totale supply of exchange flows. De Coinbase-premium is expliciet een Bitget-vergelijkingsproxy met USDT/USD-correctie; bronnen ouder dan drie minuten of meer dan twee minuten uiteen worden afgewezen. Futuresbasis betekent hier perpetual mark/index-premium, geen geannualiseerde termijnbasis.

`index.html` leest de openbare `main/data/latest.json` rechtstreeks, zodat snapshots zichtbaar worden zonder elke vier uur een Pages-build. De collector start ook na wijzigingen aan scripts/tests/workflow op main. Activeer in de repository Settings → Pages → Source: GitHub Actions en start **BTC dashboard Pages** eenmaal handmatig. Publicatie en een succesvolle eerste Actions-run zijn nog vereist. De workflow gebruikt uitsluitend standaard publieke runners en slaat private repositories over; geen betaalde dienst of betaalde runner wordt gestart.

Voor CVD: zie [voorbereiding](docs/CVD.md). Er is geen 24/7 host geactiveerd en er worden geen fictieve CVD-waarden getoond.

## Planning en beperkingen

De planning is 00:17, 04:17, 08:17, 12:17, 16:17 en 20:17 **UTC**, onafhankelijk van Nederlandse zomer-/wintertijd. GitHub kan runs vertragen of overslaan. Openbare repositories kunnen na 60 dagen zonder repositoryactiviteit hun planning verliezen; controleer Actions als er geen nieuwe bestanden verschijnen. Een geheel niet gestarte run kan zelf geen foutbestand schrijven. Controleer dus ook gaten tussen tijdstempels. Er wordt niet achteraf aangevuld.

Een beurs kan GitHub-runner-IP's of regio's blokkeren (bijvoorbeeld HTTP 451/403). De eerste handmatige run moet bevestigen welke bronnen bereikbaar zijn. De workflow probeert zulke beperkingen niet te omzeilen. De verzameling draait pas nadat je de bestanden op GitHub hebt gezet.

### Geen 4H CVD uit vijf aggTrades

4H CVD vereist volledige trade-data over het gekozen vieruursinterval, met koop-/verkoopagressorrichting en consistente volume-eenheden. Vijf recente aggTrades zijn slechts een klein fragment en leveren geen geldige 4H CVD op. Daarvoor zijn volledige gepagineerde trade-data (of een aantoonbaar volledige trade-stream/archief) nodig, met controle op tijdgrenzen, gaten en dubbelen. Een cumulatieve reeks vereist daarnaast een gekozen beginpunt. Deze versie zet `cvd_4h.value` expliciet op `null` met status `not_collected`.

## Lokaal controleren

Python 3, geen externe pakketten: `python3 -m unittest discover -s tests`.
Een echte meting: `python3 scripts/collect.py` (schrijft naar `data/`).

## Bronnen

- [Binance spot marktdata](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market)
- [Binance futures marktdata](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)
- [GitHub Actions kosten](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [GitHub geplande workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

## Kostengrens

Budget: **€0 per maand**. Geen betaalde API's, cloudservers, proefabonnementen, grotere runners of upgrades activeren. De nieuwe workflows weigeren uitvoering in een private repository. CVD blijft voorbereiding totdat een bestaande kosteloze host beschikbaar is.

## Aanvullende bronnen

- https://www.bitget.com/docs/catalog/classic-contract-market/classic-contract-market
- https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-ticker

De API-responses zijn lokaal getest; bereikbaarheid vanaf GitHub-hosted runners moet nog met workflow_dispatch worden bevestigd.
