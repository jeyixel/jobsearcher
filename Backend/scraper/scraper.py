import asyncio
import json
import hashlib
import re
from urllib.parse import urljoin
from playwright.async_api import async_playwright

# Helper to generate ID
def generate_id(link):
    # We hash the link so the ID is always the same for the same job.
    # This prevents duplicates if you run the scraper multiple times.
    return hashlib.md5(link.encode('utf-8')).hexdigest()

async def scrape_jobhub():
    print("--- Starting JobHub Scraper ---")
    extracted_data = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) 
        page = await browser.new_page()

        target_url = "https://jobhub.lk/en/Sri%20Lanka/search?q=software%20intern&type=Internship&sort-by=Relevance"
        print(f"[JobHub] Navigating to: {target_url}")
        await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")

        try:
            print("[JobHub] Waiting for content...")
            # Using a generic wait to ensure content loads
            await page.wait_for_selector(".listings-container", timeout=10000)
            
            job_cards = await page.query_selector_all(".job-listing")
            print(f"[JobHub] Found {len(job_cards)} cards.")

            for card in job_cards:
                try:
                    # A. Title
                    title_el = await card.query_selector(".job-listing-title")
                    title = await title_el.inner_text() if title_el else "N/A"

                    # B. Company
                    comp_el = await card.query_selector(".job-listing-company")
                    company = await comp_el.inner_text() if comp_el else "N/A"

                    # C. Date
                    date_el = await card.query_selector(".job-listing-footer li:has(.icon-material-outline-access-time)")
                    date = await date_el.inner_text() if date_el else "N/A"

                    # D. Link
                    raw_link = await card.get_attribute("href")
                    if raw_link and raw_link.startswith("/"):
                        link = f"https://jobhub.lk{raw_link}"
                    else:
                        link = raw_link or "N/A"

                    # E. ID (New)
                    job_id = generate_id(link)

                    extracted_data.append({
                        "id": job_id,
                        "site": "JobHub",
                        "job_title": title.strip(),
                        "company": company.strip(),
                        "date": date.strip(),
                        "link": link
                    })
                except Exception as e:
                    print(f"[JobHub] Error parsing a card: {e}")

        except Exception as e:
            print(f"[JobHub] Global error: {e}")

        await browser.close()
        print(f"--- JobHub Finished ({len(extracted_data)} jobs) ---")
        return extracted_data


async def scrape_Devjobs():
    print("--- Starting devjobs.lk Scraper ---")
    extracted_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        target_url = "https://devjobs.lk/intern-jobs"
        print(f"[Devjobs] Navigating to: {target_url}")
        await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")

        try:
            print("[Devjobs] Waiting for content...")
            # We wait for the LINK element now, not the card body
            await page.wait_for_selector("a.card-link", timeout=10000)

            # --- KEY CHANGE HERE ---
            # We select the Anchor tag (<a>) directly. 
            # This contains the 'href' we need.
            job_cards = await page.query_selector_all("a.card-link")
            print(f"[Devjobs] Found {len(job_cards)} cards.")

            for card in job_cards:
                try:
                    # 1. GET THE LINK (Directly from the main card element)
                    raw_link = await card.get_attribute("href")
                    if raw_link:
                        link = raw_link.strip()
                        # print(f"[Devjobs DEBUG] Found Link: {link}") # <--- DEBUG PRINT
                    else:
                        link = "N/A"
                        print("[Devjobs DEBUG] Link was N/A!")

                    # 2. Get Title (Search inside the card)
                    title_el = await card.query_selector(".card-title")
                    title = await title_el.inner_text() if title_el else "N/A"

                    # 3. Get Company
                    company_el = await card.query_selector(".card-text.mb-0")
                    company = await company_el.inner_text() if company_el else "N/A"

                    # 4. Get Date
                    date_el = await card.query_selector(".text-muted")
                    date = await date_el.inner_text() if date_el else "N/A"

                    job_id = generate_id(link)

                    extracted_data.append({
                        "id": job_id,
                        "site": "Devjobs.lk",
                        "job_title": title.strip(),
                        "company": company.strip(),
                        "date": date.strip(),
                        "link": link
                    })
                except Exception as e:
                    print(f"[Devjobs] Error parsing a card: {e}")

        except Exception as e:
            print(f"[Devjobs] Global error: {e}")

        await browser.close()
        print(f"--- Devjobs Finished ({len(extracted_data)} jobs) ---")
        return extracted_data


async def scrape_itpro():
    print("--- Starting ITPro Scraper ---")
    extracted_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        target_url = "https://itpro.lk/jobs/internship/"
        print(f"[ITPro] Navigating to: {target_url}")
        await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")

        try:
            print("[ITPro] Waiting for content...")
            await page.wait_for_selector("article", timeout=10000)

            job_cards = await page.query_selector_all("article")
            print(f"[ITPro] Found {len(job_cards)} cards.")

            for card in job_cards:
                try:
                    title_el = await card.query_selector(".job-title")
                    title = await title_el.inner_text() if title_el else "N/A"

                    company_el = await card.query_selector(".jc-company")
                    company = await company_el.inner_text() if company_el else "N/A"

                    date_el = await card.query_selector(".time-posted")
                    date = await date_el.inner_text() if date_el else "N/A"

                    link_el = await card.query_selector(".job-record-link") 
                    raw_link = await link_el.get_attribute("href") if link_el else "N/A"
                    
                    if raw_link and raw_link.startswith("/"):
                        link = f"https://itpro.lk{raw_link}"
                    else:
                        link = raw_link

                    # E. ID (New)
                    job_id = generate_id(link)

                    extracted_data.append({
                        "id": job_id,
                        "site": "ITPro.lk",
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
    print("Running scrapers concurrently...")
    
    results = await asyncio.gather(
        scrape_jobhub(),
        scrape_itpro(),
        scrape_Devjobs()
    )
    
    # Flatten the list
    all_jobs = results[0] + results[1] + results[2]
    
    save_locally(all_jobs)

if __name__ == "__main__":
    asyncio.run(main())