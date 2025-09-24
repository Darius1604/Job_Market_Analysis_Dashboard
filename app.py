from datetime import datetime
from datetime import date
import pandas as pd
import os
from collections import Counter
import streamlit as st
import altair as alt
import subprocess
import sys
import json


def update_search_log(keyword, just_scraped):
    filename = 'search_log.json'
    today = date.today().strftime('%d-%m-%Y')

    # Load existing log
    try:
        with open(filename, 'r') as f:
            log = json.load(f)
    except FileNotFoundError:
        log = {}

    # Update today's search
    if today not in log:
        log[today] = {}
    if keyword not in log[today]:
        log[today][keyword] = {'scraped': just_scraped}
    else:
        if log[today][keyword]['scraped'] < just_scraped:
            log[today][keyword] = {
                'scraped': just_scraped
            }

    # Save back to file
    with open(filename, 'w') as f:
        json.dump(log, f, indent=4)


def make_bar_chart(df, x, y, color_scheme, title):
    return (
        alt.Chart(df).mark_bar().encode(
            x=f"{x}:Q",
            y=alt.Y(f"{y}:N", sort='-x'),
            color=alt.Color(f"{x}:Q", scale=alt.Scale(scheme=color_scheme)),
            tooltip=[y, x]
        )
        .properties(title=title, height=500)
        .configure_title(
            fontSize=25
        )
    )


def render_dashboard(keyword, df):
    st.title(f'{keyword.capitalize()} listings')
    df.index = df.index + 1
    st.dataframe(df)

    top_cities = (
        df['Location']
        .value_counts()
        .reset_index()  # reset_index() converts the index into a column and makes the counts another column
        .sort_values(by='count', ascending=False)
        .head(10)
    )
    top_cities = top_cities.rename(columns={'count': 'Number of jobs'})
    st.altair_chart(make_bar_chart(top_cities, "Number of jobs",
                    "Location", "bluepurple", "Top cities"))

    top_3_cities = top_cities['Location'].head(3).tolist()
    st.markdown("##### The cities with the most job listings are:")
    for city in top_3_cities:
        st.markdown(f"- {city}")
    st.divider()

    top_companies = (
        df['Company']
        .value_counts()
        .reset_index()
        .sort_values(by='count', ascending=False)
        .head(10)
    )
    top_companies = top_companies.rename(columns={'count': 'Number of jobs'})
    st.altair_chart(make_bar_chart(top_companies, x='Number of jobs',
                    y='Company', color_scheme='greens', title='Top companies'))

    top_3_companies = top_companies['Company'].head(3).tolist()
    st.markdown("##### The companies with the most job listings are:")
    for company in top_3_companies:
        st.markdown(f"- {company}")

    st.divider()

    all_skills = df['Skills'].dropna().str.split(', ')
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
    st.altair_chart(make_bar_chart(top_skills, x='Number of jobs',
                    y='Skill', color_scheme='cividis', title='Top skills'))

    st.markdown('#### The most important skills are: ')
    top_3_skills = top_skills['Skill'].head(3).tolist()
    for skill in top_3_skills:
        st.markdown(f"- {skill.capitalize()}")

def run_scraper_and_dashboard(keyword, limit):
    today = date.today().strftime('%d-%m-%Y')
    filename = 'search_log.json'
    
    # Load log
    try:
        with open(filename, 'r') as f:
            log = json.load(f)
    except FileNotFoundError:
        log = {}
    
    if today not in log:
        log[today] = {}

    jobs_df = None
    
    # Case 1: need to scrape
    if keyword not in log[today] or limit > log[today][keyword]['scraped']:
        with st.spinner("Scraping jobs, please wait..."):
            result = subprocess.run(
                [sys.executable, "scraper.py", keyword, str(limit)],
                text=True,
                capture_output=True
            )
            if not result.returncode:
                st.success('Jobs have been successfully written to the CSV file')
                # Remove old file if exists
                if keyword in log[today]:
                    previously_scraped = log[today][keyword]['scraped']
                    prev_file = f'csv_files/jobs_{datetime.today().strftime("%Y-%m-%d")}_{keyword}_{previously_scraped}.csv'
                    if os.path.exists(prev_file):
                        os.remove(prev_file)
                update_search_log(keyword, limit)
                jobs_df = pd.read_csv(
                    f'csv_files/jobs_{datetime.today().strftime("%Y-%m-%d")}_{keyword}_{limit}.csv'
                )
            else:
                st.error('No jobs found')
    
    # Case 2: already scraped enough
    else:
        max_scraped = log[today][keyword]['scraped']
        jobs_df = pd.read_csv(
            f'csv_files/jobs_{datetime.today().strftime("%Y-%m-%d")}_{keyword}_{max_scraped}.csv',
            nrows=limit
        )

    # Render dashboard if data exists
    if jobs_df is not None:
        st.success('Data visualization is ready')
        render_dashboard(keyword, jobs_df)


if __name__ == '__main__':
    keyword = st.text_input("Job keyword", "Python Developer")
    limit = st.number_input("Number of jobs", min_value=1,
                            max_value=10000, value=20, step=10)
    if st.button('Scrape new jobs'):
        run_scraper_and_dashboard(keyword,limit)