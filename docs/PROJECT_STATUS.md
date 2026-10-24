# BTC Monitor — scope en openstaande onderdelen

Stand van de controle: 24 oktober 2026. Een werkende NAS-koppeling betekent niet dat het gehele analyseproject is afgerond.

| Onderdeel | Stand | Afbakening |
| --- | --- | --- |
| NAS-metingen en publicatie | Werkend bevestigd | Meerdere opeenvolgende metingen; geen garantie op ononderbroken beschikbaarheid. |
| Spot- en futuresjournal | Werkend bevestigd | Bewaart trades en controlebewijs; bestaande gap-markers blijven behouden. |
| Gecontroleerde Bitget buy−sell-delta | Werkend bevestigd per interval | Publieke historie/candlevolumes gecontroleerd. Agressorzijde niet onafhankelijk geverifieerd; geen volledige marktbrede of cumulatieve CVD. |
| Drie BTC-monitors | Opnieuw ingedeeld op 24 oktober | Eén gecombineerde taak op 00/04/08/12/16/20 uur Europe/Amsterdam, om 08 uur uitgebreide dagversie; aparte psychologische analyse om 12 uur; nieuwsmonitor blijft apart. Oude losse dag-/4H-taken gepauzeerd, historie behouden. Inclusief bestaande VIX-taak zijn vier monitors actief, onder de grens van vijf. De eerstvolgende echte uitvoeringen moeten de nieuwe keten aantonen. |
| Multi-timeframe marktrichting | Bestaand | Technische prijs-/momentum-/volumeheuristiek, niet hetzelfde als geïntegreerde monitorbias of Wall Street-marktpsychologie. |
| Historische signaaltijdlijn | Bestaand | Archiveert native modelsignalen en uitkomsten per model/timeframe, geen volledige monitorrapporten. |
| Hoofdpagina met navigatie | Deze wijziging | De gepubliceerde root wordt overzicht/scenario’s; de bestaande marktmetingen staan op btc-dashboard.html. |
| Prijsniveaus en scenario’s | Deze wijziging | Afgesloten 4H-candles; range van 20 voorafgaande candles, eenvoudige ATR14, expliciete voorwaarden, projecties en ongeldigverklaring. Ongekalibreerd. |
| Volumevergelijking | Deze wijziging op hoofdpagina | Laatste candle tegenover 20 voorafgaande; laatste 6 afgesloten 4H-candles tegenover de 6 daarvoor. Geen volledige 7D/30D-volumetrend toegevoegd. |
| Archief van echte monitorrapporten en geïntegreerde vijfpuntsbias | Koppeling in review; toestemming verleend | Inbox→ongewijzigde rapporttekst→gedateerd record/index→Pages is geïmplementeerd. Het openbare archief start leeg; tests gebruiken fictieve teksten. Publicatie van nieuwe rapporten is expliciet toegestaan op 24 oktober. Schrijven start pas als protocol/code op main staan; een toekomstige echte schrijfrun moet de automatische keten nog aantonen. Native signalen vervangen dit archief niet. |
| GitHub-reserve | Werkende marktmeting aangetoond | Start afhankelijk van GitHub-planning. Geen NAS-CVD bij uitval. Echte uitvaltest niet uitgevoerd. |
| Onafhankelijke agressor-CVD / absorptie- en distributiebevestiging | Open | Gecontroleerde Bitget buy/sell-velden bewijzen dit niet. |
| Psychologie, Fibonacci en Elliott Wave | Aanvullende laag in review | De homepage berekent range-geankerde Fibonacci-niveaus. Monitors krijgen een expliciet protocol voor psychologische fasehypothesen en alternatieve Elliott-tellingen. Geen automatische bevestiging van een fase of complete golftelling; onvoldoende data blijft zichtbaar. |
| Korte, middellange en macro-koersroute | Deze aanvulling | Gescheiden native 4H/1D/1W-routes met voorwaarden en procentuele terugval vanaf een geteste zone. Geen bullcyclus automatisch vastgesteld. ATH alleen via apart gecontroleerde CoinGecko BTC/USD-bron; beperkte Bitget-historie is geen lifetime-record. |

## Scenario-methode

`closed_4h_range20_atr14_v1` is een transparante technische heuristiek, geen gekalibreerd voorspellend model. De beoordeelde candle staat buiten de 20-candle-referentierange. True range is max(high−low, |high−vorig slot|, |low−vorig slot|); ATR14 is het eenvoudige gemiddelde van de laatste 14 referentie-true-ranges, geen Wilder-gemiddelde. De aandachtsdrempels liggen 0,1 ATR buiten de range. Projecties liggen één en twee ATR voorbij de drempel; ze zijn geen beloofde koersdoelen. Ongeldigverklaring gebruikt een volgend 4H-slot aan de andere kant van de rangegrens met 0,1 ATR buffer.

De nieuwste snapshot wordt gebruikt; er wordt niet stilzwijgend teruggevallen op een oudere groene meting. De laatste afgesloten UTC-candle moet aanwezig zijn en de 21 benodigde candles moeten aansluitend en geldig zijn. Bij een ongeldige/verouderde bron worden geen scenario-niveaus gepubliceerd. De browser verbergt de niveaus wanneer de meting één uur oud wordt of een nieuw 4H-venster aanbreekt. Vernieuwen vraagt de nieuwste Pages-publicatie op.

Prijsniveaus horen bij Bitget BTCUSDT USDT-futures, in USDT. Ze mogen niet zonder aanpassing als spotorders, USD-/europrijzen, persoonlijke stop-loss of positiegrootte worden gebruikt. Spot en futuresdelta worden afzonderlijk getoond en alleen bij bewijs voor hetzelfde venster. Ze bepalen geen koop-/verkoopadvies, automatische bias of psychologische fase.

Budget blijft €0. Deze wijziging verandert geen collector, monitorplanning, alertdrempel of betaalde dienst. Publicatie gebeurt na review en merge via de bestaande Pages-workflow.
