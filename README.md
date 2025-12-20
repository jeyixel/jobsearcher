# Jobsearcher Backend

Collects Sri Lankan internship listings from multiple sites and saves them locally or publishes new jobs to Firebase Firestore with push notifications via FCM.

## Overview
- Sources: JobHub.lk, Devjobs.lk, ITPro.lk
- Local run: Scrapes concurrently and writes `all_internships.json`
- Bot run: Compares new jobs against Firestore, writes new ones, sends a topic notification (`internships`) via FCM

## Project Structure
- [Backend/scraper/scraper.py](Backend/scraper/scraper.py): Async Playwright scrapers for each site; saves combined results.
- [Backend/scraper/bot.py](Backend/scraper/bot.py): Orchestrator that writes new items to Firestore and sends FCM notifications.
- [Backend/goodsitestoscrape.txt](Backend/goodsitestoscrape.txt): Reference to target pages (optional).
- [Backend/scraper/serviceAccountKey.json](Backend/scraper/serviceAccountKey.json): Firebase service account (not committed).

## Prerequisites
- Windows with Python 3.10+ installed
- A Firebase project with Firestore and FCM enabled
- Firebase Admin service account JSON placed at: [Backend/scraper/serviceAccountKey.json](Backend/scraper/serviceAccountKey.json)

## Setup
From PowerShell:

```powershell
# Navigate to project root
cd "c:\Users\Janith\Desktop\jobsearcher\jobsearcher"

# (Optional) Use the existing venv under Backend or create a new one
python -m venv Backend\venv
Backend\venv\Scripts\Activate.ps1

# Install Python dependencies
pip install playwright firebase-admin

# Install Playwright browsers
python -m playwright install
```

## Usage
### 1) Scrape and save locally
This writes a single JSON file with all scraped internships.

```powershell
cd Backend\scraper
python scraper.py
```
- Output: `all_internships.json` in the current working directory.

### 2) Save to Firestore + send FCM notification
Requires a valid service account at [Backend/scraper/serviceAccountKey.json](Backend/scraper/serviceAccountKey.json). New jobs are detected by a stable `id` based on the listing URL.

```powershell
cd Backend\scraper
python bot.py
```
- Firestore: Documents written to the `internships` collection using `id` as the document ID.
- FCM: One summary notification to the `internships` topic. Devices must subscribe to receive it.

## Configuration & Customization
- Modify target URLs inside the site-specific functions in [Backend/scraper/scraper.py](Backend/scraper/scraper.py) (`scrape_jobhub()`, `scrape_itpro()`, `scrape_Devjobs()`).
- Use [Backend/goodsitestoscrape.txt](Backend/goodsitestoscrape.txt) as a simple reference list for pages you care about.
- Deduplication: `id` is a deterministic MD5 of the job link; running multiple times won’t create duplicates.

## Troubleshooting
- Playwright errors about missing browsers: run `python -m playwright install`.
- `serviceAccountKey.json` not found: ensure the JSON exists at [Backend/scraper/serviceAccountKey.json](Backend/scraper/serviceAccountKey.json) and the process has read permissions.
- Firestore permission issues: verify the service account has `Firebase Admin` roles and your Firestore is in the correct mode (Production/Datastore Native).

## Notes
- This repo intentionally keeps the scraper headless. For debugging, switch `launch(headless=True)` to `False` in the scraper functions.
- Be mindful of each site’s terms of service and scraping policies.
