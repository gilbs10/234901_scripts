import os
import zipfile
import shutil
import hashlib
import time
import re
import json
from glob import glob

from config import input_dir, extracted_dir

def extract_zip(zip_path, extracted_dir):
    zip_obj = zipfile.ZipFile(zip_path)
    filename_parts = os.path.splitext(os.path.basename(zip_path.lower()))[0].split('-')
    assignment_name = filename_parts[0]
        
    # Create destination directory
    extract_to = os.path.join(extracted_dir, assignment_name)
    if not os.path.isdir(extract_to):
        os.mkdir(extract_to)
    # Extract files
    if 'manual' not in filename_parts:
        # Webcourse files
        zip_obj.extractall(extract_to)
    else:
        # Manual submissions
        orig_filename = os.path.basename(zip_path).replace(assignment_name,'').strip('-')
        dst_filename = os.path.join(extract_to, orig_filename)
        tz = filename_parts[1:filename_parts.index('manual')]
        tz.sort() # make sure the ids are sorted to avoid conflicts with webcourse submissions
        shutil.copy(zip_path, dst_filename)       
        # Create details file for late submissions
        details_path = os.path.join(
            extract_to,
            orig_filename.replace('.zip','.details')
        )
        with open(details_path,'w') as details_file:
            file_sha256 = hashlib.sha256(open(zip_path, 'rb').read()).hexdigest()
            submission_time_st = time.strftime(
                '%d/%m/%Y, %H:%M:%S',
                time.strptime(filename_parts[-1],'%Y%m%d')
            )
            details_file.write('Submitted by: %s\n' % ', '.join(tz))
            details_file.write('SHA256 checksum: %s\n' % file_sha256)
            details_file.write('Date of submission: %s\n' % submission_time_st)
            details_file.write('Submitter: MANUAL\n')
        

if __name__=='__main__':
    for zip_path in glob(os.path.join(input_dir,'*.zip')):
        print(zip_path)
        extract_zip(zip_path, extracted_dir)
