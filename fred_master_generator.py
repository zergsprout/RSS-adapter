#!/usr/bin/env python3
import os
import html
import requests
import xml.etree.ElementTree as ET
from email.utils import formatdate

FRED_API_KEY = os.environ["FRED_API_KEY"]

SERIES = [
    {
        "id": "REAINTRATREARAT10Y",
        "title": "10-Year Real Interest Rate",
        "link": "https://fred.stlouisfed.org/series/REAINTRATREARAT10Y",
    },
    {
        "id": "REAINTRATREARAT1YE",
        "title": "1-Year Real Interest Rate",
        "link": "https://fred.stlouisfed.org/series/REAINTRATREARAT1YE",
    },
    {
        "id": "NFCI",
        "title": "Chicago Fed National Financial Conditions Index",
        "link": "https://fred.stlouisfed.org/series/NFCI",
    },
    {
        "id": "BAMLH0A0HYM2",
        "title": "ICE BofA US High Yield Index Option-Adjusted Spread",
        "link": "https://fred.stlouisfed.org/series/BAMLH0A0HYM2",
    },
    {
        "id": "BAA10YM",
        "title": "Moody's Seasoned Baa Corporate Bond Yield Relative to 10-Year Treasury",
        "link": "https://fred.stlouisfed.org/series/BAA10YM",
    },
    {
        "id": "T10YFF",
        "title": "10-Year Treasury Constant Maturity Minus Federal Funds Rate",
        "link": "https://fred.stlouisfed.org/series/T10YFF",
    },
]

OBS_URL = "https://api.stlouisfed.org/fred/series/observations"
SERIES_URL = "https://api.stlouisfed.org/fred/series"

def get_series_meta(series_id):
    r = requests.get(
        SERIES_URL,
        params={
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()["seriess"][0]
    return {
        "title": data.get("title", series_id),
        "frequency": data.get("frequency", ""),
        "units": data.get("units", ""),
        "notes": data.get("notes", ""),
        "last_updated": data.get("last_updated", ""),
    }

def get_latest_observation(series_id):
    r = requests.get(
        OBS_URL,
        params={
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 12,
        },
        timeout=30,
    )
    r.raise_for_status()
    observations = r.json().get("observations", [])
    for obs in observations:
        if obs.get("value") not in (".", None, ""):
            return {"date": obs["date"], "value": obs["value"]}
    raise ValueError(f"No valid observation found for {series_id}")

def cdata(text):
    return f"<![CDATA[{text}]]>"

def build_item(cfg):
    meta = get_series_meta(cfg["id"])
    latest = get_latest_observation(cfg["id"])

    item = ET.Element("item")
    ET.SubElement(item, "title").text = f'{cfg["id"]}: {meta["title"]} = {latest["value"]}'
    ET.SubElement(item, "link").text = cfg["link"]
    ET.SubElement(item, "guid").text = f'{cfg["id"]}-{latest["date"]}-{latest["value"]}'
    ET.SubElement(item, "pubDate").text = formatdate(usegmt=True)

    desc = (
        f"<p><strong>Series:</strong> {html.escape(cfg['id'])}</p>"
        f"<p><strong>Title:</strong> {html.escape(meta['title'])}</p>"
        f"<p><strong>Latest observation date:</strong> {html.escape(latest['date'])}</p>"
        f"<p><strong>Latest value:</strong> {html.escape(latest['value'])}</p>"
        f"<p><strong>Frequency:</strong> {html.escape(meta['frequency'])}</p>"
        f"<p><strong>Units:</strong> {html.escape(meta['units'])}</p>"
        f"<p><a href=\"{html.escape(cfg['link'])}\">View series on FRED</a></p>"
    )

    description = ET.SubElement(item, "description")
    description.text = cdata(desc)
    return item

def main():
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Custom FRED Macro Feed"
    ET.SubElement(channel, "link").text = "https://fred.stlouisfed.org/"
    ET.SubElement(channel, "description").text = (
        "Latest observations for selected FRED series: "
        "REAINTRATREARAT10Y, REAINTRATREARAT1YE, NFCI, "
        "BAMLH0A0HYM2, BAA10YM, T10YFF"
    )
    ET.SubElement(channel, "lastBuildDate").text = formatdate(usegmt=True)
    ET.SubElement(channel, "language").text = "en-us"

    for cfg in SERIES:
        try:
            channel.append(build_item(cfg))
        except Exception as e:
            item = ET.Element("item")
            ET.SubElement(item, "title").text = f'{cfg["id"]}: ERROR'
            ET.SubElement(item, "link").text = cfg["link"]
            ET.SubElement(item, "guid").text = f'{cfg["id"]}-error'
            ET.SubElement(item, "pubDate").text = formatdate(usegmt=True)
            d = ET.SubElement(item, "description")
            d.text = cdata(f"<p>Failed to fetch {html.escape(cfg['id'])}: {html.escape(str(e))}</p>")
            channel.append(item)

    xml_bytes = ET.tostring(rss, encoding="utf-8")
    with open("feed.xml", "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(xml_bytes)

if __name__ == "__main__":
    main()
