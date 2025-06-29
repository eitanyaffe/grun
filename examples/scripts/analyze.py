#!/usr/bin/env python3

import argparse
import os

parser = argparse.ArgumentParser(description='Simple analysis script')
parser.add_argument('--input', required=True)
parser.add_argument('--param1', required=True)
parser.add_argument('--param2', required=True)
parser.add_argument('--output', required=True)
args = parser.parse_args()

# create output directory if needed
output_dir = os.path.dirname(args.output)
if output_dir:
    os.makedirs(output_dir, exist_ok=True)

# write simple output
with open(args.output, 'w') as f:
    f.write(f"analysis complete\n")
    f.write(f"input: {args.input}\n")
    f.write(f"param1: {args.param1}\n")
    f.write(f"param2: {args.param2}\n")

print(f"analysis done, output written to {args.output}") 