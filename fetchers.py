from settings import MAX_RETRIES
from settings import RETRY_DELAY
from bs4 import BeautifulSoup
import requests
from datetime import datetime,date
import logging
import httpx
import asyncio
import random
def fetch_job_html(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'lxml')

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
            'Posted on': posting_time_date,
            'Location': location,
            'Experience': years_of_experience,
            'Skills': key_skills,
            'Url' : url,
            'Scrape_date' : date.today()
        }

    except Exception as e:
        logging.warning(f"Failed fetching {url}: {e}")
        return None

async def fetch_all_jobs(job_links):
    jobs = []
    failed_urls = job_links.copy()
    limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
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