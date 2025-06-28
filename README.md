# Google Run (grun)

**grun** is a command-line tool for running computational jobs on Google Cloud Batch. It handles Docker image building, cloud storage management, job submission, and result retrieval.

## What You Provide

To run a job with grun, you need:

1. **A bash script** - Your computational job. This is what gets executed.

2. **A Dockerfile** - Defines your runtime environment with the tools and packages your job needs.

3. **Input files** (optional) - Data files your job needs.

## What grun Does

1. **Builds** your Docker image and uploads it to Google Container Registry (GCR)
2. **Creates** a Google Cloud Storage bucket 
3. **Uploads** your input files to the bucket
4. **Submits** your job to Google Cloud Batch
5. **Downloads** results to your local machine when complete

grun also supports local execution for debugging and sanity checks before launching cloud jobs.

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
Install [Docker](https://docs.docker.com/engine/install/) and ensure it's running.

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

3. **Install the command (optional):**
   For convenience, install grun to your system:
   ```bash
   make install
   ```
   This installs `grun` to `/usr/local/bin`, allowing you to run `grun` from anywhere instead of `./grun.py`.

4. **Configure your project:**
   Edit `config.mk` to set your GCP project ID and other defaults:
   ```bash
   # Edit these key variables
   GCP_PROJECT=your-project-id
   LOCATION=us-central1
   ```

## Quick Start

Let's walk through running the included example job:

### 1. Build and Upload Docker Image (once only)
```bash
grun setup_docker
```
This builds the Docker image from `examples/docker/basic_ubuntu/Dockerfile` and pushes it to GCR. **You only need to do this once** unless you change your Dockerfile.

### 2. Set Up Cloud Storage (once only)
```bash
grun setup_bucket
```
This creates your GCS bucket and uploads the job script. **You only need to do this once** - the bucket persists and each job gets its own directory.

### 3. Upload files (optional)
```bash
grun upload_file --job grun-test --input_file examples/files/some_table.txt
```
This uploads your input file to the job's directory in the bucket.

### 4. Submit a Job
```bash
grun submit --job grun-test
```
This submits the job and waits for it to complete (default behavior).

### 5. Monitor the Job (if running asynchronously)
If you run jobs asynchronously (with `--wait F`), you can monitor them:
```bash
# List all jobs
grun list_jobs

# Check job files in the bucket
grun show --job grun-test
```

### 6. Download Results
```bash
grun download --job grun-test --output_dir output
```
Results are downloaded to `output/grun-test`.

## Command Syntax

grun uses a simple command-based syntax:

```bash
grun <command> [options]
```

### Basic Usage
- **Get help**: `grun` (shows all available commands and configuration options)
- **Run a command**: `grun submit --job my-job`
- **Dry run**: `grun --dry-run submit --job my-job` (shows what would be executed)

### Commands
Commands are automatically discovered from the makefile rules. Common commands include:
- `setup_docker` - Build and upload Docker image
- `setup_bucket` - Create bucket and upload scripts
- `submit` - Submit a job to Google Cloud Batch
- `download` - Download job results
- `list_jobs` - List all jobs

### Arguments
Configuration arguments are automatically generated from `config.mk`. Each variable becomes a command-line option:
- `GCP_PROJECT` becomes `--gcp_project`
- `MACHINE_TYPE` becomes `--machine_type`
- `INPUT_FILE` becomes `--input_file`

### Examples
```bash
# Use default configuration
grun submit --job my-analysis

# Override specific settings
grun submit --job my-analysis --machine_type n1-highcpu-16 --disk_size_gb 200

# Preview commands without executing
grun --dry-run setup_docker

# Get help and see all available options
grun
```

## Creating Your Own Job

### 1. Create a Dockerfile (once only)
Define your runtime environment with the tools and packages your job needs.

```dockerfile
FROM ubuntu:22.04

# Install system packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    curl \
    && apt-get clean

# Install a code repository
RUN git clone https://github.com/your-username/your-analysis-repo.git /workspace
WORKDIR /workspace

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Install additional tools as needed
RUN pip3 install pandas numpy scipy scikit-learn

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
# $PARAM1 - custom parameter 1
# $PARAM2 - custom parameter 2

JOB_DIR=$MNT_DIR/jobs/$JOB
OUTPUT_DIR=$JOB_DIR/output

echo "running analysis for job: $JOB"
echo "using parameters: PARAM1=$PARAM1, PARAM2=$PARAM2"
mkdir -p $OUTPUT_DIR

# Your computation here
# Access input files: $JOB_DIR/input_file.txt
# Write results to: $OUTPUT_DIR/results.txt
python3 /my_code/analyze.py $JOB_DIR/data.csv --param1 $PARAM1 --param2 $PARAM2 > $OUTPUT_DIR/analysis.txt
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
grun setup_docker    # Build and upload image (once only)
grun setup_bucket    # Prepare bucket (once only)
grun upload_file --job my-analysis --input_file my_data.csv
grun submit --job my-analysis
grun download --job my-analysis
```

## Local Testing

Before running time-consuming cloud jobs, test locally:

```bash
grun run_local --job test-local --input_file examples/files/some_table.txt
```

This runs your job in a local Docker container, which is much faster for debugging.

## Configuration

You can configure grun in two ways:

1. **Permanently** - Edit `config.mk` to change defaults for all jobs
2. **Per-run** - Use command-line arguments to override settings for specific jobs

All settings in `config.mk` can be overridden via command-line arguments. For example:

```bash
# Override machine type for a specific job
grun submit --job big-job --machine_type n1-highcpu-16

# Increase disk size for large datasets
grun submit --job data-job --disk_size_gb 500

# Use different input file
grun submit --job test --input_file my_other_data.txt
```

Run `grun --help` to see all available commands and options.

### Key Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT` | Your Google Cloud Project ID | - |
| `LOCATION` | GCP region for resources | `us-central1` |
| `MACHINE_TYPE` | Compute instance type | `n1-standard-4` |
| `DISK_SIZE_GB` | Boot disk size in GB | `100` |
| `DOCKER_DIR` | Directory containing Dockerfile | `examples/docker/basic_ubuntu` |
| `RUN_SCRIPT` | Path to your job script | `examples/scripts/run_job.sh` |
| `INPUT_FILE` | Default input file | `examples/files/some_table.txt` |
| `USER_PARAMETERS` | Custom variables for your script | `"INPUT=... B=..."` |
| `OUTPUT_DIR` | Local directory for downloaded results | `output` |

## Directory Structure

### Cloud Bucket Structure
When you run a job, grun creates this structure in your GCS bucket:
```
gs://your-bucket/
├── scripts/
│   └── run_job.sh         # Uploaded job script
└── jobs/
    └── my-test-job-v1/    # Job-specific directory
        ├── some_table.txt # Uploaded input files
        └── output/        # Job results (created by your script)
```

### Container Environment
Inside the running container, files are mounted at `/mnt/disks/share`:
```
/mnt/disks/share/
├── scripts/
│   └── run_job.sh         # Your job script
└── jobs/
    └── my-test-job-v1/    # Job directory
        ├── some_table.txt # Input files
        └── output/        # Write results here
```

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