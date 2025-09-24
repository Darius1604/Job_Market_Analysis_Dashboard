from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright
import time
import math
import sys
from pathlib import Path
import random
import asyncio
import httpx
import logging

def build_search_url(keyword):
    keyword = keyword.replace(" ", '+')
    return f"https://m.timesjobs.com/mobile/jobs-search-result.html?txtKeywords={keyword}&cboWorkExp1=-1&txtLocation="

def load_next_batch(page, scroll_increment=500, timeout=30):
    """Scroll incrementally until a new batch of jobs is loaded."""
    old_job_count = len(page.locator("#jobsListULid li").all())
    start_time = time.time()

    while True:
        page.evaluate(f"window.scrollBy(0, {scroll_increment})")
        time.sleep(random.uniform(0.1, 0.3))

        new_job_count = len(page.locator("#jobsListULid li").all())
        if new_job_count > old_job_count:
            # New jobs loaded
            break
        if time.time() - start_time > timeout:
            # Avoid infinite loop if nothing loads
            break


def fetch_job_html(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'lxml')


logging.basicConfig(
    filename="job_scraper.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

MAX_RETRIES = 3  # how many times to retry a failed URL
RETRY_DELAY = (1, 3)  # random delay between retries in seconds

async def fetch_job_async(client, url):
    try:
        r = await client.get(url, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'lxml')

        outer_container = soup.find('div', class_=[
            'jd-page', 'ui-page', 'ui-page-theme-a',
            'ui-page-header-fixed', 'ui-page-footer-fixed', 'ui-page-active'
        ])
        if not outer_container:
            raise ValueError("Outer container not found")

        inner_container = outer_container.find('div', class_='jdpage-main')
        job_information = inner_container.find('div', id='jobTitle')
        job_title = job_information.h1.text.strip()
        company_name = job_information.h2.span.text.strip()
        posting_time = job_information.find('span', class_='posting-time').text.strip()
        posting_time_date = datetime.strptime(posting_time, '%d %b, %Y').date()

        location_exp_infos = inner_container.find('div', class_='clearfix exp-loc')
        location_text = location_exp_infos.find('div', class_='srp-loc jd-loc').text.strip()
        location_list = location_text.split()
        location = location_list[1].translate(str.maketrans('', '', '()/,'))
        years_of_experience = location_exp_infos.find('div', class_='srp-exp').text.split()
        years_of_experience = f"{years_of_experience[0]} {years_of_experience[1]}"

        key_skill_links = inner_container.find('div', id='JobDetails').find('div', id='KeySkills').find_all('a')
        key_skills = ', '.join([a.text.lower() for a in key_skill_links])

        return {
            'Title': job_title,
            'Company': company_name,
            'Posted on': str(posting_time_date),
            'Location': location,
            'Experience': years_of_experience,
            'Skills': key_skills
        }

    except Exception as e:
        logging.warning(f"Failed fetching {url}: {e}")
        return None


async def fetch_all_jobs(job_links):
    jobs = []
    failed_urls = job_links.copy()
    limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
    async with httpx.AsyncClient(limits=limits, timeout=30) as client:

        for attempt in range(1, MAX_RETRIES + 1):
            if not failed_urls:
                break
            logging.info(f"Attempt {attempt} for {len(failed_urls)} URLs")
            current_failed = []
            tasks = [fetch_job_async(client, url) for url in failed_urls]
            for url, future in zip(failed_urls, await asyncio.gather(*tasks)):
                if future:
                    jobs.append(future)
                else:
                    current_failed.append(url)
            failed_urls = current_failed
            if failed_urls:
                logging.info(f"{len(failed_urls)} URLs failed, retrying...")
                await asyncio.sleep(random.uniform(*RETRY_DELAY))  # small delay before next retry

    logging.info(f"Finished fetching jobs. Total successful: {len(jobs)}, failed: {len(failed_urls)}")
    if failed_urls:
        logging.info("Failed URLs:")
        for f in failed_urls:
            logging.info(f)

    return jobs



JOBS_PER_SCROLL = 25


def scrape_jobs(keyword, limit):
    base_url = build_search_url(keyword=keyword)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(base_url)

        # Scroll n times to load n batches
        # The website loads 25 jobs when we scroll to the end of the page
        batches_to_load = math.floor(limit / JOBS_PER_SCROLL)
        for _ in range(batches_to_load):
            load_next_batch(page, scroll_increment=500, timeout=10)
            time.sleep(random.uniform(0.1,0.3)) # wait a little for content to stabilize

        jobs_raw = page.locator(
            "#jobsListULid li .srp-listing.clearfix a.srp-apply-new.ui-link")
        job_links = []
        for i in range(limit):
            job_links.append(jobs_raw.nth(i).get_attribute('href'))
        print('Saved ',len(job_links),' links')
        browser.close()
    jobs = asyncio.run(fetch_all_jobs(job_links))
    if jobs:
        df = pd.DataFrame(jobs)
        df_sorted = df.sort_values(by='Posted on', ascending=False)
        df_sorted = df_sorted.reset_index(drop=True)
        df_sorted.index = df_sorted.index + 1
        Path("csv_files").mkdir(parents=True, exist_ok=True)

        csv_file = f"csv_files/jobs_{datetime.today().strftime('%Y-%m-%d')}_{keyword}_{limit}.csv"
        df_sorted.to_csv(csv_file, index=False)
        print(f"\nSaved {len(jobs)} jobs to {csv_file}")
        return 0
    else:
        print("No jobs found.")
        return 1


if __name__ == "__main__":
    keyword = sys.argv[1]
    limit = int(sys.argv[2])

    result_code = scrape_jobs(keyword, limit)
   
    