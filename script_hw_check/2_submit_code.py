import os
import re
import zipfile
import json
import time
import subprocess
import sys

from pdb import pm
from pprint import pprint


from config import possible_problems, \
    process_extracted, \
    parse_details_file, \
    problem_alternatives, \
    ALTERNATIVE_FILE_FOLDER, \
    assignment_id_clean, \
    bcolors, \
    LOCAL_PREFIX, \
    get_local_pid
from credentials import login_details
from livearchive import LiveArchiveConnection, UVAConnection
from local_manager import submit_locally

def time_count_down(t):
    print("Out of tokens", end = '')
    for i in range(t,-1,-1):
        print('\r'+bcolors.OKBLUE+'Next submission in: {} seconds'.format(i)+bcolors.ENDC, end='')
        sys.stdout.flush()
        time.sleep(1)
    print("")

# Parsing Functions
def is_legal_cpp_filename(filename):
    filename = filename.lower()
    return (filename.endswith('.cpp')) \
           and not (filename.startswith('._') or filename.startswith('__'))

def parse_problem_id(filename):
    try:
        judge_id = 'uva' if 'uva' in filename.lower() else 'icpc' if 'icpc' in filename.lower() else 'kattis'
        if judge_id == 'kattis':
            p_id =  filename.split(".")[0]
        else:
            problem_id = int(re.findall('\d{3,5}', filename)[0])
            p_id = judge_id+str(problem_id)
    except IndexError:
        p_id = ""
    return p_id

def get_probelm_from_list(file_name, assignment_id, possible_problems):
    assignment_id = assignment_id_clean(assignment_id)
    while file_name in problem_alternatives[assignment_id]:
        file_name = problem_alternatives[assignment_id][file_name]
    p_id = parse_problem_id(file_name)
    while p_id not in possible_problems:
        new_name = input(bcolors.FAIL+"Problem with filename {}, in assignment {}. enter an alternative name:".format(file_name, assignment_id)+bcolors.ENDC)
        with open(os.path.join(ALTERNATIVE_FILE_FOLDER,"{}.txt".format(assignment_id)), "a+") as f:
            f.write("{}\t{}\n".format(file_name, new_name))
            problem_alternatives[assignment_id][file_name] = new_name
        file_name = new_name
        while file_name in problem_alternatives[assignment_id]:
            file_name = problem_alternatives[assignment_id][file_name]
        p_id = parse_problem_id(file_name)
    return p_id

# Submission function
def submit_problem(conn, problem_id, code, problem_id_alternatives=[]):
    # time_count_down(5)
    if 'uva' not in problem_id.lower() and 'icpc' not in problem_id.lower() and LOCAL_PREFIX not in problem_id.lower():
        return kattis_submitter(problem_id, code, problem_id_alternatives)
    elif LOCAL_PREFIX in problem_id.lower():
        return local_submitter(problem_id, code, problem_id_alternatives)
    else:
        return uva_submitter(conn, problem_id, code, problem_id_alternatives)

def get_kattis_id(problem_id, problem_id_alternatives):
    for p_id in problem_id_alternatives:
        if p_id in problem_id.lower():
            return p_id
    return None

def kattis_submitter(problem_id, code, problem_id_alternatives=[]):
    kattis_id = get_kattis_id(problem_id, problem_id_alternatives)
    submission_details = []
    if kattis_id is None:
        return submission_details
    f_name = kattis_id+'.cpp'
    with open(f_name, 'w+', encoding="utf-8") as f:
        try:
            f.write(code.decode('ascii'))
        except:
            for c in code:
                print(c, chr(c))
    while True:
        stream = subprocess.check_output('python3 kattis_submit.py -f -b '+ f_name, shell=True)
        stream = stream.decode('ascii')
        try:
            sub_id = int(re.findall('\d+',re.findall('ID: \d+',stream)[0])[0])
            break
        except IndexError:
            print(stream)
            try:
                time_till_token = int(re.findall('\d+', stream)[0])
            except:
                time_till_token = 15;
            time_till_token = max(time_till_token,15)
            time_count_down(time_till_token)
    submission_details.append({
        'oj_judeg_type': 'kattis',
        'oj_submission_time': time.time(),
        'problem_id': kattis_id,
        'oj_submission_id': sub_id,
        'oj_verdict': 'N/A',
        'oj_verdict_update_time': time.time()})    
    os.remove(f_name)
    return submission_details


def local_submitter(problem_id, code, problem_id_alternatives=[]):
    problem_id_clean = get_local_pid(problem_id)
    print(problem_id_clean)
    verdict = submit_locally(problem_id_clean, code)
    print(verdict)
    submission_details = []
    submission_details.append({
        'oj_judeg_type': 'local_judge',
        'oj_submission_time': time.time(),
        'problem_id': problem_id,
        'oj_submission_id': 'N/A',
        'oj_verdict': verdict,
        'oj_verdict_update_time': time.time()})
    return submission_details

def uva_submitter(conn, problem_id, code, problem_id_alternatives=[]):
    # Submit single problem 
    # Check if we need to use a different problem id
    if (problem_id is None) \
       or (problem_id_alternatives and problem_id not in problem_id_alternatives):
        # Cant parse problem id, try alternatives
        if not problem_id_alternatives:
            raise RuntimeError('Invalid problem id, alternatives not provided')
    else:
        problem_id_alternatives = [problem_id,]
    # Submit and save the details
    submission_details = []
    for pid in problem_id_alternatives:
        judge = re.findall('\D+',pid)[0]
        problem_number = int(re.findall('\d+',pid)[0])
        while True:
            try:
                submission_id = conn[judge].quick_submit(problem_number, code)
                break
            except RuntimeError:
                print("Trying again")
        submission_details.append({
            'oj_judeg_type': 'uva',
            'oj_submission_time': time.time(),
            'problem_id': pid,
            'oj_submission_id': submission_id,
            'oj_verdict': 'N/A',
            'oj_verdict_update_time': time.time()})
    return submission_details
    
def submit_zip(conn, zip_path, details, assignment_id, problem_id_alternatives=[]):
    " Submit zip file "
    out = []
    zip_obj = zipfile.ZipFile(zip_path)
    for inner_file in zip_obj.filelist:
        orig_filename = os.path.basename(inner_file.filename)
        if is_legal_cpp_filename(orig_filename):
            problem_id = get_probelm_from_list(orig_filename, assignment_id, problem_id_alternatives)
            print('Parsing problem ID: {} -> {}'.format(orig_filename, problem_id))
            # Extract code
            code = zip_obj.read(inner_file)
            # Submit problem
            submission_details = submit_problem(conn, problem_id, code, problem_id_alternatives)
            for submission in submission_details:
                submission['orig_filename'] = orig_filename
                submission['file_path'] = zip_path
                submission['file_sha256'] = details['sha256_checksum']
                submission['submission_time'] = time.mktime(
                    time.strptime(details['date_of_submission'], '%d/%m/%Y, %H:%M:%S')
                )
                out.append(submission)
    return out
                
def submit_cpp(conn, cpp_path, details, assignment_id, problem_id_options=[]):
    orig_filename = details['file_name']
    problem_id = get_probelm_from_list(orig_filename, assignment_id, problem_id_options)
    print(orig_filename, '->', problem_id)
    # Extract code
    code = open(cpp_path,'rb').read()
    # Submit problem
    submission_details = submit_problem(conn, problem_id, code, problem_id_options) 
    for submission in submission_details:
        submission['orig_filename'] = orig_filename
        submission['file_path'] = cpp_path
        submission['file_sha256'] = details['sha256_checksum']
        submission['submission_time'] = time.mktime(time.strptime(details['date_of_submission'],
                                                                  '%d/%m/%Y, %H:%M:%S'))
    return submission_details

# MAIN
def filter_unsubmitted(f):
    # This script works on .details files
    # without a matching .submissions file
    return f.endswith('.details') \
        and (not os.path.isfile(f.replace('.details','.submission')))

def submit(details_path):
    # Parse filename
    root = os.path.dirname(details_path)
    basename = os.path.splitext(os.path.basename(details_path))[0]
    print(basename)
    assignment_id = os.path.basename(root)
    # Parse .details file
    details = parse_details_file(details_path)
    problem_options = possible_problems[assignment_id]

    # Look for related files
    cpp_path = os.path.join(root, basename+'.cpp')
    txt_path = os.path.join(root, basename+'.txt')
    zip_path = os.path.join(root, basename+'.zip')
    submission_path = os.path.join(root, basename+'.submission')
    # Look for zip files
    if os.path.isfile(zip_path):
        submission_details = submit_zip(conn, zip_path, details, assignment_id, problem_options)
    # Look for cpp files
    elif os.path.isfile(cpp_path):
        submission_details = submit_cpp(conn, cpp_path, details, assignment_id, problem_options)
    elif os.path.isfile(txt_path):
        submission_details = submit_cpp(conn, txt_path, details, assignment_id, problem_options)
    # Raise an exception of no file was found
    else:
        raise ValueError('Source not found')
    # Print details and save
    pprint(submission_details)
    json.dump(submission_details, open(submission_path, 'w'))

if __name__=='__main__':
    # Connect to livearchive
    # conn = {'icpc':LiveArchiveConnection(*login_details['icpc']),
            # 'uva':UVAConnection(*login_details['uva'])} 
    # livearchive is down, only uva remains
    conn = {'uva':UVAConnection(*login_details['uva'])}
    # Submit all new files
    process_extracted(filter_unsubmitted, submit)


