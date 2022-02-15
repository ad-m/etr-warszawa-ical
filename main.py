#!/usr/bin/env python
import csv
import datetime
import os
import re
from time import strptime
import itertools

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, vText
from io import StringIO
from pytz import timezone

csv.register_dialect("etr", delimiter=" ", quotechar="'", quoting=csv.QUOTE_ALL)

ETR_URL = "https://bip.warszawa.wsa.gov.pl/183/elektroniczny-terminarz-rozpraw.html"

session = requests.Session()


def fix_dict(row):
    return {key.strip(";"): value.strip(";") for key, value in row.items()}


def clean_text(text):
    return re.sub(r"\s+", " ", text)


def dedupe(items, keygen):
    keys = set()
    for item in items:
        key = keygen(item)
        if key in keys:
            continue
        items.add(key)
        yield item


def row_to_text(row):
    return "\n".join(
        "{}:{}".format(key, clean_text(value)) for key, value in sorted(row.items())
    )


def etr_query(**kwargs):
    time_start = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime(
        "%Y-%m-%d"
    )
    time_end = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime(
        "%Y-%m-%d"
    )
    data = {
        "sygnatura": "",
        "data_posiedzenia": time_start,
        "data_posiedzenia_do": time_end,
        "sala_rozpraw": "Wszystkie",
        "typ_posiedzenia": "'N', 'J', 'P'",
        "wydzial_orzeczniczy": "Wszystkie",
        "opis": "",
        "wynik": "",
        "sortowanie": "3",
        "act": "szukaj",
        "get_csv": "1",
        "guzik": "Filtruj / Sortuj",
    }
    data.update(kwargs)
    soup = BeautifulSoup(session.post(ETR_URL, data=data).text, "html.parser")
    csv_text = soup.find("div", attrs={"id": "csv_text"}).text
    csv_data = csv.DictReader(StringIO(csv_text), dialect="etr")
    return map(fix_dict, csv_data)


def make_cal(data):
    cal = Calendar()
    cal["summary"] = "Cases of Freedom of Information in Warsaw"
    if not data:
        raise Exception("Not found any events")
    for row in data:
        event = Event()
        try:
            struct = strptime(row["Data"] + " " + row["Godzina"], "%Y-%m-%d %H:%M")
        except ValueError:
            struct = strptime(row["Data"], "%Y-%m-%d")
        event.add(
            "dtstart",
            datetime.datetime(*struct[:6]).replace(tzinfo=timezone("Europe/Warsaw")),
        )
        tag = {"Jawne": "J", "Niejawne": "N", "Publikacja": "P"}.get(
            row["Typ posiedzenia"], "?"
        )
        event["summary"] = "[{tag}] {organ} - {sygnatura}".format(
            tag=tag, organ=row["Organ administracji"], sygnatura=row["Sygnatura akt"]
        )
        event["description"] = row_to_text(row)
        event["location"] = vText(
            "Wydzial %s, WSA Warszawa" % (row["Wydział orzeczniczy"])
        )
        cal.add_component(event)
    return cal


def main():
    keygen = lambda item: item["Sygnatura akt"] + item["Data"] + item["Typ posiedzenia"]
    rows = itertools.chain(
        etr_query(symbol=648), etr_query(symbol=6480), etr_query(symbol=6481)
    )
    rows = dedupe(rows, keygen)
    rows = list(rows)
    if len(rows) == 0:
        raise Exception("Missing data to fetch")
    cal = make_cal(rows)
    open("648.ics", "wb").write(cal.to_ical())


if "DSN_URL" in os.environ:
    import raven

    client = raven.Client(
        dsn=os.environ["DSN_URL"],
        release=raven.fetch_git_sha(os.path.dirname(__file__)),
    )
    try:
        main()
    except Exception:
        client.captureException()
        raise
else:
    main()
