import asyncio
import httpx  # or the client library you use
from bs4 import BeautifulSoup
from datetime import datetime

# Replace fetch_job_async with your function if it's already defined
async def fetch_job_async(client, url):
    try:
        r = await client.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'lxml')
        outer_container = soup.find('div', class_=['jd-page', 'ui-page', 'ui-page-theme-a',
                                                   'ui-page-header-fixed', 'ui-page-footer-fixed', 'ui-page-active'])
        if not outer_container:
            return None

        inner_container = outer_container.find('div', class_='jdpage-main')

        # Job info: title, company and the positing date
        job_information = inner_container.find('div', id='jobTitle')
        job_title = job_information.h1.text.strip()
        company_name = job_information.h2.span.text.strip()
        posting_time = job_information.find(
            'span', class_='posting-time').text.strip()
        posting_time_date = datetime.strptime(posting_time, '%d %b, %Y').date()

        # Location and experience
        location_exp_infos = inner_container.find(
            'div', class_='clearfix exp-loc')
        location_text = location_exp_infos.find(
            'div', class_='srp-loc jd-loc').text.strip()
        location_list = location_text.split()
        location = location_list[1].translate(str.maketrans('', '', '()/,'))
        years_of_experience = location_exp_infos.find(
            'div', class_='srp-exp').text.split()
        years_of_experience = years_of_experience[0] + \
            ' ' + years_of_experience[1]

    # Key Skills
        key_skill_links = inner_container.find('div', id='JobDetails').find(
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
    except Exception as e:
        print(f"Failed fetching {url}: {e}")
        return None
url = "https://m.timesjobs.com/mobile/job-detail/manager-reporting-python-power-bi-sql-6-years-gurgaon-job-crescendo-global-gurgaon-6-to-8-yrs-jobid-L1BeTvasnpZzpSvf__PLUS__uAgZw==&bc=+&sequence=705"  # replace with a real job URL

async def main():
    async with httpx.AsyncClient() as client:
        job_data = await fetch_job_async(client, url)
        print(job_data)

# Run the async function
asyncio.run(main())
