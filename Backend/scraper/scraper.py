import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_jobhub():
    print("Launching browser...")
    async with async_playwright() as p:
        # headless=False lets you see the browser open (useful for debugging)
        browser = await p.chromium.launch(headless=True) 
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
            ".listings-container.margin-top-35",
            "listings-container margin-top-35",
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
                print(f"Page content found using '{sel}'.")
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
            ".job-listing",
            "job-listing",
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

           # ... (after Date section)

            # D. Link
            # Since the card itself is an <a> tag, we get the 'href' directly from it.
            try:
                raw_link = await card.get_attribute("href")
                
                # Handling Relative URLs:
                # The site likely returns "/job?id=123", so we prepend the domain.
                if raw_link and raw_link.startswith("/"):
                    job_link = f"https://jobhub.lk{raw_link}"
                elif raw_link:
                    job_link = raw_link
                else:
                    job_link = "N/A"
            except Exception as e:
                print(f"Error reading link for a card: {e}")
                job_link = "N/A"

            # Update the object
            job_obj = {
                "Site": "JobHub",
                "job_title": title_text.strip(),
                "company": company_text.strip(),
                "date": date_text.strip(),
                "link": job_link  # <--- Added here
            }
            
            extracted_data.append(job_obj)

        await browser.close()
        return extracted_data
    
# Scrape the ITpro.lk internships as well
async def scrape_itpro():
    print("--- Starting ITPro Scraper ---")
    extracted_data = []

    async with async_playwright() as p:
        # Set headless=False to debug and find selectors visually!
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        target_url = "https://itpro.lk/jobs/internship/"
        print(f"[ITPro] Navigating to: {target_url}")
        await page.goto(target_url)

        try:
            # 1. WAIT FOR CONTAINER
            # Look for the big div that holds the list of jobs.
            print("[ITPro] Waiting for content...")
            await page.wait_for_selector("#job-listings", timeout=10000)

            # 2. IDENTIFY CARDS
            # Look for the element that represents ONE job row.
            job_cards = await page.query_selector_all("article")
            print(f"[ITPro] Found {len(job_cards)} cards in ITpro.lk")

            for card in job_cards:
                try:
                    # A. Job Title
                    title_el = await card.query_selector(".job-title")
                    title = await title_el.inner_text() if title_el else "N/A"

                    # B. Company Name
                    company_el = await card.query_selector(".jc-company")
                    company = await company_el.inner_text() if company_el else "N/A"

                    # C. Date
                    date_el = await card.query_selector(".time-posted")
                    date = await date_el.inner_text() if date_el else "N/A"

                    # D. Link
                    # Check if the link is on the card itself or a 'Apply' button inside
                    link_el = await card.query_selector(".job-record-link") 
                    raw_link = await link_el.get_attribute("href") if link_el else "N/A"
                    
                    # Fix relative links if ITPro uses them
                    if raw_link and raw_link.startswith("/"):
                        link = f"https://itpro.lk{raw_link}"
                    else:
                        link = raw_link

                    extracted_data.append({
                        "Site": "ITPro.lk",
                        "job_title": title.strip(),
                        "company": company.strip(),
                        "date": date.strip(),
                        "link": link
                    })
                except Exception as e:
                    print(f"[ITPro] Error parsing a card: {e}")

        except Exception as e:
            print(f"[ITPro] Global error: {e}")

        await browser.close()
        print(f"--- ITPro Finished ({len(extracted_data)} jobs) ---")
        return extracted_data

# ==========================================
# MAIN EXECUTION
# ==========================================
def save_locally(data):
    filename = "all_internships.json"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\nSUCCESS: Saved {len(data)} total jobs to '{filename}'")
    except Exception as e:
        print(f"Error saving file: {e}")

async def main():
    # This runs both scrapers AT THE SAME TIME (Concurrent)
    # It waits for both to finish before continuing.
    print("Running scrapers concurrently...")
    
    # gather returns a list of results: [result_from_jobhub, result_from_itpro]
    results = await asyncio.gather(
        scrape_jobhub(),
        scrape_itpro()
    )
    
    # Flatten the list of lists into one big list
    all_jobs = results[0] + results[1]
    
    save_locally(all_jobs)

if __name__ == "__main__":
    asyncio.run(main())