import os
import re
import zipfile
import json
import time
import cgi

from pdb import pm, set_trace
from pprint import pprint

from config import possible_problems,\
     process_extracted,\
     summary_dir,\
     parse_details_file

html_template = u'''
<table style="width:100%" cellpadding=30>
  <caption>{zip_filename} - {cpp_filename}</caption>
  <col width="50%">
  <col width="50%">
  <tr>
    <th>Description</th>
    <th>Code</th>
  </tr>
  <tr>
    <td style="background: #faffff; dir: rtl; white-space: pre-wrap; font-family: monospace, 'Courier New'; vertical-align: text-top">
<b>Description:</b>
{desc}

<b>Submission Details:</b>
{verdict}
    </td>
    <td>{code}</td>
  </tr>
</table><hr>
'''

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import chardet
import unicodedata
from io import StringIO

lexer = get_lexer_by_name("cpp", stripall=True)
formatter = HtmlFormatter(linenos=False,
                          full=False,
                          noclasses=True,
                          nobackground=True)

id2name = {'icpc3135':'Argus', 'icpc6139':'Interval Product', 'icpc4944':'Fair Division', 'icpc5358':'8 Queens Chess Problem', 'icpc6527':'Counting Ones', 'icpc4303':'Top Secret', 'icpc5139':'Rare Order', 'icpc2425':'Mice and Maze', 'icpc5130':'Ancient Messages', 'uva10585':'Center of symmetry',
'uva11362':'Phone List', 'uva1254':'Top 10', 'icpc4299':'Randomly-priced Tickets', 'icpc3619':'Sum of Different Primes', 'icpc7425':'Cleaning Pipes', 'icpc7274':'Canvas Painting', 'uva105':'The Skyline Problem', 'uva1111':'Trash Removal'}
# Parsing Functions
def parse_details_file(details_data):
    " Parse *.details Files "
    parsed = re.findall('^(.*?)\:\s*(.*)', details_data, re.MULTILINE)
    return {key.lower(): val for key,val in parsed}

def parse_problem_id(filename):
    try:
        judge_id = 'uva' if 'uva' in filename.lower() else 'icpc'
        problem_id = int(re.findall('\d{3,5}', filename)[0])
        return judge_id+str(problem_id)
    except IndexError:
        return None

def is_legal_cpp_filename(filename):
    filename = filename.lower()
    return (filename.endswith('.cpp')) \
           and not (filename.startswith('._') or filename.startswith('__'))

def clean_filename(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

# Submission function   
def create_submission_htmls(zip_path, submisssion):
    " Submit zip file "
    out = {}
    zip_obj = zipfile.ZipFile(zip_path)
    # Create a dictionary with clean filenames
    # (ignoring spaces and unicode control characters)
    clean_filenames = {clean_filename(zfile.filename): zfile
                       for zfile in zip_obj.filelist}
    # Create an HTML report for each cpp file
    for inner_file in zip_obj.filelist:
        orig_filename = os.path.basename(inner_file.filename)
        if is_legal_cpp_filename(orig_filename):
            # Extract code
            code = zip_obj.read(inner_file)
            problem_id = parse_problem_id(orig_filename)
            # Extract Description
            try:
                desc_file = clean_filenames[clean_filename(orig_filename).replace('cpp','txt')]
                desc = zip_obj.read(desc_file)
                encoding = chardet.detect(desc)['encoding']
                assert encoding is not None
                desc = desc.decode(encoding)
            except KeyError:
                try:
                    print("Hi")
                    desc_file = clean_filenames[id2name[problem_id]+".txt"]
                    desc = zip_obj.read(desc_file)
                    encoding = chardet.detect(desc)['encoding']
                    assert encoding is not None
                    desc = desc.decode(encoding)
                except KeyError:
                    print(zip_path)
                    desc = u'N/A'
            except AssertionError:
                desc = u'Encoding not detected. File might be binary.'
            # Get verdict
            verdict = [details for details in submisssion if details['orig_filename']==orig_filename]
            verdict_io = StringIO()
            pprint(verdict, verdict_io)
            pretty_verdict = verdict_io.getvalue()
            pretty_verdict = pretty_verdict.replace('accepted','<font color="green">accepted</font>')
            # Fix problem ID if the file was accpeted
            if problem_id is None \
               and 'accepted' in [details['oj_verdict'] for details in verdict]:
                problem_id = [details for details in verdict
                              if details['oj_verdict']=='accepted'][0]['problem_id']
            # Render submission html
            code_pygments = code=highlight(code, lexer, formatter) # highlight cpp
            submission_html = html_template.format(zip_filename=os.path.basename(zip_path),
                                                   cpp_filename=orig_filename,
                                                   code=code_pygments,
                                                   desc=cgi.escape(desc),
                                                   verdict=pretty_verdict)
            out[problem_id] = submission_html
    
    return out

def html_from_list(lst):
    return '<html><meta charset="UTF-8"><body>' + u''.join(lst) + '</body></html>'

def filter_details(filename):
    return filename.endswith('.details')

def process_details(details_path):
    # Parse .details file
    details = parse_details_file(open(details_path,'r',encoding='utf8').read())
    # Parse problems files
    dirname = os.path.dirname(details_path)
    basename = os.path.splitext(os.path.basename(details_path))[0]
    zip_path = os.path.join(dirname, basename+'.zip')
    submission_path = os.path.join(dirname, basename+'.submission')
    html_path = os.path.join(dirname, basename+'.html')
    # Read submission details
    submission = json.load(open(submission_path,'r'))
    # Create html
    html_summary = create_submission_htmls(zip_path, submission)
    open(html_path,'w',encoding='utf8').write(html_from_list(html_summary.values()))
    # Create per-problem summaries
    problem_options = possible_problems[os.path.basename(dirname)]
    for problem_id in html_summary:
        per_problem_html_filename = str(problem_id)
        if problem_id not in problem_options:
            per_problem_html_filename += '-invalid'
        per_problem_html_path = os.path.join(dirname,per_problem_html_filename+'.html')
        problem_summaries.setdefault(per_problem_html_path, list()).append(html_summary[problem_id])

if __name__=='__main__':
    problem_summaries = {}
    process_extracted(filter_details, process_details)

    # Create report files grouped by problem ID
    for html_path, summaries in problem_summaries.items():
        open(html_path,'w',encoding='utf8').write(html_from_list(summaries))            

