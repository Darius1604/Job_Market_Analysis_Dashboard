import time
import logging
def show_timer(stop_event):
    start_time = time.time()
    while not stop_event.is_set():
        elapsed = int(time.time() - start_time)
        print(f"\rTime elapsed: {elapsed} seconds", end="")
        time.sleep(1)
    print("\nDone fetching batch!")
    
logging.basicConfig(
    filename="job_scraper.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)