from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pandas as pd
import numpy as np
import argparse
import os
from collections import Counter
from playwright.sync_api import sync_playwright
import time
import math
import streamlit as st
import altair as alt


def get_search_url(keyword):
    keyword = keyword.replace(" ", '+')
    return f"https://m.timesjobs.com/mobile/jobs-search-result.html?txtKeywords={keyword}&cboWorkExp1=-1&txtLocation="


def scroll_batch(page, scroll_increment=500, timeout=10):
    """Scroll incrementally until a new batch of jobs is loaded."""
    old_job_count = len(page.locator("#jobsListULid li").all())
    start_time = time.time()

    while True:
        page.evaluate(f"window.scrollBy(0, {scroll_increment})")
        time.sleep(0.5)

        new_job_count = len(page.locator("#jobsListULid li").all())
        if new_job_count > old_job_count:
            # New jobs loaded
            break
        if time.time() - start_time > timeout:
            # Avoid infinite loop if nothing loads
            break


def fetch_job_page(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'lxml')


def parse_job_details(job_url):
    # Parse the page of a job and extract the useful details
    soup = fetch_job_page(job_url)
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


def find_jobs(keyword, limit):
    base_url = get_search_url(keyword=keyword)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(base_url)

        # Scroll n times to load n batches
        # The website loads 25 jobs when we scroll to the end of the page
        batches_to_load = math.floor(limit / 25)
        for _ in range(batches_to_load):
            scroll_batch(page, scroll_increment=500, timeout=10)
            time.sleep(1)  # wait a little for content to stabilize

        jobs_raw = page.locator(
            "#jobsListULid li .srp-listing.clearfix a.srp-apply-new.ui-link")
        job_links = []
        for i in range(limit):
            job_links.append(jobs_raw.nth(i).get_attribute('href'))

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

        browser.close()

    if jobs:
        df = pd.DataFrame(jobs)
        csv_file = f"jobs_{datetime.today().strftime('%Y-%m-%d')}_{keyword}.csv"
        df.to_csv(csv_file, index=False)
        print(f"\nSaved {len(jobs)} jobs to {csv_file}")
        return df
    else:
        print("No jobs found.")
        return None

def launch_streamlit(keyword, df):
    st.title(f'{keyword.capitalize()} listings')
    st.dataframe(df)

    top_cities = (
        df['Location']
        .value_counts()
        .reset_index()  # reset_index() converts the index into a column and makes the counts another column
        .sort_values(by='count', ascending=False)
        .head(10)
    )
    st.subheader('_Locations with the most job listings_')
    top_cities = top_cities.rename(columns={'count': 'Number of jobs'})
    chart = alt.Chart(top_cities).mark_bar().encode(
        x='Number of jobs:Q',  # Q -> Quantitative, N -> Nominal
        y=alt.Y('Location:N', sort='-x'),
        # categories on y-axis, sorted by count
        color=alt.Color('Number of jobs:Q',
                        scale=alt.Scale(scheme='bluepurple'))
    ).properties(height=500)
    st.altair_chart(chart, use_container_width=True)
    st.markdown('##### The cities with the most job listings are: ' +
                ', '.join(top_cities['Location'].head(3).tolist()))
    st.divider()

    st.subheader('_Top companies_')
    top_companies = (
        df['Company']
        .value_counts()
        .reset_index()  
        .sort_values(by='count', ascending=False)
        .head(10)
    )
    top_companies = top_companies.rename(columns={'count': 'Number of jobs'})
    chart2 = alt.Chart(top_companies).mark_bar().encode(
        x='Number of jobs:Q',
        y=alt.Y('Company:N', sort='-x'),
        color=alt.Color('Number of jobs:Q', scale=alt.Scale(scheme='greens'))
    ).properties(height=500)
    st.altair_chart(chart2, use_container_width=True)
    st.markdown('##### The companies with the most job listings are: ' +
                ', '.join(top_companies['Company'].head(3).tolist()))
    st.divider()

    st.subheader('_Top Skills_')
    all_skills = df['Skills'].dropna().str.split(', ')  # dropna() ignores empty cells
    # Some skills are duplicated for the same job so we'll remove them using sets
    flattened_skills = []
    for sublist in all_skills:
        clean_skills = {skill.strip().lower() for skill in sublist}
        flattened_skills.extend(clean_skills)

    skill_counts = Counter(flattened_skills)
    df_skills = pd.DataFrame(skill_counts.items(), columns=[
                             'Skill', 'Number of jobs'])
    top_skills = (df_skills
                  .sort_values(by='Number of jobs', ascending=False)
                  .head(10))
    chart3 = alt.Chart(top_skills).mark_bar().encode(
        x='Number of jobs:Q',
        y=alt.Y('Skill:N', sort='-x'),
        color=alt.Color('Number of jobs:Q', scale=alt.Scale(scheme='cividis'))).properties(height=500)

    st.altair_chart(chart3, use_container_width=True)
    st.markdown('##### The most important skills are: ' +
                ', '.join(top_skills['Skill'].head(3).tolist()))
    st.divider()


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
        launch_streamlit(args.keyword, jobs_df)
