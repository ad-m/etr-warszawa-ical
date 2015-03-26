#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from icalendar import Calendar, Event, vText
from time import strptime
import datetime
HEADER_STYLE = 'border-width: 2px; border-style: double;'
END_STYLE = 'border-bottom-width: 2px; border-bottom-style: double; border-top: none;'
MSG = """Organ: {organ}
Sygnatura: {sygnatura}
Symbole: {symbol}
Przedmiot: {przedmiot}
Sklad: {sklad}
Termin: {data} {godzina}"""


def etr_query(**kwargs):
    data = {'wydzial_orzeczniczy': '---',
            'symbol': '',
            'sygnatura': '',
            'sortowanie': '3',
            'sala_rozpraw': '---',
            'opis': '',
            'guzik': 'Filtruj / Sortuj',
            'data_posiedzenia': '',
            'act': 'szukaj', }
    data.update(kwargs)
    soup = BeautifulSoup(requests.post(
        'http://www.warszawa.wsa.gov.pl/183/elektroniczny-terminarz-rozpraw.html', data=data).text)
    data = []
    data.append({})

    for i, row in enumerate(soup.select('table.ftabela_123 tr')):
        if not row.has_attr('style'):
            record = data[len(data)-1]
            # ['III', <br/>, 'III SA/Wa 1698/14', <br/>]
            record['wydzial'] = row.select('td')[0].contents[0]
            record['sygnatura'] = row.select('td')[0].contents[2]
            record['data'], record['godzina'], record['sala'] = row.select('td')[1].strings
            # ('Dyrektor Izby Skarbowej w Warszawie', '6118 - Koszty; Koszty')
            record['organ'] = row.select('td')[2].contents[0]
            record['symbol'] = row.select('td')[2].contents[2]
            record['symbole'] = [x.strip() for x in record['symbol'].split('-')[0].split('/')]
            record['przedmiot'] = row.select('td')[2].contents[5].text
            record['sklad'] = []
            # [' Andrzej Czarnecki',
            # <br/>,
            # ' Izabela Głowacka-Klimas',
            # <br/>,
            # '  Henryka Lewandowska-Kuraszkiewicz (spr.)',
            # <br/>]
            for el in row.select('td')[3]:
                if type(el) == NavigableString:
                    record['sklad'].append(el.strip())
            # <span style="color: #F00;">PUBLIKACJA</span>
            el = row.find('span', style='color: #F00;')
            if el:
                record['note'] = el.text
            data[len(data)-1] = record
        if row.has_attr('style') and row['style'] == END_STYLE:
            data[len(data)-1]['orzeczenie'] = [x.strip() for x in row.strings]
            data.append({})
    return data[:-1]
data = etr_query()
data = [row for row in data if '648' in row['symbole']]

cal = Calendar()
cal['summary'] = 'Cases of Freedom of Information in Warsaw'

for row in data:
    event = Event()
    struct = strptime(row['data']+" "+row['godzina'], "%Y-%m-%d %H:%M")
    event.add('dtstart', datetime.datetime(*struct[:6]))
    event['summary'] = MSG.format(**row)
    event['location'] = vText('Wydzial %s, WSA Warszawa' % (row['wydzial']))
    cal.add_component(event)
open('648.ics', 'wb').write(cal.to_ical())

