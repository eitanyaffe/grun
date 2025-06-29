#!/usr/bin/env python3

import argparse
import subprocess
import sys

def run_command(cmd, capture_output=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
        if result.returncode != 0:
            print(f"error running command: {cmd}", file=sys.stderr)
            print(f"stderr: {result.stderr}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"exception running command: {cmd}: {e}", file=sys.stderr)
        return False

def get_job_list(bucket_name):
    """Get list of all jobs in the bucket"""
    cmd = f"gsutil ls gs://{bucket_name}/jobs/"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return []
        
        job_dirs = []
        for line in result.stdout.split('\n'):
            if line.strip().endswith('/'):
                job_name = line.strip().rstrip('/').split('/')[-1]
                job_dirs.append(job_name)
        return job_dirs
    except Exception:
        return []

def confirm_deletion(job_name=None, job_count=0):
    """Ask user to confirm deletion"""
    if job_name:
        print(f"you are about to delete job: {job_name}")
        print("this will permanently remove all files for this job from the bucket")
    else:
        print(f"you are about to delete ALL {job_count} jobs from the bucket")
        print("this will permanently remove all job files from the bucket")
    
    print("this action cannot be undone!")
    
    while True:
        response = input("are you sure you want to continue? (yes/no): ").lower().strip()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("please enter 'yes' or 'no'")

def clean_job(bucket_name, job_name):
    """Clean a specific job"""
    print(f"checking if job {job_name} exists...")
    cmd = f"gsutil ls gs://{bucket_name}/jobs/{job_name}/ >/dev/null 2>&1"
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode != 0:
        print(f"job {job_name} not found in bucket")
        return False
    
    if not confirm_deletion(job_name=job_name):
        print("deletion cancelled")
        return False
    
    print(f"deleting job {job_name}...")
    cmd = f"gsutil -m rm -r gs://{bucket_name}/jobs/{job_name}/"
    success = run_command(cmd, capture_output=False)
    
    if success:
        print(f"successfully deleted job {job_name}")
    else:
        print(f"failed to delete job {job_name}")
    
    return success

def clean_all_jobs(bucket_name):
    """Clean all jobs"""
    print("scanning for jobs in bucket...")
    job_list = get_job_list(bucket_name)
    
    if not job_list:
        print("no jobs found in bucket")
        return True
    
    print(f"found jobs: {', '.join(job_list)}")
    
    if not confirm_deletion(job_count=len(job_list)):
        print("deletion cancelled")
        return False
    
    print("deleting all jobs...")
    success = True
    for job_name in job_list:
        print(f"  deleting {job_name}...")
        cmd = f"gsutil -m rm -r gs://{bucket_name}/jobs/{job_name}/"
        if not run_command(cmd, capture_output=False):
            print(f"  failed to delete {job_name}")
            success = False
        else:
            print(f"  deleted {job_name}")
    
    if success:
        print(f"successfully deleted all {len(job_list)} jobs")
    else:
        print("some jobs failed to delete")
    
    return success

def main():
    parser = argparse.ArgumentParser(description="clean jobs from the bucket")
    parser.add_argument('--bucket_name', required=True, help='bucket name')
    parser.add_argument('--job_tag', required=True, help='job to clean (use "all" to clean all jobs)')
    
    args = parser.parse_args()
    
    if args.job_tag.lower() == 'all':
        success = clean_all_jobs(args.bucket_name)
    else:
        success = clean_job(args.bucket_name, args.job_tag)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 