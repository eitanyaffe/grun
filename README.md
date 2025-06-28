# Google Run (grun)

**grun** is a command-line tool that simplifies running computational jobs on Google Cloud Batch. Designed for researchers who want to leverage cloud computing without dealing with the complexities of Google Cloud Platform, grun handles Docker image building, cloud storage management, job submission, and result retrieval automatically.

## What You Provide

To run a job with grun, you need:

1. **A bash script** - Your computational job (e.g., `run_job.sh`)
2. **A Dockerfile** - Defines your runtime environment  
3. **Input files** (optional) - Data files your job needs

## What grun Does

1. **Builds** your Docker image and uploads it to Google Container Registry (GCR)
2. **Creates** a Google Cloud Storage bucket 
3. **Uploads** your input files to the bucket
4. **Submits** your job to Google Cloud Batch
5. **Downloads** results to your local machine when complete

grun also supports local execution for debugging and sanity checks before launching expensive cloud jobs.

## Prerequisites

### Google Cloud SDK
Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) and authenticate:
```bash
# Initialize gcloud and log in
gcloud init
gcloud auth login

# Authorize application-level credentials (used by scripts)
gcloud auth application-default login
```

### Docker
Install [Docker](https://docs.docker.com/engine/install/) and ensure it's running. On macOS:
```bash
open -a Docker
```

### Python 3
Required for the grun wrapper script.

### GCP Project Setup
You need a Google Cloud Project with the necessary APIs enabled. Key services used:
- Google Cloud Batch API
- Google Container Registry API  
- Google Cloud Storage API

For detailed instructions on setting up user permissions and enabling APIs, see [google.md](google.md).

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/eitanyaffe/grun.git
   cd grun
   ```

2. **Set the environment variable:**
   Add this to your shell configuration (e.g., `~/.zshrc`, `~/.bashrc`):
   ```bash
   export GRUN_DIR=/path/to/your/grun
   ```
   Reload your shell: `source ~/.zshrc`

3. **Configure your project:**
   Edit `config.mk` to set your GCP project ID and other defaults:
   ```bash
   # Edit these key variables
   GCP_PROJECT=your-project-id
   LOCATION=us-central1
   ```

## Quick Start

Let's walk through running the included example job:

### 1. Build and Upload Docker Image
```bash
./grun.py setup_docker
```
This builds the Docker image from `examples/docker/basic_ubuntu/Dockerfile` and pushes it to GCR.

### 2. Set Up Cloud Storage
```bash
./grun.py setup_bucket
```
This creates your GCS bucket and uploads the job script.

### 3. Upload files (optional)

```bash
./grun.py upload_file --job my-test-job --input_file examples/files/some_table.txt
```
This uploads your input file.


### 4. Submit a Job
```bash
./grun.py submit --job my-test-job --input_file examples/files/some_table.txt --wait T
```
This uploads your input file, submits the job, and returns after the job completed.

### 5. Monitor the Job

Relevant if jobs were run asynchronsiously (with `--wait F`).
```bash
# List all jobs
./grun.py list_jobs

# Check job files in the bucket
./grun.py show --job my-test-job
```

### 5. Download Results
```bash
./grun.py download --job my-test-job
```
Results are downloaded to `output/my-test-job/`. The output directory can be determined with the `OUTPUT_DIR` variable.

## Creating Your Own Job

### 1. Create a Dockerfile (once)
Define your runtime environment:

```dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && apt-get clean

COPY my_code/ /my_code/
RUN pip3 install -r /my_code/requirements.txt

CMD ["bash"]
```

### 2. Create a Job Script

Your job script accesses files using environment variables:
- `$MNT_DIR` - Mount directory (`/mnt/disks/share`)
- `$JOB` - Job name (`my-test-job-v1`)
- Custom parameters from `USER_PARAMETERS`

Create a bash script that performs your computation:

```bash
#!/bin/bash
# my_analysis.sh

set -e -o pipefail
trap 'echo "Command failed. Exiting."; exit 1' ERR

# Environment variables available:
# $MNT_DIR - mount directory (/mnt/disks/share)
# $JOB - job name
# Custom variables from USER_PARAMETERS

JOB_DIR=$MNT_DIR/jobs/$JOB
OUTPUT_DIR=$JOB_DIR/output

echo "Running analysis for job: $JOB"
mkdir -p $OUTPUT_DIR

# Your computation here
# Access input files: $JOB_DIR/input_file.txt
# Write results to: $OUTPUT_DIR/results.txt
python3 /my_code/analyze.py $JOB_DIR/data.csv > $OUTPUT_DIR/analysis.txt
```

### 3. Update Configuration
Edit `config.mk` to point to your files:
```bash
RUN_SCRIPT=path/to/my_analysis.sh
DOCKER_DIR=path/to/my_dockerfile_dir
INPUT_FILE=path/to/my_data.csv
USER_PARAMETERS="PARAM1=value1 PARAM2=value2"
```
See `config.mk` for a complete list of variables.
### 4. Run Your Job
```bash
./grun.py setup_docker    # Build and upload image
./grun.py setup_bucket    # Prepare bucket
./grun.py upload_file --job my-analysis --input_file my_data.csv
./grun.py submit --job my-analysis
./grun.py download --job my-analysis
```

## Local Testing

Before running time-consuming cloud jobs, test locally:

```bash
./grun.py run_local --job test-local --input_file examples/files/some_table.txt
```

This runs your job in a local Docker container, which is much faster for debugging.

## Configuration

All settings in `config.mk` can be overridden via command-line arguments. For example:

```bash
# Override machine type for a specific job
./grun.py submit --job big-job --machine_type n1-highcpu-16

# Use different input file
./grun.py submit --job test --input_file my_other_data.txt
```

Run `./grun.py --help` to see all available commands and options.

### Key Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT` | Your Google Cloud Project ID | - |
| `LOCATION` | GCP region for resources | `us-central1` |
| `MACHINE_TYPE` | Compute instance type | `n1-standard-4` |
| `DOCKER_DIR` | Directory containing Dockerfile | `examples/docker/basic_ubuntu` |
| `RUN_SCRIPT` | Path to your job script | `examples/scripts/run_job.sh` |
| `INPUT_FILE` | Default input file | `examples/files/some_table.txt` |
| `USER_PARAMETERS` | Custom variables for your script | `"INPUT=... B=..."` |

## Available Commands

- `setup_docker` - Build and upload Docker image
- `create_bucket` - Create GCS bucket  
- `upload_code` - Upload job script to bucket
- `setup_bucket` - Combined: create bucket + upload code
- `upload_file` - Upload input file to bucket
- `submit` - Submit job (includes file upload and JSON generation)
- `run_local` - Run job locally for testing
- `download` - Download job results
- `list_jobs` - List all batch jobs
- `show` - Show files in job bucket directory

## Implementation

grun is implemented as a Python wrapper around a makefile system. The `grun.py` script automatically discovers available commands from `rules.mk` and converts makefile variables in `config.mk` into command-line arguments. This design provides a user-friendly interface while maintaining the flexibility and power of make for job orchestration.

When you run a grun command, it constructs and executes the corresponding `make` command with your specified parameters. For example, `./grun.py submit --job test` becomes `make submit JOB=test` internally. 