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
    st.title(f'{keyword} Listings')
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Jobs Scraped", len(df))
    with col2:
        st.metric("Unique Companies",df['Company'].nunique())
    df.index = df.index + 1
    st.dataframe(df)
    
    tab1,tab2,tab3 = st.tabs(["Cities","Companies","Skills"])
    

    top_cities = (
        df['Location']
        .value_counts()
        .reset_index()  # reset_index() converts the index into a column and makes the counts another column
        .sort_values(by='count', ascending=False)
        .head(10)
    )
    top_cities = top_cities.rename(columns={'count': 'Number of jobs'})
    with tab1:
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
    with tab2:
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
        clean_skills = {skill.strip().lower().strip("'\"") for skill in sublist}
        flattened_skills.extend(clean_skills)

    skill_counts = Counter(flattened_skills)
    df_skills = pd.DataFrame(skill_counts.items(), columns=[
                             'Skill', 'Number of jobs'])
    top_skills = (df_skills
                  .sort_values(by='Number of jobs', ascending=False)
                  .head(10))
    with tab3:
        st.altair_chart(make_bar_chart(top_skills, x='Number of jobs',
                        y='Skill', color_scheme='cividis', title='Top skills'))

        st.markdown('#### The most important skills are: ')
        top_3_skills = top_skills['Skill'].head(3).tolist()
        for skill in top_3_skills:
            st.markdown(f"- {skill.capitalize()}")
    


def load_data_and_run_dashboard(keyword ):
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
    jobs_df = pd.read_csv(f'csv_files/jobs_{datetime.today().strftime("%Y-%m-%d")}_{keyword}_{1000}.csv'
                          )
    filtered_df = jobs_df.copy()
    
    selected_city = st.selectbox("Filter by city", ["All"] + sorted(filtered_df["Location"].dropna().unique()))

    if selected_city != "All":
        df_for_company = filtered_df[filtered_df["Location"] == selected_city]
    else:
        df_for_company = filtered_df.copy()
        
    selected_company = st.selectbox("Filter by company",["All"] + sorted(df_for_company["Company"].dropna().unique()))
        
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df["Location"] == selected_city]
    if selected_company != "All":
        filtered_df = filtered_df[filtered_df["Company"] == selected_company]
    render_dashboard(keyword, filtered_df)


if __name__ == '__main__':
    option = st.selectbox('Select the keyword',['Java','Python','AI'])
    load_data_and_run_dashboard(option)

