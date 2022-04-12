# Get statistics of all the problems from the uva judge
# Just run the code, no input :)

import requests
import csv
from bs4 import BeautifulSoup as bs

categories = ['submissions','tried','solved']
min_p = 30 # Min number to try (real problems starts from 36)
max_p = 100 # Max number to try (there are ~5000 problems)
site_template = 'https://uva.onlinejudge.org/index.php?option=com_onlinejudge&Itemid=8&page=problem_stats&problemid=%d&category=0'
stats = []
failed = 0
failed_threshold = 100 # After this number of failed attempts the code stops
for p_num in range(min_p,max_p+1):
    site = requests.get(site_template % p_num)
    if site.status_code is 200:
        print(p_num)
        content = bs(site.content, 'html.parser')
        problem_header = content.find(class_='componentheading').get_text()
        if problem_header == ' - ':
            failed += 1
            if failed>failed_threshold:
                print("failed threshold")
                break
            continue
        failed = 0
        stats.append({})
        stats[-1]['title'] = problem_header
        print(problem_header)
        solvers_table = content.find(class_='sectiontableentry1')
        # print(solvers_table[0])
        for i,entry in enumerate(solvers_table.find_all('td')):
            stats[-1][categories[i]] = entry.get_text()
csv_cols = ['title'] + categories
with open('uva_stats.csv','w',encoding="utf-8",newline='') as f:
    writer = csv.DictWriter(f,fieldnames=csv_cols)
    writer.writeheader()
    for s in stats:
        writer.writerow(s)
print(len(stats))

