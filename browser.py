from settings import JOBS_PER_SCROLL
from settings import BATCH_SIZE
from utils import show_timer
from fetchers import fetch_all_jobs
import time
import random
from playwright.sync_api import sync_playwright
import math

def build_search_url(keyword):
    keyword = keyword.replace(" ", '+')
    return f"https://m.timesjobs.com/mobile/jobs-search-result.html?txtKeywords={keyword}&cboWorkExp1=-1&txtLocation="

def load_next_batch(page, scroll_increment=500, timeout=30):
    """Scroll incrementally until a new batch of jobs is loaded."""
    old_job_count = len(page.locator("#jobsListULid li").all())
    start_time = time.time()
    
    while True:
        page.evaluate(f"window.scrollBy(0, {scroll_increment})")
        time.sleep(random.uniform(0.1,0.3))
        
        new_job_count = len(page.locator('#jobsListULid li').all())
        if new_job_count > old_job_count:
            # New jobs loaded
            break
        if time.time() - start_time > timeout:
            # Avoid infinite loop if nothing loads
            break
def get_job_links(keyword, limit):
    base_url = build_search_url(keyword=keyword)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(base_url)

        # Scroll n times to load n batches
        # The website loads 25 jobs when we scroll to the end of the page
        batches_to_load = math.floor(limit / JOBS_PER_SCROLL)
        for _ in range(batches_to_load):
            load_next_batch(page, scroll_increment=500, timeout=30)
            time.sleep(random.uniform(0.1,0.3)) # wait a little for content to stabilize

        jobs_raw = page.locator(
            "#jobsListULid li .srp-listing.clearfix a.srp-apply-new.ui-link")
        job_links = []
        for i in range(limit):
            job_links.append(jobs_raw.nth(i).get_attribute('href'))
        print('Saved ',len(job_links),' links')
        browser.close()
        return job_links

