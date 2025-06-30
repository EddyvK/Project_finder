#!/usr/bin/env python3
import re
import os

def fix_file(filename):
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return False

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove the requirements field line
    pattern = r'requirements=json\.dumps\(list\(project_data\["requirements_tf"\]\.keys\(\)\)\),\s*\n\s*'
    new_content = re.sub(pattern, '', content)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Fixed: {filename}")
    return True

files = [
    'test_tfidf_weighted_matching.py',
    'test_tfidf_low_threshold.py',
    'test_tfidf_debug.py',
    'test_tfidf_complete.py',
    'test_matching_debug.py',
    'test_embedding_fix.py'
]

for f in files:
    fix_file(f)

print("Done!")