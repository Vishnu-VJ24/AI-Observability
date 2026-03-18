import os
import glob
import autopep8

def format_all():
    files = glob.glob('**/*.py', recursive=True)
    for f in files:
        if '.venv' in f: continue
        print(f"Formatting {f}...")
        with open(f, 'r', encoding='utf-8') as file:
            source = file.read()
            
        fixed = autopep8.fix_code(source, options={'max_line_length': 79, 'aggressive': 2})
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(fixed)
            
if __name__ == "__main__":
    format_all()
