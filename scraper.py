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


async def fetch_job_async(client, url):
    try:
        r = await client.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'lxml')
        outer_container = soup.find('div', class_=['jd-page', 'ui-page', 'ui-page-theme-a',
                                                   'ui-page-header-fixed', 'ui-page-footer-fixed', 'ui-page-active'])
        if not outer_container:
            return None

        inner_container = outer_container.find('div', class_='jdpage-main')

        # Job info: title, company and the positing date
        job_information = inner_container.find('div', id='jobTitle')
        job_title = job_information.h1.text.strip()
        company_name = job_information.h2.span.text.strip()
        posting_time = job_information.find(
            'span', class_='posting-time').text.strip()
        posting_time_date = datetime.strptime(posting_time, '%d %b, %Y').date()

        # Location and experience
        location_exp_infos = inner_container.find(
            'div', class_='clearfix exp-loc')
        location_text = location_exp_infos.find(
            'div', class_='srp-loc jd-loc').text.strip()
        location_list = location_text.split()
        location = location_list[1].translate(str.maketrans('', '', '()/,'))
        years_of_experience = location_exp_infos.find(
            'div', class_='srp-exp').text.split()
        years_of_experience = years_of_experience[0] + \
            ' ' + years_of_experience[1]

    # Key Skills
        key_skill_links = inner_container.find('div', id='JobDetails').find(
            'div', id='KeySkills').find_all('a')
        key_skills = [key_skill_link.text.lower()
                      for key_skill_link in key_skill_links]
        key_skills = ', '.join(key_skills)
        return {
            'Title': job_title,
            'Company': company_name,
            'Posted on': str(posting_time_date),
            'Location': location,
            'Experience': years_of_experience,
            'Skills': key_skills
        }
    except Exception as e:
        print(f"Failed fetching {url}: {e}")
        return None


async def fetch_all_jobs(job_links):
    jobs = []
    tasks = []
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
    async with httpx.AsyncClient(limits=limits,timeout=30) as client:
        tasks = [fetch_job_async(client, url) for url in job_links]
        for future in asyncio.as_completed(tasks):
            result = await future
            if result:
                jobs.append(result)
       
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
    # keyword = sys.argv[1]
    # limit = int(sys.argv[2])

    result_code = scrape_jobs(keyword, limit)
    print('GATA SEF')
