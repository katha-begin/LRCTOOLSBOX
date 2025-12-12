#!/usr/bin/env python3
"""
Convert f-strings to .format() for Python 2.7 compatibility
"""
import re
import sys

def convert_fstring_to_format(line):
    """Convert f-string to .format() style."""
    # Pattern to match f"..." or f'...'
    pattern = r'f(["\'])((?:(?!\1).)*)\1'
    
    def replacer(match):
        quote = match.group(1)
        content = match.group(2)
        
        # Find all {var} patterns
        vars_pattern = r'\{([^}]+)\}'
        variables = re.findall(vars_pattern, content)
        
        # Replace {var} with {}
        new_content = re.sub(vars_pattern, '{}', content)
        
        # Build .format() call
        if variables:
            format_args = ', '.join(variables)
            return '{}{}{}.format({})'.format(quote, new_content, quote, format_args)
        else:
            # No variables, just remove the f prefix
            return '{}{}{}'.format(quote, new_content, quote)
    
    return re.sub(pattern, replacer, line)

def convert_file(filepath):
    """Convert all f-strings in a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    converted_lines = []
    for line in lines:
        converted_line = convert_fstring_to_format(line)
        converted_lines.append(converted_line)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(converted_lines)
    
    print("Converted {} lines".format(filepath))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python convert_fstrings.py <filepath>")
        sys.exit(1)
    
    convert_file(sys.argv[1])

