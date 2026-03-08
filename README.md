# Google Places Scraper

Simple GUI tool to search for local businesses using the Google Places API (New) and export results to CSV.

## Setup

1. **Get an API key** — enable the **Places API (New)** in your [Google Cloud Console](https://console.cloud.google.com/apis/library/places-backend.googleapis.com).

2. **Configure your key** — copy `.env.example` to `.env` and paste your key:
   ```
   cp .env.example .env
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Run:**
   ```
   python app.py
   ```

## Usage

| Field      | Example               |
|------------|-----------------------|
| Keyword    | `skating rinks`       |
| Category   | *(optional extra)*    |
| City       | `Springfield, IL`     |

Click **Search** to query the API, then **Export CSV** to save results.

## Cost

The app requests only Basic + Pro tier fields. Google gives a **$200/month free credit** which covers roughly **5,000+ text searches** before any charges apply. See [Places API pricing](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing) for details.
