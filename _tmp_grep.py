import re

lines = open('frontend/index.html').read().split('\n')
for i, line in enumerate(lines):
    if 'toLocaleString' in line:
        print("{}: {}".format(i+1, line))

lines = open('frontend/agent.html').read().split('\n')
for i, line in enumerate(lines):
    if 'toLocaleString' in line:
        print("{}: {}".format(i+1, line))
