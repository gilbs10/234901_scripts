import json
import os
import csv
import time
import copy
import pandas as pd
from datetime import datetime

from config import possible_problems,\
    process_extracted,\
    summary_dir,\
    parse_details_file, \
    hw_grading, \
    get_local_pid, \
    broken_problems

# HW Score
def is_valid_problem_id(task, problem_id):
    return problem_id in possible_problems[task]

def filter_submission(f):
    return f.endswith('.submission')

def summarize_verdicts(submission_path):
    # Parse .submission file
    submission_summary = json.load(open(submission_path,'r'))
    webcourse_details = parse_details_file(submission_path.replace('.submission','.details'))
    task_name = os.path.basename(os.path.dirname(submission_path))
    # Change verdicts
    for submission_details in submission_summary:
        submission_details['student_ids'] = webcourse_details['submitted_by'].zfill(9)
        submission_details['submitter'] = webcourse_details['submitter']
        submission_details['task'] = task_name
        submission_details['is_valid'] = is_valid_problem_id(task_name, submission_details['problem_id'])
        submission_details['oj_verdict'] = submission_details['oj_verdict'].lower()
        for key in submission_details:
            if key.endswith('time'):
                submission_details[key] = datetime.fromtimestamp(submission_details[key])
        all_submissions_lst.append(copy.copy(submission_details))


# Main
if __name__=='__main__':
    # All submisssions
    all_submissions_lst = []                                        
    
    # Check files
    process_extracted(filter_submission, summarize_verdicts)
    print('%d submissions found' % len(all_submissions_lst))

    # All submissions csv
    all_submissions = pd.DataFrame.from_dict(all_submissions_lst)
    all_submissions.to_csv(os.path.join(summary_dir, 'all_submissions.csv'))

    # Broken problems - problems that were broken in class, count them in a special file
    broken_problems_counter = {}
    # Create summaries for each task
    task_pivs = {}
    for task, task_df in all_submissions.groupby('task'):
        task_piv = pd.pivot_table(
            task_df,
            index='student_ids',
            columns='problem_id',
            values='oj_verdict',
            aggfunc=lambda s: 'accepted' if (s == 'accepted').sum() else s.iloc[0],
        )
        for problem_id in possible_problems[task]:
            if problem_id not in task_piv:
                task_piv[problem_id] = None
        task_piv = task_piv[possible_problems[task]]
        task_piv['webcourse_submission_date'] = task_df.groupby('student_ids')['submission_time'].max()
        task_piv['submitter'] = task_df.groupby('student_ids')['submitter']\
                                .aggregate(lambda s: ', '.join(set(s)))
        task_pivs[task] = task_piv

    # Make sure class and late submissions don't conflict
    for task, task_piv in task_pivs.items():
        # For late lesson submissions, account for problems solved in class
        if task.endswith('late'):
            lsn_task_piv = task_pivs[task.replace('_late','')]
            lsn_task_by_student = pd.DataFrame(columns=possible_problems[task])
            for idx, row in lsn_task_piv[possible_problems[task]].iterrows():
                for student_id in idx.split(', '):
                    lsn_task_by_student.loc[student_id] = row
            lsn_task_by_student[lsn_task_by_student!='accepted'] = None
            lsn_task_by_student[lsn_task_by_student=='accepted'] = '(solved in class)'
            for idx, row in task_piv[possible_problems[task]].iterrows():
                if idx in lsn_task_by_student.index:
                    task_piv.loc[idx,possible_problems[task]] = lsn_task_by_student.loc[idx].fillna(task_piv.loc[idx,possible_problems[task]])
            if task.replace('_late','') in broken_problems:
                for idx, row in task_piv[broken_problems[task.replace('_late','')]].iterrows():
                    # print(idx)
                    for pid in broken_problems[task.replace('_late','')]:
                        # print(row[pid])
                        if row[pid] == 'accepted':
                            if idx not in broken_problems_counter:
                                broken_problems_counter[idx] = 0
                            broken_problems_counter[idx] += 1

        # Add summary and empty columns
        task_piv['num_rejected'] = ((task_piv[possible_problems[task]]!='accepted') \
                                    & task_piv[possible_problems[task]].notnull()).sum(axis=1)
        task_piv['num_accepted'] = (task_piv[possible_problems[task]] == 'accepted').sum(axis=1)
        task_piv['days_late'] = ''
        task_piv['description_modifier'] = ''
        task_piv['final_grade'] = ''
        task_piv['comments'] = ''
        # Save CSV
        task_piv.to_csv(os.path.join(summary_dir, '{}.csv'.format(task)))

    ids = set()
    all_grades = {} # (id,task) -> grade
    for task, task_piv in task_pivs.items():
        with open(os.path.join(summary_dir, '{}_gr.csv'.format(task)), 'w+') as f:
            # f.write("ID, {}\n".format(task))
            for i,r in task_piv.iterrows():
                for id in i.split(", "):
                    ids.add(id)
                    grade = r['num_accepted']
                    if task in hw_grading:
                        grade = hw_grading[task][grade]
                    all_grades[(id,task)] = grade
                    f.write("{} {}\n".format(int(id),grade))
    with open(os.path.join(summary_dir, 'all_gr.csv'.format(task)), 'w+') as f:
        f.write("ID")
        tasks = list(task_pivs.keys())
        for task in tasks:
            f.write(",{}".format(task))
        f.write("\n")
        for id in ids:
            f.write(id)
            for task in tasks:
                g = ""
                if (id,task) in all_grades:
                    g = all_grades[(id,task)]
                f.write(",{}".format(g))
            f.write("\n")
    with open(os.path.join(summary_dir, 'broken_problems.csv'.format(task)), 'w+') as f:
        for idx, n in broken_problems_counter.items():
            f.write("{} {}\n".format(idx, n))
    # print(grades_summary)