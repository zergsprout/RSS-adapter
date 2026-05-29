import os, requests, datetime, email.utils
import xml.etree.ElementTree as ET

API_KEY = os.environ["FRED_API_KEY"]

SERIES = [
    "REAINTRATREARAT10Y",
    "REAINTRATREARAT1YE",
    "NFCI",
    "BAMLH0A0HYM2",
    "BAA10YM",
    "T10YFF",
]

rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")

ET.SubElement(channel, "title").text = "Custom FRED Macro Feed"
ET.SubElement(channel, "link").text = "https://fred.stlouisfed.org/"
ET.SubElement(channel, "description").text = "Latest raw FRED observations"
ET.SubElement(channel, "language").text = "en-us"
ET.SubElement(channel, "lastBuildDate").text = email.utils.format_datetime(
    datetime.datetime.now(datetime.UTC)
)

for sid in SERIES:
    try:
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

        obs = r.json()["observations"][0]
        date = obs["date"]
        value = obs["value"]

        # Convert FRED observation date into RSS pubDate
        obs_date = datetime.datetime.strptime(date, "%Y-%m-%d").replace(
            tzinfo=datetime.UTC
        )

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = f"{sid}: {value}"
        ET.SubElement(item, "link").text = f"https://fred.stlouisfed.org/series/{sid}"
        ET.SubElement(item, "guid", isPermaLink="false").text = f"{sid}-{date}-{value}"
        ET.SubElement(item, "pubDate").text = email.utils.format_datetime(obs_date)
        ET.SubElement(item, "description").text = f"{value} ({date})"

    except Exception as e:
        print(f"Skipped {sid}: {e}")

os.makedirs("public", exist_ok=True)
ET.ElementTree(rss).write(
    "public/fred-rss.xml",
    encoding="utf-8",
    xml_declaration=True
)
