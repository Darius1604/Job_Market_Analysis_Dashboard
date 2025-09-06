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
import subprocess
import sys


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

    top_3_cities = top_cities['Location'].head(3).tolist()

    st.markdown("##### The cities with the most job listings are:")
    for city in top_3_cities:
        st.markdown(f"- {city}")
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
    top_3_companies = top_companies['Company'].head(3).tolist()

    st.markdown("##### The companies with the most job listings are:")
    for company in top_3_companies:
        st.markdown(f"- {company}")

    st.divider()

    st.subheader('_Top Skills_')
    all_skills = df['Skills'].dropna().str.split(
        ', ')  # dropna() ignores empty cells
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
    st.markdown('#### The most important skills are: ')

    top_3_skills = top_skills['Skill'].head(3).tolist()
    for skill in top_3_skills:
        st.markdown(f"- {skill}")
    st.divider()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()  # Create the parser instance

    # Add a Command - Line - Interface argument to pass( --keyword django)
    # help = '...' shows up when we run python script.py --help
    parser.add_argument('--keyword', type=str,
                        default='python', help='Job keyword to search')
    parser.add_argument('--limit', type=int, default=25,
                        help='Number of job listings to fetch')
    parser.add_argument('--scrape', type=bool, default=True,
                        help='Scrape new jobs from timesjobs if scrape is True or use the ones already scraped if scrape is False')
    args = parser.parse_args()

    keyword = st.text_input("Job keyword", "Python Developer")
    limit = st.number_input("Number of jobs", min_value=1,
                            max_value=100, value=20, step=10)
    scrape_enable = st.checkbox('Find new jobs')
    if st.button('Scrape new jobs'):
        if scrape_enable == True or not os.path.exists(f'jobs_{datetime.today().strftime('%Y-%m-%d')}_{keyword}.csv'):
            with st.spinner("Scraping jobs, please wait..."):
                result = subprocess.run(
                    [sys.executable, "scrape_jobs.py", keyword, str(limit)],
                    text=True
                )
                st.success('Done!')
        jobs_df = pd.read_csv(f'jobs_{datetime.today().strftime('%Y-%m-%d')}_{keyword}.csv')
        if jobs_df is not None:
            launch_streamlit(keyword, jobs_df)
