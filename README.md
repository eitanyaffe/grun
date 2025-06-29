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
```

### Docker
Install [Docker](https://docs.docker.com/engine/install/) and ensure it's running.

### GCP Project Setup
You need a Google Cloud Project with the necessary APIs enabled. For detailed instructions on setting up user permissions and enabling APIs, see [google.md](google.md).

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/eitanyaffe/grun.git
   cd grun
   ```

2. **Install the command:**
   For convenience, install grun to your system:
   ```bash
   make install
   ```
   This installs `grun` to `/usr/local/bin`, allowing you to run `grun` from anywhere instead of `./grun.py`.

3. **Set the environment variable:**
   Add this to your shell configuration (e.g., `~/.zshrc`, `~/.bashrc`):
   ```bash
   export GRUN_DIR=/path/to/your/grun
   ```
   Reload your shell: `source ~/.zshrc`


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
grun setup_docker --docker_dir examples/docker/basic_ubuntu
```
This builds the Docker image from `examples/docker/basic_ubuntu/Dockerfile` (replace with your docker directory) and pushes it to GCR. **You only need to do this once** unless you change your Dockerfile.

### 2. Set Up Cloud Storage (once only)
```bash
grun setup_bucket --user_script examples/scripts/run_job.sh
```
This creates your GCS bucket and uploads the job script. **You only need to do this once** - the bucket persists and each job gets its own directory.

You can upload auxilary scripts:
```bash
grun upload_code --user_script examples/scripts/analyze.py
```
This uploads a script input file to the script directory in the bucket.

### 3. Upload other files (optional)
```bash
grun upload_file --job grun-test --input_file examples/files/some_table.txt
```
This uploads a file to the job directory in the bucket for job `grun-test`.

### 4. Submit a Job
```bash
grun submit --job grun-test --wait T
```
This submits job `grun-test` and waits for it to complete.

### 5. Monitor the Job (if running asynchronously)
You can monitor job statuses:
```bash
# List all jobs
grun list_jobs

# Show list of job files in the bucket
grun show --job grun-test
```

### 6. Download Results
```bash
grun download --job grun-test --output_dir output
```
Results will be downloaded to `output/grun-test`.

## Customize Your Own Job

You can define your runtime environment with the tools and packages your job needs by creating a Dockerfile. A Dockerfile is a text file that contains instructions for building a Docker image. See this example of a basic [dockerfile](examples/docker/basic_ubuntu/Dockerfile) and learn more about [writing Dockerfiles](https://docs.docker.com/get-started/docker-concepts/building-images/writing-a-dockerfile/).

You need to implement a single bash script that will perform the work on the cloud. This script should:
- Accept parameters passed via environment variables
- Create output directories and files as needed

See this [example](examples/scripts/run_job.sh) for a complete working script.

## Local Testing

Before running a job on the cloud you can test it locally:

```bash
grun run_local --job test-local --input_file examples/files/some_table.txt --ifn some_table.txt --param1 17
```

This runs your job in a local Docker container, which is much faster for debugging.

## Command Syntax

grun uses a simple command-based syntax:

```bash
grun <command> [options]
```

### Basic Usage
- **Get help**: `grun` (shows all available commands and configuration options)
- **Run a command**: `grun submit --job my-job`
- **Dry run**: `grun submit --job my-job --dry-run` (shows what would be executed, also works with `-n`)

### Commands
Commands are automatically discovered from the makefile rules. Common commands include:
- `setup_docker` - Build and upload Docker image
- `setup_bucket` - Create bucket and upload scripts
- `submit` - Submit a job to Google Cloud Batch
- `download` - Download job results
- `list_jobs` - List all jobs
- `space` - Show space usage per job in bucket
- `clean` - Delete jobs from bucket (with confirmation)

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

# Check space usage and clean up jobs
grun space                    # Show space usage for all jobs
grun clean --job_tag all          # Delete all jobs (with confirmation)
grun clean --job_tag old-test     # Delete specific job (with confirmation)

# Get help and see all available options
grun
```

## Configuration

You can configure grun parameters in two ways:

1. **Permanently** - Edit `config.mk` to change defaults for all jobs
2. **Per-run** - Use command-line arguments to override settings for specific jobs

All settings in `config.mk` can be overridden via command-line arguments. For example:

```bash
# Override machine type and disk size for a specific job
grun submit --job big-job --machine_type n1-highcpu-16 --disk_size_gb 500
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
| `USER_SCRIPT` | Path to your job script | `examples/scripts/run_job.sh` |
| `INPUT_FILE` | Default input file | `examples/files/some_table.txt` |
| `USER_PARAMETERS` | Custom variables for your script | `"IFN=... PARAM1=..."` |
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

Inside the running docker container, the bukcet is mounted at `/mnt/disks/share`.

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
- `space` - Show space usage per job in bucket
- `clean` - Delete jobs from bucket (with confirmation)

## Implementation

grun is implemented as a Python wrapper around a makefile system. The `grun.py` script automatically discovers available commands from `rules.mk` and converts makefile variables in `config.mk` into command-line arguments. This design provides a user-friendly interface while maintaining the flexibility and power of make for job orchestration.

When you run a grun command, it constructs and executes the corresponding `make` command with your specified parameters. For example, `./grun.py submit --job test` becomes `make submit JOB=test` internally. 