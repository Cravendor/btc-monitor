# BTC-monitor — elke vier uur

## Starten op GitHub

1. Maak een lege **Public** repository, bijvoorbeeld `btc-monitor`. De code en marktdata worden openbaar. Standaard GitHub-hosted runners zijn gratis voor openbare repositories; private repositories hebben planlimieten.
2. Pak het ZIP-bestand uit. Upload de inhoud van `btc-monitor` naar de hoofdmap van de repository. Let op: `.github/workflows/btc.yml` is een verborgen map/bestand; controleer dat het daadwerkelijk op GitHub staat. Je kunt via **Add file → Create new file** de volledige bestandsnaam `.github/workflows/btc.yml` invoeren en de inhoud plakken.
3. Zorg dat de bestanden op de standaardbranch staan. Open **Actions → BTC market snapshots → Run workflow** en voer een eerste run uit.
4. Controleer de samenvatting van de run en de nieuwe JSON onder `data/JJJJ/MM/DD/`. Een rode run kan bewust betekenen dat Binance een fout gaf: de foutstatus is dan wel opgeslagen.

De workflow heeft alleen `contents: write` nodig om de gegevens in deze repository te bewaren. GitHub geeft daarvoor automatisch een tijdelijk token. Geen Binance-account, Binance-API-key, handmatig token of trading permissions nodig. Deel geen sleutels in de chat. Branchbescherming of organisatiebeleid kan de opslag blokkeren; gebruik dan bij voorkeur een aparte datarepository waar deze workflow mag schrijven.

## Gegevens en betekenis

| Veld | Publieke bron | Betekenis |
|---|---|---|
| spot_price | `https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT` | Laatste spotprijs, in USDT; geen bron-tijdstempel in deze respons, daarom lokale UTC-observatietijd |
| open_interest | `https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT` | Huidige USDⓈ-M futures open interest in BTC; geen USDT-notional |
| funding | `https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT` | `lastFundingRate` zoals Binance rapporteert, markprijs, brontijd en volgende fundingtijd; geen fundinghistorie |

Funding is een decimale verhouding: `0.0001` betekent `0.01%`. Een meting elke vier uur betekent niet dat funding iedere vier uur wordt afgerekend. De API-respons wordt ongewijzigd bewaard nadat verplichte velden zijn gevalideerd. De aanvragen zijn opeenvolgend, geen gelijktijdige marktmeting.

Elke meting bevat begin-/eindtijd in UTC, een eigen observatietijd per bron, URL, aantal pogingen en status. Per bron: `ok`, `missing_data` bij ontbrekende velden, of `error` bij netwerk-, HTTP- of ongeldige-datafouten. Onbruikbare data blijven `null`, nooit nul of een oude waarde. Het totaal is `ok`, `partial` of `error`. Time-outs en serverfouten krijgen maximaal drie pogingen; HTTP 4xx, 418, 429 en regionale blokkades worden direct vastgelegd zonder omweg. Opslagfouten maken de workflow ook rood.

## Planning en beperkingen

De planning is 00:17, 04:17, 08:17, 12:17, 16:17 en 20:17 **UTC**, onafhankelijk van Nederlandse zomer-/wintertijd. GitHub kan runs vertragen of overslaan. Openbare repositories kunnen na 60 dagen zonder repositoryactiviteit hun planning verliezen; controleer Actions als er geen nieuwe bestanden verschijnen. Een geheel niet gestarte run kan zelf geen foutbestand schrijven. Controleer dus ook gaten tussen tijdstempels. Er wordt niet achteraf aangevuld.

Binance kan GitHub-runner-IP's of regio's blokkeren (bijvoorbeeld HTTP 451/403). De eerste handmatige run moet bevestigen dat alle drie bronnen bereikbaar zijn. De workflow probeert zulke beperkingen niet te omzeilen. De verzameling draait pas nadat je de bestanden op GitHub hebt gezet.

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
