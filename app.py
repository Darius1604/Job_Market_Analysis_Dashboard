from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pandas as pd
import numpy as np
import os
from collections import Counter
from playwright.sync_api import sync_playwright
import time
import math
import streamlit as st
import altair as alt
import subprocess
import sys


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
    col1, col2, col3 = st.columns(3)
    for col, skill in zip([col1, col2, col3], top_3_skills):
        col.metric(value=skill.capitalize())


if __name__ == '__main__':
    keyword = st.text_input("Job keyword", "Python Developer")
    limit = st.number_input("Number of jobs", min_value=1,
                            max_value=100, value=20, step=10)
    found_new_jobs = False
    if st.button('Scrape new jobs'):
        if not os.path.exists(f'csv_files/jobs_{datetime.today().strftime('%Y-%m-%d')}_{keyword}_{limit}.csv'):
            with st.spinner("Scraping jobs, please wait..."):
                result = subprocess.run(
                    [sys.executable, "scraper.py", keyword, str(limit)],
                    text=True,
                    capture_output=True
                )
                if 'Found job' in result.stdout:
                    found_new_jobs = True
                    st.success('Jobs have been found and written to the CSV file')
                else:
                    st.error('No jobs found.')
        if not found_new_jobs:
            st.success('Jobs have been found and written to the CSV file')
        jobs_df = pd.read_csv(
            f'csv_files/jobs_{datetime.today().strftime('%Y-%m-%d')}_{keyword}_{limit}.csv')
        if jobs_df is not None:
            render_dashboard(keyword, jobs_df)
