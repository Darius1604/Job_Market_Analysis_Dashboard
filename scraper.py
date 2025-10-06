from settings import BATCH_SIZE
from browser import get_job_links, fetch_all_jobs
from utils import show_timer
from csv_handler import save_jobs_csv
from playwright.sync_api import sync_playwright
import time
import math
from pathlib import Path
import random
import asyncio
import threading
import sys

def scrape_jobs(keyword='Python', limit=1000):

    job_links = get_job_links(keyword,limit)
    jobs = []
    for i in range(0,len(job_links), BATCH_SIZE):
        batch= job_links[i:i+BATCH_SIZE]
        print(f"Batch {math.ceil(i/BATCH_SIZE)} has {len(batch)} jobs")
        if i != 0:
            wait_time = random.uniform(120, 180)
            print(f"Waiting for {wait_time:.0f} seconds before continuing... (scraper is idle, not blocked)")
            time.sleep(wait_time)
        print(f"Started to fetch the jobs from batch number {math.ceil(i/BATCH_SIZE) + 1}")
        stop_event = threading.Event()
        timer_thread = threading.Thread(target=show_timer,args=(stop_event,)) # comma makes it a tuple
        timer_thread.start()
        jobs.extend(asyncio.run(fetch_all_jobs(batch)))
        stop_event.set()
        timer_thread.join()
        
    save_jobs_csv(jobs,keyword,limit)
    return jobs
        
def main():
    keyword = sys.argv[1]
    limit = int(sys.argv[2])
    scrape_jobs(keyword,limit)

if __name__ == "__main__":
    main()
   
    