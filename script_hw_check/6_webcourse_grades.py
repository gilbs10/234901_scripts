import pandas as pd
import os

from config import summary_dir, webcourse_dir

if __name__=='__main__':
    all_grades = pd.DataFrame()
    for f in os.listdir(summary_dir):
        if f.startswith('.'):
            continue
        print(f)
        input_path = os.path.join(summary_dir,f)
        output_path = os.path.join(webcourse_dir,os.path.splitext(f)[0]+'.txt')
        # Parse grades
        if f.endswith('.csv'):
            df = pd.read_csv(input_path)
        elif f.endswith('.xlsx') or f.endswith('.xls'):
            df = pd.read_excel(input_path)
        # Convert to webcourse format
        grades = pd.DataFrame(
            df['student_ids'].astype(str).str.zfill(9).str.split(', ').tolist(),
            index=df['final_grade']
        ).stack()\
         .reset_index()[[0,'final_grade']]\
         .set_index(0)\
         .rename(columns={'final_grade': os.path.splitext(f)[0].upper()})\
         .astype(int)
        assert len(set(grades.index)) == len(grades.index)
        grades.to_csv(output_path, header=False, sep=' ')
        all_grades = all_grades.merge(grades, how='outer', left_index=True, right_index=True)

    # Summary of all grades
    all_grades.index.name = 'id'
    all_grades_path = os.path.join(webcourse_dir,'all.csv')
    all_grades.fillna('-').to_csv(all_grades_path, sep=',')
                
        
