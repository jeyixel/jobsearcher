import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_jobhub():
    print("Launching browser...")
    async with async_playwright() as p:
        # headless=False lets you see the browser open (useful for debugging)
        browser = await p.chromium.launch(headless=False) 
        page = await browser.new_page()

        target_url = "https://jobhub.lk/en/Sri%20Lanka/search?q=software%20intern&type=Internship&sort-by=Relevance"
        print(f"Navigating to: {target_url}")
        await page.goto(target_url)

        # -----------------------------------------------------------------------
        # STEP 1: LOAD WAIT
        # -----------------------------------------------------------------------
        # We need to wait for the main list of jobs to appear before scraping.
        # PICK A SELECTOR: Pick the ID or Class of the main container holding the jobs.
        print("Waiting for page content to load...")
        # Try multiple possible selectors — the original value may be missing dots
        container_selectors = [
            "listings-container margin-top-35",
            ".listings-container.margin-top-35",
            ".listings-container .margin-top-35",
            ".listings-container",
            "div.listings-container",
        ]

        container_found = False
        for sel in container_selectors:
            try:
                print(f"Trying container selector: '{sel}'")
                await page.wait_for_selector(sel, timeout=5000)
                print(f"Container selector matched: '{sel}'")
                container_found = True
                break
            except Exception as e:
                print(f"Container selector '{sel}' did not match: {e}")

        if not container_found:
            print("Warning: No container selector matched within time. The page structure or selector may be incorrect.")
            print("Continuing — results may be empty. Consider opening the browser (headless=False) and inspecting the DOM to pick correct selectors.")

        
        # -----------------------------------------------------------------------
        # STEP 2: IDENTIFY THE CARDS
        # -----------------------------------------------------------------------
        # We need a list of all job card elements.
        # PICK A SELECTOR: The class name shared by every single job card (e.g., '.job-card', '.listing-item').
        # Try several selectors for job cards (could be a tag or a class)
        jobcard_selectors = [
            "job-listing",
            ".job-listing",
            "div.job-listing",
            "job-listing-card",
        ]

        job_cards = []
        for sel in jobcard_selectors:
            try:
                print(f"Trying job-card selector: '{sel}'")
                cards = await page.query_selector_all(sel)
                if cards:
                    job_cards = cards
                    print(f"job-card selector matched: '{sel}', found {len(cards)} cards")
                    break
                else:
                    print(f"Selector '{sel}' returned 0 cards")
            except Exception as e:
                print(f"Error when querying selector '{sel}': {e}")

        if not job_cards:
            print("Warning: No job cards found. Check the page and selectors. You may need to adjust the selectors after inspecting the page DOM.")
        else:
            print(f"Found {len(job_cards)} job cards. extracting data...")

        extracted_data = []

        for card in job_cards:
            # -------------------------------------------------------------------
            # STEP 3: EXTRACT DETAILS INSIDE EACH CARD
            # -------------------------------------------------------------------
            # For these, find the selector *inside* the card.
            # Example: if the title is <h3 class="title">, put '.title' below.
            
            # A. Job Title
            try:
                title_element = await card.query_selector("job-listing-title")
                if not title_element:
                    title_element = await card.query_selector(".job-listing-title")
                title_text = await title_element.inner_text() if title_element else "N/A"
            except Exception as e:
                print(f"Error reading title for a card: {e}")
                title_text = "N/A"

            # B. Company Name
            try:
                company_element = await card.query_selector("job-listing-company")
                if not company_element:
                    company_element = await card.query_selector(".job-listing-company")
                company_text = await company_element.inner_text() if company_element else "N/A"
            except Exception as e:
                print(f"Error reading company for a card: {e}")
                company_text = "N/A"

            # C. Date
            # We look for the <li> inside the footer that HAS the specific clock icon class
            try:
                date_element = await card.query_selector(".job-listing-footer li:has(.icon-material-outline-access-time)")
                if not date_element:
                    # fallback: try a more generic footer li
                    date_element = await card.query_selector(".job-listing-footer li")
                date_text = await date_element.inner_text() if date_element else "N/A"
            except Exception as e:
                print(f"Error reading date for a card: {e}")
                date_text = "N/A"

            # Create the object
            job_obj = {
                "job_title": title_text.strip(),
                "company": company_text.strip(),
                "date": date_text.strip()
            }
            
            extracted_data.append(job_obj)

        await browser.close()
        return extracted_data

def save_locally(data):
    filename = "jobhub_internships.json"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\nSUCCESS: Scraped {len(data)} jobs. Data saved to '{filename}'")
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    data = asyncio.run(scrape_jobhub())
    save_locally(data)