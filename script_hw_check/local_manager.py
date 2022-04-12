import os
import subprocess
import zipfile
import yaml
from tkinter import filedialog
from config import bcolors, Verdicts

PROBLEMS_DIR = "local_problems"
WORKSPACE_DIR = "workspace"
CODE_FILE_NAME = "submitted_code.cpp"
METADATA_FILE = "problem.yaml"
COMPILATION_FLAGS ="-std=c++11 -DNDEBUG -Wall"
EXECUTABLE_FILE = "main.out"
COMPILE_OUTPUT_FILE = "compile_output.txt"
TESTS_FOLDER = "data"
INPUT_FILE_SUFFIX = ".in"
ANSWER_FILE_SUFFIX = ".ans"
CODE_OUTPUT_FILE = "temp.out"
VALIDATOR_RUNFILE = 'validate'
VALIDATOR_FOLDER = os.path.join('output_validators','validate')
DEFAULT_VALIDATION_TIME = 3
ACCEPTED_EXIT_CODE = 42

def load_problem(problem_name = ''):
    problem_archive = filedialog.askopenfilename(filetypes=[('Zip file', '*.zip')])
    archive = zipfile.ZipFile(problem_archive, 'r')
    if METADATA_FILE in archive.namelist():
        with archive.open(METADATA_FILE, 'r') as f:
            config = yaml.safe_load(f)
            if 'name' in config:
                problem_name = config['name']
    while not problem_name:
        problem_name = input("No {} file in archive, or no problem name, enter a problem name.".format(METADATA_FILE))
        config = {}
        config['name'] = problem_name
    problem_name = problem_name.lower()
    problem_dir = os.path.join(PROBLEMS_DIR, problem_name)
    os.mkdir(problem_dir)
    archive.extractall(problem_dir)


def compile_code():
    """Compiling the files in workspace dir and returns a path to the executable"""
    source_file = os.path.join(WORKSPACE_DIR,CODE_FILE_NAME)
    exe_file = os.path.join(WORKSPACE_DIR, EXECUTABLE_FILE)
    output_file = os.path.join(WORKSPACE_DIR, COMPILE_OUTPUT_FILE)
    if os.system("g++ {} -o {} {} 2> {}".format(COMPILATION_FLAGS, exe_file, source_file, output_file)) == 0:
        return exe_file
    return ""

def default_validate(test_ans_file, submitted_ans_file):
    with open(submitted_ans_file, "r") as out_file, open(test_ans_file ,"r") as test_out_file:
        out_lines = out_file.readlines()
        test_lines = test_out_file.readlines()
        if len(out_lines) != len(test_lines):
            return Verdicts.WRONG_ANSWER
        for l1, l2 in zip(out_lines, test_lines):
            if l1.strip() != l2.strip():
                return Verdicts.WRONG_ANSWER
        return Verdicts.ACCEPTED

def specific_validate(test_in_file, test_ans_file, submitted_ans_file, validator_dir):
    runfile = os.path.join(validator_dir,VALIDATOR_RUNFILE)
    if not os.path.isfile(runfile):
        source_files = os.path.join(validator_dir,"*.cpp")
        os.system("g++ {} -o {}".format(source_files, runfile))
    res = os.system("{} {} {} {} < {}".format(runfile, test_in_file, test_ans_file, WORKSPACE_DIR, submitted_ans_file))
    res = os.WEXITSTATUS(res)
    if res == ACCEPTED_EXIT_CODE:
        return Verdicts.ACCEPTED
    else:
        return Verdicts.WRONG_ANSWER

def check_test(exe_file, test_input_file, test_answer_file, validator_dir, time_limit):
    # print("Checking {}".format(test_input_file))
    output_file = os.path.join(WORKSPACE_DIR, CODE_OUTPUT_FILE)
    with open(test_input_file) as f_in, open(output_file, 'w') as f_out:
        with subprocess.Popen(exe_file, stdin=f_in, stdout=f_out) as p:
            try:
                p.wait(timeout=time_limit)
            except subprocess.TimeoutExpired:
                print("TIMEOUT")
                p.kill()
                return Verdicts.TLE
    if validator_dir:
        return specific_validate(test_input_file, test_answer_file, output_file, validator_dir)
    else:
        return default_validate(test_answer_file, output_file)

def test_submission(exe_file, tests_folder, validator_dir = "", time_limit = DEFAULT_VALIDATION_TIME):
    res = Verdicts.ACCEPTED
    for d in os.listdir(tests_folder):
        cur_d = os.path.join(tests_folder,d)
        if os.path.isdir(cur_d):
            for f in os.listdir(cur_d):
                if f.endswith(INPUT_FILE_SUFFIX):
                    test_name = f.split(".")[0]
                    input_file = os.path.join(cur_d,test_name+INPUT_FILE_SUFFIX)
                    answer_file = os.path.join(cur_d,test_name+ANSWER_FILE_SUFFIX)
                    res = check_test(exe_file, input_file, answer_file, validator_dir, time_limit)
                    if res != Verdicts.ACCEPTED:
                        return res
    return res

def submit_locally(p_id, code):
    # print(p_id)
    problem_dir = os.path.join(PROBLEMS_DIR, p_id)
    while not os.path.isdir(problem_dir):
        print(bcolors.FAIL + "Can't find local problem {}, please select the problem data zip file.".format(p_id) + bcolors.ENDC)
        load_problem(p_id)
    if not os.path.isdir(WORKSPACE_DIR):
        os.mkdir(WORKSPACE_DIR)
    with open(os.path.join(WORKSPACE_DIR,CODE_FILE_NAME), "wb") as f:
        f.write(code)
    exe_file = compile_code()
    if exe_file == "":
        return Verdicts.COMPILATION_ERROR
    # TODO Load time limit
    validator_dir = os.path.join(problem_dir,VALIDATOR_FOLDER)
    if not os.path.isdir(validator_dir):
        validator_dir = ""
    return test_submission(exe_file, os.path.join(problem_dir,TESTS_FOLDER), validator_dir)

# with open("raphael.cpp","r") as f:
#     code = f.read()
#     local_submitter("cakes",code)
