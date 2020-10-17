#! /usr/bin/python3
# Convert Jekyll kramdown to ZhiHu markdown
# Copyright (C) 2020 Xie Ruifeng
# Licensed under AGPL-3.0 or later

import sys
import argparse
import re

# arguments
parser = argparse.ArgumentParser(
    description='Convert Jekyll kramdown to ZhiHu markdown.')
parser.add_argument('file', metavar='INPUT', type=str, nargs=1,
                    help='input file name')
parser.add_argument('--output', '-o', metavar='OUTPUT', default='-',
                    type=str, nargs=1, help='output file name')
args = parser.parse_args()

# i/o
file = open(args.file[0], "r")
output = args.output[0]
if output == '-':
    output = sys.stdout
else:
    open(output, "w")

# skip YAML meta data
line = file.readline()
if line == '---\n':
    line = file.readline()
    while line != '---\n':
        line = file.readline()
    line = file.readline()

# handle contents
for line in file.readlines():
    if re.match(r'\{:\.\w+\}', line):
        continue
    match = re.match(r'\{%\s*highlight(?:\s+(\w+))+\s*%\}', line)
    if match:
        output.write(match.expand('```\\g<1>\n'))
    elif re.match(r'\{%\s*endhighlight\s*%\}', line):
        output.write('```')
    else:
        line = re.sub(r'<!--.*?-->', '', line)
        line = re.sub(r'\~\~(.*?)\~\~', r'\1（划掉）', line)
        output.write(line)
