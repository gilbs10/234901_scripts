import os
import re
import zipfile
import json
import time
import requests
from bs4 import BeautifulSoup as bs
import kattis_submit


from config import possible_problems, \
         process_extracted, \
         num_last_submissions

from credentials import login_details
         

from livearchive import LiveArchiveConnection, UVAConnection

from pdb import pm
from pprint import pprint

def filter_submission(f):
    return f.endswith('.submission')

def update_verdicts(submission_path):
    # Parse .submission file
    submission_summary = json.load(open(submission_path,'r'))
    # Change verdicts
    is_changed = False
    for submission_details in submission_summary:
        if submission_details['oj_judeg_type'] == 'uva':
            try:
                is_changed |= update_verdicts_uva(submission_details)
            except KeyError:
                print("Error in {}. Removing file, resubmit it.".format(submission_details))
                os.remove(submission_path)
                return
        else:
            is_changed |= update_verdicts_kattis(submission_details)

    # Rewrite the details if it changed
    if is_changed:
        json.dump(submission_summary, open(submission_path,'w'))

def update_verdicts_uva(submission_details):
    # Broken!!!
    # verdict = 'accepted' if submission_details['oj_verdict'] in ['Accepted','N/A'] else submission_details['oj_verdict']
    is_changed = False
    judge_id = re.findall('\D+',submission_details['problem_id'])[0]
    verdict = verdict_cache[judge_id][submission_details['oj_submission_id']]['Verdict'].strip().lower()
    if verdict != submission_details['oj_verdict']:
        print("UVA:", submission_details['oj_verdict'], '->', verdict)
        is_changed = True
        submission_details['oj_verdict'] = verdict
    return is_changed

def update_verdicts_kattis(submission_details):
    if submission_details['oj_verdict'] != 'N/A':
        return False
    is_changed = False
    sub_id = int(submission_details['oj_submission_id'])
    site = kattis_submit.get_submission_results(sub_id, kattis_login_data)
    if site.status_code == 200:
        content = bs(site.content, 'html.parser')
        verdict = content.find(class_='status').get_text().lower()
        if verdict != submission_details['oj_verdict']:
            print("Kattis:", submission_details['oj_verdict'], '->', verdict)
            is_changed = True
            submission_details['oj_verdict'] = verdict
    return is_changed

if __name__=='__main__':
    # Connect to livearchive
    conn = {'uva':UVAConnection(*login_details['uva'])}

    # # Retrieve latest verdicts
    verdict_cache = {judge: conn[judge].my_submissions(num_last_submissions)
                     for judge in conn}

    kattis_login_data = kattis_submit.login_blank()
    # Check files
    process_extracted(filter_submission, update_verdicts)
