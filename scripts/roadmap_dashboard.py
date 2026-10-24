"""Render a conditional level ladder with explicit percentage bases."""
from html import escape


def price(value, unit='USDT'):
    return format(value, ',.1f').replace(',', '_').replace('.', ',').replace('_', '.') + ' ' + unit


def pct(value):
    return format(value, '+.2f').replace('.', ',') + '%'


def render(roadmap, ath=None):
    parts = ['<section class="panel" style="margin-top:24px"><h2>Koersroute en mogelijke afwijzing</h2>',
             '<p>Een routekaart met voorwaarden, geen voorspelling dat ieder niveau wordt bereikt. Een bullcyclus is hiermee niet vastgesteld. De eerdere ATH is een aparte langetermijnreferentie.</p>']
    if roadmap.get('status') != 'ready':
        parts.append('<p>ONVOLDOENDE DATA voor een actuele koersroute.</p>')
    else:
        parts.append('<div id="roadmap-levels">')
        for horizon in roadmap['horizons']:
            parts.append('<h3>' + escape(horizon['label']) + '</h3>')
            if horizon['status'] != 'ready':
                parts.append('<p>ONVOLDOENDE DATA · geen vervangende horizon gebruikt.</p>')
                continue
            parts.append('<p>Referentieprijs: <b>' + price(horizon['reference_price']) +
                         '</b>. Broncandles: ' + escape(str(horizon['history_candles'])) + ' × ' + escape(horizon['timeframe']) +
                         '; laatste sluiting <time>' + escape(horizon['last_closed_at']) + '</time>. Tijdschalen zijn analysehorizons, geen aankomstdata.</p>')
            fib = horizon['fibonacci']
            if fib['status'] == 'calculated':
                parts.append('<p>Lineaire Fib-referentie van de vorige 20 candles: ' +
                             ('laag → hoog' if fib['direction'] == 'up' else 'hoog → laag') +
                             '. Low ' + price(fib['low']) + ' · ankercandle vanaf <time>' + escape(fib['low_at']) +
                             '</time>; high ' + price(fib['high']) + ' · ankercandle vanaf <time>' + escape(fib['high_at']) +
                             '</time>. Dit zijn candle-openingen, geen exacte ticktijden.</p>')
            else:
                parts.append('<p>Fib-ankervolgorde niet vast te stellen; alleen de beschikbare rangegrenzen en pivot-lows worden gebruikt.</p>')
            if not horizon['upward']:
                parts.append('<p>Geen bovenliggende niveaus uit deze referentiebeweging beschikbaar. Er wordt geen koersdoel verzonnen.</p>')
                continue
            parts.append('<div style="overflow:auto" tabindex="0" role="region" aria-label="Koersroute, horizontaal schuifbaar"><table><thead><tr><th>Mogelijke volgende zone</th><th>Vanaf referentieprijs</th><th>Bij afwijzing: eerste terugvalzone</th><th>Verdere terugvalzone</th></tr></thead><tbody>')
            for level in horizon['upward']:
                cells = []
                for target in level['rejection_to']:
                    cells.append(price(target['price']) + '<br><b>' + pct(target['change_pct']) + '</b> vanaf de geteste zone' +
                                 '<br><small>' + escape(' / '.join(target['labels'])) + '</small>')
                while len(cells) < 2: cells.append('ONTBREEKT in deze historie')
                parts.append('<tr><td><b>' + price(level['price']) + '</b><br><small>' +
                             escape(' / '.join(level['labels'])) + '</small></td><td>' + pct(level['distance_pct']) +
                             '</td><td>' + cells[0] + '</td><td>' + cells[1] + '</td></tr>')
            parts.append('</tbody></table></div><p>Een afwijzingsscenario vergt een test van de zone en vervolgens een afgesloten ' +
                         escape(horizon['timeframe']) + '-candle terug onder die zone. Een volgend slot erboven ontkracht dat afwijzingsscenario. ' +
                         'Een terugvalzone is een scenario, geen voorspelde bodem. Fib-zones en bevestigde pivot-lows blijven verschillende berekeningen uit dezelfde prijsbron.</p>')
        parts.append('<p>De referentieprijs is Bitget BTCUSDT USDT-futures, niet BTC/USD-spot. Percentage naar boven = (zone/referentieprijs − 1) × 100. ' +
                     'Percentage bij afwijzing = (terugvalzone/geteste zone − 1) × 100. De twee kolommen hebben dus een andere basis.</p></div>')
    parts.append('</section>')
    ath = ath or {'status': 'unavailable'}
    expiry = escape(ath.get('valid_until', ''), quote=True)
    parts.append('<section class="panel" style="margin-top:24px" id="ath-reference" data-valid-until="' + expiry + '"><h2>Uitgezoomd: eerdere ATH als referentie</h2>')
    if ath.get('status') != 'ok':
        parts.append('<p>ATH-referentie ONTBREEKT. Een high in onze beperkte candlehistorie is geen bewezen all-time high. ' +
                     'De overige scenario’s blijven bruikbaar binnen hun eigen bronvenster.</p>')
    else:
        parts.append('<div id="ath-values"><p><b>' + price(ath['ath'], 'USD') + '</b> · volgens CoinGecko, bereikt op <time>' + escape(ath['ath_at']) +
                     '</time>.</p><p>Actuele BTC/USD-referentie van dezelfde aanbieder: ' + price(ath['price'], 'USD') +
                     ' · <time>' + escape(ath['source_at']) + '</time>.</p><p>Benodigde stijging vanaf die USD-prijs: <b>' + pct(ath['to_ath_pct']) +
                     '</b>. Afstand onder de ATH, gemeten vanaf de ATH: <b>' + pct(ath['from_ath_pct']) + '</b>.</p>' +
                     '<p>Dit is een geaggregeerde spotreferentie in USD. Zij wordt niet als exact USDT-futuresniveau in de koersroute gemengd. ' +
                     'Alleen als het langetermijnbullscenario daadwerkelijk wordt ondersteund, kan herovering van oude toppen een te toetsen route zijn; een bullcyclus verplicht geen terugkeer naar de ATH.</p></div>' +
                     '<p id="ath-stale" hidden>ATH-prijsreferentie is verouderd. Vernieuw voor een nieuwe broncontrole.</p>')
    parts.append('<p><a href="https://www.coingecko.com/en/coins/bitcoin">CoinGecko BTC/USD-referentie</a> · gratis openbare bron, geen API-key of betaald alternatief.</p></section>')
    return ''.join(parts)
