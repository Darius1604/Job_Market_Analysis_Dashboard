from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pandas as pd
import argparse


def get_search_url(keyword):
    keyword = keyword.replace(" ", '+')
    return f"https://m.timesjobs.com/mobile/jobs-search-result.html?txtKeywords={keyword}&cboWorkExp1=-1&txtLocation="


def fetch_page(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'lxml')


def parse_job_links(soup, limit=5):
    # Extract the links to the job pages from the main page
    listings = soup.find_all('div', class_='srp-listing', limit=limit)
    if limit == -1:
        listings = soup.find_all('div', class_='srp-listing')
    else:
        listings = soup.find_all('div', class_='srp-listing', limit=limit)
    links = [listing.find('a').get('href') for listing in listings]
    return links


def parse_job_details(job_url):
    # Parse the page of a job and extract the useful details
    soup = fetch_page(job_url)
    outer_infos = soup.find('div', class_=['jd-page', 'ui-page', 'ui-page-theme-a',
                                           'ui-page-header-fixed', 'ui-page-footer-fixed', 'ui-page-active'])
    if not outer_infos:
        return None

    inner_infos = outer_infos.find('div', class_='jdpage-main')

    # Job info: title, company and the positing date
    job_information = inner_infos.find('div', id='jobTitle')
    job_title = job_information.h1.text.strip()
    company_name = job_information.h2.span.text.strip()
    posting_time = job_information.find(
        'span', class_='posting-time').text.strip()
    posting_time_date = datetime.strptime(posting_time, '%d %b, %Y').date()

    # Location and experience
    location_exp_infos = inner_infos.find('div', class_='clearfix exp-loc')
    location_text = location_exp_infos.find(
        'div', class_='srp-loc jd-loc').text.strip()
    location_list = location_text.split()
    location = location_list[1].translate(str.maketrans(
        '', '', '()/,')) + ' - ' + location_list[2].translate(str.maketrans('', '', '()/,'))
    years_of_experience = location_exp_infos.find(
        'div', class_='srp-exp').text.split()
    years_of_experience = years_of_experience[0] + ' ' + years_of_experience[1]

    # Key Skills
    key_skill_links = inner_infos.find('div', id='JobDetails').find(
        'div', id='KeySkills').find_all('a')
    key_skills = [key_skill_link.text for key_skill_link in key_skill_links]
    key_skills = ', '.join(key_skills)
    return {
        'Title': job_title,
        'Company': company_name,
        'Posted on': str(posting_time_date),
        'Location': location,
        'Experience': years_of_experience,
        'Skills': key_skills
    }


def find_jobs(keyword, limit):
    base_url = get_search_url(keyword=keyword)
    soup = fetch_page(base_url)
    job_links = parse_job_links(soup, limit)

    jobs = []
    for link in job_links:
        try:
            job = parse_job_details(link)
            if job:
                print(
                    f"Found job: {job['Title']} at {job['Company']} posted on {job['Posted on']}")
                jobs.append(job)
        except Exception as e:
            print(f"Failed to parse job at {link}: {e}")

    if jobs:
        df = pd.DataFrame(jobs)
        csv_file = f"jobs_{datetime.today().strftime('%Y-%m-%d')}_{keyword}.csv"
        df.to_csv(csv_file, index=False)
        print(f"\nSaved {len(jobs)} jobs to {csv_file}")
    else:
        print("No jobs found.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()  # Create the parser instance

    # Add a Command - Line - Interface argument to pass( --keyword django)
    # help = '...' shows up when we run python script.py --help
    parser.add_argument('--keyword', type=str,
                        default='python', help='Job keyword to search')
    parser.add_argument('--limit', type=int, default=5,
                        help='Number of job listings to fetch')

    # Parse the arguments into a Namespace object
    args = parser.parse_args()
    find_jobs(args.keyword, args.limit)


# Use pandas to analyse the data
