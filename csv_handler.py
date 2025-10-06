import pandas as pd
from pathlib import Path
from datetime import datetime

def save_jobs_csv(jobs, keyword, limit):
    df = pd.DataFrame(jobs)
    df_sorted = df.sort_values(by='Posted on', ascending=False)
    df_sorted = df_sorted.reset_index(drop=True)
    df_sorted.index = df_sorted.index + 1
    Path("csv_files").mkdir(parents=True, exist_ok=True)

    csv_file = f"csv_files/jobs_{datetime.today().strftime('%Y-%m-%d')}_{keyword}_{limit}.csv"
    df_sorted.to_csv(csv_file, index=False)
    print(f"\nSaved {len(jobs)} jobs to {csv_file}")
    return 0
