import re

# Read the file
with open('scheduled_worker.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace print with safe_print (but not in the safe_print function definition itself)
lines = content.split('\n')
new_lines = []
skip_next = False

for i, line in enumerate(lines):
    # Don't replace in the safe_print function definition
    if 'def safe_print' in line:
        skip_next = True
    elif skip_next and line.strip().startswith('print('):
        skip_next = False
    
    if not skip_next and '    print(' in line and 'safe_print' not in line:
        line = line.replace('print(', 'safe_print(')
    
    new_lines.append(line)

# Write back
with open('scheduled_worker.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print('✅ Updated all print() to safe_print()')
