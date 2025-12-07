import asyncio
import sys
from playwright.async_api import async_playwright


async def scrape_example(page):
    await page.goto("https://example.com")
    title = await page.title()
    return {"url": "https://example.com", "title": title}


async def scrape_quotes(page, max_quotes: int = 5):
    # Site intentionally provided for scraping practice
    url = "http://quotes.toscrape.com"
    await page.goto(url)
    quotes = []
    elems = await page.query_selector_all('.quote')
    for i, el in enumerate(elems):
        if i >= max_quotes:
            break
        text_el = await el.query_selector('.text')
        author_el = await el.query_selector('.author')
        text = await text_el.inner_text() if text_el else ""
        author = await author_el.inner_text() if author_el else ""
        quotes.append({"text": text, "author": author})
    return {"url": url, "quotes": quotes}


async def run_scrapers(headless: bool = True):
    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        # Example.com scraper
        try:
            results['example'] = await scrape_example(page)
        except Exception as e:
            results['example'] = {"error": str(e)}

        # Quotes scraper (site designed for scraping practice)
        try:
            results['quotes'] = await scrape_quotes(page)
        except Exception as e:
            results['quotes'] = {"error": str(e)}

        await browser.close()
    return results


def print_results(results):
    print('\n=== Scrape Results ===')
    if 'example' in results:
        ex = results['example']
        if 'error' in ex:
            print(f"example.com: ERROR: {ex['error']}")
        else:
            print(f"example.com title: {ex.get('title')}")

    if 'quotes' in results:
        q = results['quotes']
        if 'error' in q:
            print(f"quotes.toscrape.com: ERROR: {q['error']}")
        else:
            print(f"quotes.toscrape.com ({len(q.get('quotes', []))} quotes):")
            for i, quote in enumerate(q.get('quotes', []), start=1):
                print(f"  {i}. {quote['text']} — {quote['author']}")


if __name__ == "__main__":
    # simple CLI: optional arg 'headless=false' to show browser
    headless = True
    for arg in sys.argv[1:]:
        if arg.lower().startswith('headless='):
            val = arg.split('=', 1)[1].lower()
            headless = False if val in ('false', '0', 'no') else True

    results = asyncio.run(run_scrapers(headless=headless))
    print_results(results)