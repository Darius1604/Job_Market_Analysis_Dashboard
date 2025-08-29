from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pandas as pd
import numpy as np
import argparse
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.cm as cm  # matplotlib colormap
import matplotlib.gridspec as gridspec
from collections import Counter


def get_search_url(keyword):
    keyword = keyword.replace(" ", '+')
    return f"https://m.timesjobs.com/mobile/jobs-search-result.html?txtKeywords={keyword}&cboWorkExp1=-1&txtLocation="


def fetch_page(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'lxml')


def parse_job_links(soup, limit=25):
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
    location = location_list[1].translate(str.maketrans('', '', '()/,'))
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


def find_jobs(keyword, limit=25):
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
        return df
    else:
        print("No jobs found.")
        return None


def plot_data(df):
    if jobs_df is not None:
        # Creates both the figure and the axes
        fig = plt.figure(figsize=(18,10))
        gs = gridspec.GridSpec(3,1,height_ratios=[1,1,2]) # ax3 is 2x taller
        
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        ax3 = fig.add_subplot(gs[2])
        ax1.set_title("Jobs per location")
        ax2.set_title("Most popular required skills")
        ax3.set_title("Jobs per company")
        job_locations = df['Location'].value_counts()
        
        cmap = plt.get_cmap('tab20')  # pallete with max distinct colors
        colors = cmap(np.linspace(0, 1, len(job_locations.values)))

        ax1.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax1.bar(job_locations.index, job_locations.values, color=colors)

        ax1.set_ylabel(f'{args.keyword.capitalize()} jobs')
        ax1.set_title(f'{args.keyword.capitalize()} jobs by location and number')
        
        
        all_skills = df['Skills'].dropna().str.split(', ') # dropna() ignores empty cells
        
        # Some skills are duplicated for the same job so we'll remove them using sets
        
        flattened_skills = []
        
        for sublist in all_skills:
            clean_skills = {skill.strip().lower() for skill in sublist}
            flattened_skills.extend(clean_skills)
        
        
        skill_counts = Counter(flattened_skills)
        skill_series = pd.Series(skill_counts).sort_values(ascending=False)
        
        cmap = plt.get_cmap('winter')
        colors = cmap(np.linspace(0,1,len(skill_series.head(10))))
        
        
        
        ax2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax2.bar(skill_series.index[:10], skill_series.values[:10],color=colors)
        
        ax2.set_ylabel('Number of jobs')
        ax2.set_title('Skills')
        
       
        company_names = df['Company'].value_counts()
        # Series where index -> location names
        #              Values -> number of jobs in each location
        cmap = plt.get_cmap('gnuplot2')  # pallete with max distinct colors
        colors = cmap(np.linspace(0, 1, len(company_names.values)))
        
        

        ax3.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax3.barh(company_names.index[:10], company_names.values[:10], color=colors)
        

        ax3.set_ylabel(f'Companies')
        ax3.set_title(f'Jobs per company')
        ax3.set_yticks(range(len(company_names.index[:10])))
        ax3.set_yticklabels(company_names.index[:10])
        
        
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()  # Create the parser instance

    # Add a Command - Line - Interface argument to pass( --keyword django)
    # help = '...' shows up when we run python script.py --help
    parser.add_argument('--keyword', type=str,
                        default='python', help='Job keyword to search')
    parser.add_argument('--limit', type=int, default=25,
                        help='Number of job listings to fetch')
    parser.add_argument('--scrape', type=bool, default=False,
                        help='Scrape new jobs from timesjobs if scrape is True or use the ones already scraped if scrape is False')
    args = parser.parse_args()
    if args.scrape == True or not os.path.exists(f'jobs_{datetime.today().strftime('%Y-%m-%d')}_{args.keyword}.csv'):
        jobs_df = find_jobs(args.keyword, args.limit)
    else:
        jobs_df = pd.read_csv(
            f'jobs_{datetime.today().strftime('%Y-%m-%d')}_{args.keyword}.csv')
    if jobs_df is not None:
        plot_data(df=jobs_df)
