#!/usr/bin/env python3

import argparse
import subprocess
import sys
import json
import re

def run_command(cmd, capture_output=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
        if result.returncode != 0:
            print(f"error running command: {cmd}", file=sys.stderr)
            print(f"stderr: {result.stderr}", file=sys.stderr)
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"exception running command: {cmd}: {e}", file=sys.stderr)
        return None

def get_bucket_usage(bucket_name):
    """Get space usage for all jobs in the bucket"""
    print(f"scanning bucket gs://{bucket_name}/jobs/ for job directories...")
    
    # get list of all job directories
    cmd = f"gsutil ls gs://{bucket_name}/jobs/"
    output = run_command(cmd)
    if not output:
        print(f"no jobs found in bucket gs://{bucket_name}/jobs/", file=sys.stderr)
        return []
    
    job_dirs = []
    for line in output.split('\n'):
        if line.strip().endswith('/'):
            job_name = line.strip().rstrip('/').split('/')[-1]
            job_dirs.append(job_name)
    
    print(f"found {len(job_dirs)} job directories")
    print("analyzing space usage for each job...")
    
    # get size information for each job
    jobs_usage = []
    for i, job_name in enumerate(job_dirs, 1):
        print(f"  [{i}/{len(job_dirs)}] analyzing {job_name}...")
        cmd = f"gsutil du -s gs://{bucket_name}/jobs/{job_name}/"
        output = run_command(cmd)
        if output:
            # parse the output to get size in bytes
            match = re.match(r'(\d+)\s+gs://.*', output)
            if match:
                size_bytes = int(match.group(1))
                jobs_usage.append({
                    'job_name': job_name,
                    'size_bytes': size_bytes,
                    'size_mb': round(size_bytes / (1024 * 1024), 2),
                    'size_gb': round(size_bytes / (1024 * 1024 * 1024), 3)
                })
    
    print(f"completed analysis of {len(jobs_usage)} jobs")
    return jobs_usage

def format_size(size_bytes):
    """Format size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def main():
    parser = argparse.ArgumentParser(description="show space usage per job in the bucket")
    parser.add_argument('--bucket_name', required=True, help='bucket name')
    parser.add_argument('--format', choices=['human', 'json'], default='human', 
                       help='output format (default: human)')
    
    args = parser.parse_args()
    
    # get space usage information
    jobs_usage = get_bucket_usage(args.bucket_name)
    
    if not jobs_usage:
        print("no jobs found or unable to retrieve space information")
        return
    
    # sort by size descending
    jobs_usage.sort(key=lambda x: x['size_bytes'], reverse=True)
    
    if args.format == 'json':
        print(json.dumps(jobs_usage, indent=2))
    else:
        # human readable format
        print(f"space usage per job in bucket gs://{args.bucket_name}/jobs/")
        print("-" * 60)
        print(f"{'Job Name':<30} {'Size':<15}")
        print("-" * 60)
        
        total_size = 0
        for job in jobs_usage:
            print(f"{job['job_name']:<30} {format_size(job['size_bytes']):<15}")
            total_size += job['size_bytes']
        
        print("-" * 60)
        print(f"{'Total':<30} {format_size(total_size):<15}")
        print(f"Number of jobs: {len(jobs_usage)}")

if __name__ == "__main__":
    main() 