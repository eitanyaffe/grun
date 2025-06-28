#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import sys
import signal

def parse_config_vars(config_path):
    """
    Parses a makefile-style config file and returns a dict of variables.
    It captures the comment immediately above the variable as its description.
    """
    vars = {}
    last_comment = ""
    skip_next = False
    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()

                if not line:
                    last_comment = ""  # Reset on empty lines
                    skip_next = False
                    continue

                if line.startswith('#'):
                    # check if comment starts with ## before stripping
                    skip_next = line.startswith('##')
                    # capture the comment, removing '#' and leading space
                    last_comment = line.lstrip('#').strip()
                    continue

                match = re.match(r'^([A-Z_]+)\s*\??=\s*(.*)', line)
                if match:
                    key, value = match.groups()
                    # skip variables with skip flag set
                    if not skip_next:
                        vars[key] = {
                            'value': value.strip(),
                            'description': last_comment.capitalize() if last_comment else last_comment
                        }
                    last_comment = "" # Reset after use
                    skip_next = False
    except FileNotFoundError:
        # Since we hard-code config.mk, this is a fatal error for the script's setup
        print(f"Error: Main config file not found at '{config_path}'", file=sys.stderr)
        print("This file is required to define available arguments.", file=sys.stderr)
        sys.exit(1)
    return vars

def parse_makefile_rules(rules_path):
    """
    Parses a makefile and returns a dict of rules.
    It captures the comment immediately above each rule as its description.
    """
    rules = {}
    last_comment = ""
    skip_next = False
    try:
        with open(rules_path, 'r') as f:
            for line in f:
                line = line.strip()

                if not line:
                    last_comment = ""  # reset on empty lines
                    skip_next = False
                    continue

                if line.startswith('#'):
                    # check if comment starts with ## before stripping
                    skip_next = line.startswith('##')
                    # capture the comment, removing '#' and leading space
                    last_comment = line.lstrip('#').strip()
                    continue

                # match makefile rules (target:)
                match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
                if match:
                    target = match.group(1)
                    # skip rules with skip flag set
                    if not skip_next:
                        description = last_comment.capitalize() if last_comment else f"Execute the {target} make target"
                        rules[target] = {
                            'description': description
                        }
                    last_comment = ""  # reset after use
                    skip_next = False
                elif not line.startswith('\t'):
                    # reset comment if we encounter a non-rule, non-comment, non-indented line
                    last_comment = ""
                    skip_next = False
    except FileNotFoundError:
        print(f"Error: Rules file not found at '{rules_path}'", file=sys.stderr)
        print("This file is required to define available commands.", file=sys.stderr)
        sys.exit(1)
    return rules

def run_command(command):
    cmd_str = ' '.join(command)
    print(f"Running command: {cmd_str}")
    try:
        exit_code = os.system(cmd_str)
        # os.system returns a 16-bit encoded value: high byte is signal, low byte is exit code
        if os.WIFSIGNALED(exit_code):
            sig = os.WTERMSIG(exit_code)
            print(f"Command terminated by signal {sig}", file=sys.stderr)
            sys.exit(128 + sig)
        elif os.WEXITSTATUS(exit_code) != 0:
            print(f"Command exited with code {os.WEXITSTATUS(exit_code)}", file=sys.stderr)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)

def get_make_args(args, config_vars):
    """Constructs a list of KEY=VALUE strings for make."""
    make_args = []
    # We only need the keys from the config_vars to check against args
    for key in config_vars.keys():
        arg_key = key.lower()
        if hasattr(args, arg_key) and getattr(args, arg_key) is not None:
            make_args.append(f"{key}={getattr(args, arg_key)}")
    return make_args
    
def main():
    """Main function."""
    GRUN_DIR = os.environ.get('GRUN_DIR')
    if not GRUN_DIR:
        print("Error: The environment variable GRUN_DIR is not set.", file=sys.stderr)
        print("Please set it to the root directory of the grun project.", file=sys.stderr)
        print("For example, add this to your .zshrc or .bashrc:", file=sys.stderr)
        print(f"export GRUN_DIR={os.getcwd()}", file=sys.stderr)
        sys.exit(1)

    try:
        os.chdir(GRUN_DIR)
    except FileNotFoundError:
        print(f"Error: The directory specified by GRUN_DIR does not exist: {GRUN_DIR}", file=sys.stderr)
        sys.exit(1)

    # parse config variables and makefile rules
    config_vars = parse_config_vars('config.mk')
    makefile_rules = parse_makefile_rules('rules.mk')
    
    parser = argparse.ArgumentParser(
        description="grun: Launch jobs on Google Cloud Batch.\n",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = True

    # dynamically add commands from makefile rules
    for rule_name, rule_data in makefile_rules.items():
        cmd_parser = subparsers.add_parser(
            rule_name,
            help=rule_data['description'],
            description=rule_data['description'],
            formatter_class=argparse.RawTextHelpFormatter
        )
        
        # add config variables as arguments for each command
        for var, data in config_vars.items():
            arg_name = f'--{var.lower()}'
            help_text = data.get('description') or f"Overrides {var}."
            default_val_str = f" Default: {data.get('value')}"
            help_text += default_val_str
            cmd_parser.add_argument(arg_name, help=help_text)
    
    # if run without arguments, print help and exit
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        print("\nConfiguration Arguments (from config.mk):", file=sys.stderr)
        
        if config_vars:
            # evaluate default values by calling make for each variable
            evaluated_defaults = {}
            for var in config_vars.keys():
                try:
                    # use the generic 'print-VAR' rule now in the makefile
                    command = ['make', '-s', f'print-{var}']
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        check=True,
                        cwd=GRUN_DIR 
                    )
                    evaluated_defaults[var] = result.stdout.strip()
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # if make fails, fall back to the raw value from the config file
                    evaluated_defaults[var] = config_vars[var].get('value', 'N/A')

            # calculate padding for alignment
            max_len = max(len(f'--{var.lower()}') for var in config_vars.keys())
            for var, data in config_vars.items():
                arg_name = f'--{var.lower()}'
                description = data.get('description', 'No description available.')
                default_val = evaluated_defaults.get(var, 'N/A')
                print(f"  {arg_name:<{max_len + 2}} {description} (Default: {default_val})", file=sys.stderr)

        sys.exit(0)

    args = parser.parse_args()
    make_args = get_make_args(args, config_vars)
    
    # run the make command with the specified rule
    run_command(['make', args.command] + make_args)

if __name__ == "__main__":
    main() 