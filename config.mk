#####################################################################################
# Google parameters
#####################################################################################

# GCP project
GCP_PROJECT?=relman-yaffe

# bucket and job location
LOCATION?=us-central1

#####################################################################################
# docker
#####################################################################################

# directory with dockerfile
DOCKER_DIR?=examples/docker/basic_ubuntu

# docker image name, shared is a shared image that is used by all jobs
IMAGE_NAME?=shared

# docker image name
DOCKER_IMAGE?=gcr.io/$(GCP_PROJECT)/$(USER)/grun-$(IMAGE_NAME)

#####################################################################################
# GCP paths
#####################################################################################

# bucket name
BUCKET_NAME?=$(GCP_PROJECT)-$(USER)-grun

#####################################################################################
# job parameters
#####################################################################################

# job label (unique string identifier)
JOB?=grun-test

# job version (allows to submit the same job multiple times)
JOB_VERSION?=v1

# run locally (TRUE or FALSE)
RUN_LOCAL?=F

# wrapper script sh path in container
RUN_SCRIPT?=examples/scripts/run_job.sh

# input file
INPUT_FILE?=examples/files/some_table.txt

# input file short name
INPUT_FILE_SHORT?=$(shell basename $(INPUT_FILE))

# wait for job to complete (TRUE or FALSE)
WAIT?=T

# user-defined parameters
USER_PARAMETERS?="INPUT=$(INPUT_FILE_SHORT) B=11"

#####################################################################################
# runtime and output parameters
#####################################################################################

# machine type (see https://cloud.google.com/compute/docs/machine-resource)
MACHINE_TYPE?=n1-standard-4

# boot disk size in GB
DISK_SIZE_GB?=100

# provisioning model (SPOT or STANDARD)
PROVISIONING_MODEL?=STANDARD

# accelerator type
ACCELERATOR_TYPE?=nvidia-h100-80gb

# accelerator count (number of GPUs)
ACCELERATOR_COUNT?=0

# output directory (data is downloaded here)
OUTPUT_DIR?=output
