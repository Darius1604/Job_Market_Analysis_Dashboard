

# Job Market Analysis Dashboard

This project is a Python-based application that scrapes job market data from timesjobs.com, stores it in a database, and displays it in an interactive Streamlit dashboard.

## Overview

The application consists of three main components:

1.  **Web Scraper (`scraper.py`):** A script designed to fetch job postings and relevant data (like titles, locations, salaries, etc.) from online sources.
2.  **Database (`database.py`):** A database module to store, manage, and query the collected job data.
3.  **Dashboard (`app.py`):** An interactive web dashboard built with Streamlit to visualize and analyze the job market data.

## Features

  * **Data Collection:** Automated web scraping to gather up-to-date job postings.
  * **Data Storage:** A persistent SQL database to store the scraped data for analysis.
  * **Interactive Visualization:** A user-friendly Streamlit dashboard to filter, explore, and analyze job market trends.
  * **CSV Handling:** Utilities for importing or exporting data as CSV files.

## Technologies Used

  * **Python:** The core language for the entire project.
  * **Streamlit:** Used to build and serve the interactive web dashboard.

This project uses several other Python libraries for web scraping (e.g., BeautifulSoup, Playwright, httpx, asyncio), database interaction (psycopg2), and data manipulation(pandas, numpy).

For a complete list of all dependencies, please see the `requirements.txt` file.

## Setup and Installation

Follow these steps to get the project running on your local machine.

**1. Clone the Repository:**

```bash
git clone https://github.com/Darius1604/Job_Market_Analysis_Dashboard.git
cd Job_Market_Analysis_Dashboard
```

**2. Create and Activate a Virtual Environment:**

  * **On macOS/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
  * **On Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

**3. Install Dependencies:**
Install all required libraries from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

**4. Configuration:**
You may need to set up configuration details (e.g., database paths) in the `config/` directory before running the application.

## How to Run

There are two main parts to running the project: collecting the data and viewing the dashboard.

**1. Run the Scraper (Optional):**
To populate or update the database with the latest job postings, run the scraper script.

```bash
python scraper.py
```

**2. Run the Streamlit Dashboard:**
To start the web application and view the dashboard, use the Streamlit CLI.

```bash
streamlit run app.py
```

This will start a local web server and open the dashboard in your default web browser.

## Project Structure

```
.
├── .streamlit/         # Streamlit configuration
├── config/             # Configuration files
├── csv_files/          # Directory for CSV exports/imports
├── db/                 # Database files
├── app.py              # Main Streamlit dashboard application
├── scraper.py          # Web scraping script
├── database.py         # Database models and connection logic
├── csv_handler.py      # Utility for handling CSV files
├── requirements.txt    # Python dependencies
└── ...                 # Other project files
```
