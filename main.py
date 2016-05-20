#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, vText
from time import strptime
import datetime
from pytz import timezone
from io import StringIO
from csv import DictReader
import csv


csv.register_dialect('etr', delimiter=' ', quotechar="'", quoting=csv.QUOTE_ALL)

ETR_URL = 'http://www.warszawa.wsa.gov.pl/183/elektroniczny-terminarz-rozpraw.html'


def fix_dict(row):
    return {key.strip(';'): value.strip(';') for key, value in row.items()}


def row_to_text(row):
    return "\n".join(key+": "+value for key, value in row.items())


def etr_query(**kwargs):
    data = {'sygnatura': '',
            'data_posiedzenia': '',
            'data_posiedzenia_do': '',
            'sala_rozpraw': '---',
            'typ_posiedzenia': "'N', 'J', 'P'",
            'wydzial_orzeczniczy': '---',
            'symbol': '648',
            'opis': '',
            'wynik': '',
            'sortowanie': '3',
            'act': 'szukaj',
            'get_csv': '1'}
    data.update(kwargs)
    soup = BeautifulSoup(requests.post(ETR_URL, data=data).text)
    csv_text = soup.find('div', attrs={'id': 'csv_text'}).text
    csv_data = DictReader(StringIO(csv_text), dialect='etr')
    return map(fix_dict, csv_data)

data = etr_query()

cal = Calendar()
cal['summary'] = 'Cases of Freedom of Information in Warsaw'

for row in data:
    event = Event()
    try:
        struct = strptime(row['Data'] + " " + row['Godzina'], "%Y-%m-%d %H:%M")
    except ValueError:
        struct = strptime(row['Data'], "%Y-%m-%d")
    event.add('dtstart', datetime.datetime(*struct[:6]).replace(tzinfo=timezone('Europe/Warsaw')))
    event['summary'] = '{organ} - {sygnatura}'.format(organ=row['Organ administracji'],
                                                      sygnatura=row['Sygnatura akt'])
    event['description'] = row_to_text(row)
    event['location'] = vText('Wydzial %s, WSA Warszawa' % (row['Wydział orzeczniczy']))
    print(event)
    cal.add_component(event)
open('648.ics', 'wb').write(cal.to_ical())
