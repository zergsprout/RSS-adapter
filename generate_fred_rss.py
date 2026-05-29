import os
import datetime
import email.utils
import xml.etree.ElementTree as ET

import requests

API_KEY = os.environ["FRED_API_KEY"]

SERIES = [
    "REAINTRATREARAT10Y",
    "REAINTRATREARAT1YE",
    "NFCI",
    "BAMLH0A0HYM2",
    "BAA10YM",
    "T10YFF",
]

OUTPUT_DIR = "public"
OUTPUT_FILE = "feed.xml"

rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")

ET.SubElement(channel, "title").text = "Custom FRED Macro Feed"
ET.SubElement(channel, "link").text = "https://zergsprout.github.io/RSS-adapter/feed.xml"
ET.SubElement(channel, "description").text = "Latest raw FRED observations"
ET.SubElement(channel, "language").text = "en-us"
ET.SubElement(channel, "lastBuildDate").text = email.utils.format_datetime(
    datetime.datetime.now(datetime.UTC)
)

for sid in SERIES:
    r = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={
            "series_id": sid,
            "api_key": API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
        },
        timeout=30,
    )
    r.raise_for_status()

    observations = r.json().get("observations", [])
    if not observations:
        raise RuntimeError(f"No observations returned for {sid}")

    obs = observations[0]
    date = obs["date"]
    value = obs["value"]

    obs_date = datetime.datetime.strptime(date, "%Y-%m-%d").replace(
        tzinfo=datetime.UTC
    )

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = f"{sid}: {value}"
    ET.SubElement(item, "link").text = f"https://fred.stlouisfed.org/series/{sid}"
    ET.SubElement(item, "guid", isPermaLink="false").text = f"{sid}-{date}-{value}"
    ET.SubElement(item, "pubDate").text = email.utils.format_datetime(obs_date)
    ET.SubElement(item, "description").text = f"{sid}: {value} ({date})"

os.makedirs(OUTPUT_DIR, exist_ok=True)

ET.indent(rss, space="  ", level=0)

ET.ElementTree(rss).write(
    os.path.join(OUTPUT_DIR, OUTPUT_FILE),
    encoding="utf-8",
    xml_declaration=True,
)

print(f"Wrote {OUTPUT_DIR}/{OUTPUT_FILE}")
