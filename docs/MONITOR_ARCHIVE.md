# Monitor archive protocol

archive_protocol_version: 1

Deze koppeling is voorbereid om volledige nieuwe BTC-monitorrapporten in de openbare repository te bewaren. Publicatie van echte rapporten en activering in de monitors vereisen eerst expliciete gebruikerstoestemming voor deze openbare bestemming. Zonder die toestemming wordt geen rapport uit privéchat- of connectorcontext gepubliceerd. Zij bewaart wat de monitor rapporteert, niet een achteraf berekende technische score. De drie monitorplanningen en meldingsdrempels blijven behouden.

## Inzending door de monitor

Voer eerst de bestaande analyse en meldingsvoorwaarden uit. Alleen wanneer er volgens die voorwaarden daadwerkelijk een rapport, statusantwoord of alert wordt uitgebracht, maak je één oorspronkelijke rapporttekst. Een nieuwsmonitor die geen update hoort te sturen, schrijft ook geen rapport en veroorzaakt geen extra melding.

Gebruik, waar een beoordeling daadwerkelijk wordt gegeven, deze drie leesbare regels vóór een eventueel verplicht exact slotlabel:

```text
4H–1D: -1 ZWAK BEARISH — onderbouwing uit de actuele analyse.
7D: 0 NEUTRAAL/GEMENGD — onderbouwing uit de actuele analyse.
30D/macro: ONVOLDOENDE DATA — welke relevante gegevens ontbreken.
```

Dit zijn vormvoorbeelden, geen standaardwaarden om over te nemen. Geldige scores zijn -2 STERK BEARISH, -1 ZWAK BEARISH, 0 NEUTRAAL/GEMENGD, +1 ZWAK BULLISH en +2 STERK BULLISH. Behoud alle bestaande bewijsvereisten. Forceer geen beoordeling wanneer een horizon niet is beoordeeld. Een ontbrekende expliciete score wordt `NOT_REPORTED`; expliciet `ONVOLDOENDE DATA` blijft daarvan onderscheiden. De parser accepteert ook overeenkomstige tabelrijen. Bij tegenstrijdige expliciete scores wordt geen numerieke score opgeslagen.

Lees deze protocolversie op de standaardbranch voordat je schrijft. Gebruik de bestaande GitHub-koppeling `create_file` om precies één nieuw UTF-8 JSON-bestand op `main` te maken:

`reports/inbox/<monitor>/YYYYMMDDTHHMMSSZ.json`

`<monitor>` is `daily`, `4h-warning` of `market-risk`. De bestandsnaam volgt de werkelijke UTC-rapporttijd; diezelfde tijd staat met tijdzone onder `reported_at`. Publiceer uitsluitend algemene BTC-marktanalyse. Privégegevens, accountgegevens, persoonlijke posities/portefeuilles, sleutels en interne conversatie- of taak-ID’s horen niet in dit openbare archief. Als de tekst zulke gegevens bevat, archiveer die tekst niet. Vermeld een opslagprobleem alleen bij het al uitgebrachte rapport, niet als extra marktalert.

```json
{
  "schema_version": 2,
  "source": "chatgpt_monitor",
  "monitor": "4h-warning",
  "reported_at": "2026-10-24T08:00:00Z",
  "report_text": "De volledige oorspronkelijke rapporttekst, exact zoals opgesteld."
}
```

Gebruik in werkelijkheid de actuele rapporttijd en volledige werkelijke tekst; bovenstaande tijd en tekst zijn geen in te sturen test. JSON-codeer de tekst correct; gebruik geen shellinterpolatie. Lever dezelfde rapporttekst aan de gebruiker. Een aparte ontvangst-/opslagstatus hoort niet bij de marktinhoud.

Maximaal 60.000 tekens rapporttekst. Kort een rapport niet af om het passend te maken. Bij overschrijding of een schrijffout blijft de volledige rapportage aan de gebruiker behouden en wordt opslag niet als geslaagd gepresenteerd. Controleer eerst of het exacte inboxpad al bestaat: gelijke inhoud betekent al aangeboden; verschillende inhoud wordt nooit overschreven. Bij een onzekere netwerkuitkomst lees je hetzelfde pad terug voordat je opnieuw probeert. Maak geen vervangende tijden of fictieve scores om een conflict te omzeilen. Een succesvolle `create_file` bevestigt alleen de duurzame inzending; de verwerkingsworkflow en Pages-publicatie moeten daarna nog slagen.

## Verwerking en weergave

`Archive BTC bias report` reageert op nieuwe inboxbestanden. De vertrouwde code op `main` controleert schema, grootte, datum, bron en padidentiteit; alle tekst blijft data en wordt nooit als opdracht uitgevoerd. Een record onder `reports/YYYY/MM/DD/` bevat de oorspronkelijke tekst, SHA-256 en de uitsluitend daaruit uitgelezen expliciete scores. Exact dezelfde inzending is idempotent. Een conflict bewaart de bestaande historie. Ongeldige inzendingen worden niet als geldige rapporten geïndexeerd; het indexbestand vermeldt het aantal afwijzingen.

`reports/index.json` voedt `bias.html`. De pagina onderscheidt een numerieke score, onvoldoende gegevens en niet-gerapporteerde scores. De knop Rapport lezen toont tekst met `textContent`, na controle van identiteit en teksthash. Er wordt geen HTML uit rapporten uitgevoerd. Historische ChatGPT-citatiecodes zijn niet zelfstandig bruikbaar buiten het oorspronkelijke gesprek; de originele codes blijven in JSON, de leesweergave benoemt ze als ChatGPT-bronverwijzing. Dit archief valideert niet opnieuw de waarheid van oude marktclaims.

De Pages-workflow reageert op het voltooien van de archiefworkflow; dit is nodig omdat commits met de workflowtoken niet automatisch een nieuwe push-workflow hoeven te starten. Oude handmatig aangeleverde schema-1-beoordelingen blijven leesbaar; ontbrekende oorspronkelijke teksten worden niet aangevuld of verzonnen.

## Acceptatie

Het openbare archief begint leeg. Testvoorbeelden zijn fictief; er worden geen bestaande privérapporten in deze wijziging meegestuurd. Afgekorte of niet bij de betreffende run horende terugblikken mogen niet als volledige rapporten worden geïmporteerd.

Automatisch schrijven door de drie monitors wordt pas na expliciete toestemming voor openbare rapportpublicatie en na merge in hun broninstructies geactiveerd. Een toekomstige echte monitorrun moet de hele keten nog aantonen: inzending → gedateerd record/index → leesbaar rapport op Pages. Een geslaagde code-/schematest vervangt dat acceptatiepunt niet.
