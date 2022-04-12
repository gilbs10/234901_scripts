import os
import re

# Possible problems for each task
possible_problems = {
    'hw0': ['icpc4954', 'icpc6152'],
    'hw1': ['supercomputer', 'more10', 'zipline', 'ninepacks', 'uva1218', 'data', 'uva1103', 'blockcrusher', 'uva11072', 'uva10078'],
    'hw2': ['uva11795','uva10645','platforme','roberthood','crowdcontrol','thekingofthenorth','uva12183','coke'],
    'hw3': ['uva11486', 'uva10801', 'gettingthrough', 'uva11523'],
    'lsn1': ['uva10945', 'uva11364', 'uva573','uva156'],
    'lsn2': ['uva12571', 'uva501', 'canvas','virtualfriends'],
    'lsn3': ['monk','uva12694','uva11264','uva11331'],
    'lsn4': ['uva11089','uva900','uva10717','enlarginghashtables','fiat'],
    'lsn5': ['uva200','flipfive','visualgo','uva1056','uva12202'],
    'lsn6': ['uva10256','uva11265','polygonarea','abstractart','saintjohn'],
    'lsn7': ['uva1449','uva12506','uva760','uva11734','kinarow'],
    'lsn8': ['uva1172','uva166','uva11407','uva10271','uva12179'],
    'lsn9': ['uva105','uva4125','doggopher','blowingcandles','closestpair1'],
    'lsn10': ['uva11045','uva11747','uva544','islandhopping','mazemovement','minspantree','waif'],
    'lsn11': ['uva10032','uva12796','uva10482','uva10870','rollercoasterfun'],
    'lsn12': ['uva11311','uva11511','euclidsgame','uva11476','rats'],
    'lsn13': ['local_centsavings','local_cakes','local_dunglish','local_emails','local_glyph','local_kitchen','local_map']
    }
hw_grading = {
    "hw1" : [0, 30, 45, 55, 65, 75, 80, 85, 90, 95, 100],
    "hw2" : [0, 30, 45, 60, 70, 80, 90, 95, 100]
}

broken_problems = {
    'lsn10' : ['uva11045','uva11747'],
    'lsn12' : ['uva11311']
}

ALTERNATIVE_FILE_FOLDER = "alternative_names"
LOCAL_PREFIX = 'local_'

def get_local_pid(pid):
    if LOCAL_PREFIX in pid:
        return pid[len(LOCAL_PREFIX):]
    return pid


problem_alternatives = {}
for assignment in possible_problems:
    problem_alternatives[assignment] = {}
    alternative_fname = os.path.join(ALTERNATIVE_FILE_FOLDER,"{}.txt".format(assignment))
    if os.path.isfile(alternative_fname):
        with open(alternative_fname,"r") as f:
            for l in f:
                names = l.split("\t")
                problem_alternatives[assignment][names[0]] = names[1].strip()


LATE_SUFFIX = "_late"
# Add "late submission" task for each lesson
possible_problems.update({k+LATE_SUFFIX: v
                          for k,v in possible_problems.items()
                          if k.startswith('lsn')})

def assignment_id_clean(assignment_id):
    if assignment_id.endswith(LATE_SUFFIX):
        return assignment_id[:-len(LATE_SUFFIX)]
    return assignment_id

# Submissions directory
submissions_dir = '../Submissions'
input_dir = os.path.join(submissions_dir, 'input')
extracted_dir = os.path.join(submissions_dir, 'extracted')
summary_dir = os.path.join(submissions_dir, 'verdict_summary')
graded_dir = os.path.join(submissions_dir, 'graded')
webcourse_dir = os.path.join(submissions_dir, 'graded_webcourse')

# Make sure all directories exist
for k,v in locals().copy().items():
    if k.endswith('dir'):
        if not os.path.isdir(v):
            raise RuntimeError('{} path does not exist: {}'.format(k,v))

# Number of submissions to retrieve from "My Submissions" page
num_last_submissions = 1500


# Utility functions
# Parsing
def _parse_details_data(details_data):
    " Parse *.details Files "
    parsed = re.findall('^(.*?)\:\s*(.*)', details_data, re.MULTILINE)
    return {key.lower().replace(' ','_'): val.strip()
            for key,val in parsed}

def parse_details_file(details_path):
    return _parse_details_data(open(details_path,'r',encoding="utf8").read())

def parse_problem_id(filename):
    try:
        judge_id = 'uva' if 'uva' in filename.lower() else 'icpc'
        problem_id = int(re.findall('\d{3,5}', filename)[0])
        return judge_id+str(problem_id)
    except IndexError:
        return None

# Iterate extracted files
def process_extracted(filter_func, process_func):
    for dirname in os.listdir(extracted_dir):
        if dirname.startswith('.'):
            continue
        print('-- %s --' % dirname)
        if dirname not in possible_problems.keys():
            print('Assignment undefined: {}'.format(dirname))
            continue
        for f in os.listdir(os.path.join(extracted_dir, dirname)):
            full_path = os.path.join(extracted_dir, dirname, f)
            if filter_func(full_path):
                process_func(full_path)


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''


class Verdicts:
    ACCEPTED = "Accepted"
    WRONG_ANSWER = "Wrong Answer"
    COMPILATION_ERROR = "Compilation Error"
    RUNTIME_ERROR = "Runtime Error"
    TLE = "Time Limit Exceeded"
