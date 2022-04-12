import os

from config import process_extracted

def filt_submissions(f_name):
    return f_name.split(".")[-1] == "submission"

def clear_empty(f_name):
    remove_file = False
    with open(f_name) as f:
        lines = f.readlines()
        if lines[0] == '[]':
            remove_file = True
    if remove_file:
        print(f_name)
        os.remove(f_name)

process_extracted(filt_submissions, clear_empty)