#!/bin/sh

set -e -o pipefail
trap 'echo "Command failed. Exiting."; exit 1' ERR

SCRIPTS_DIR=$MNT_DIR/scripts
JOB_DIR=$MNT_DIR/jobs/$JOB

OUTPUT_DIR=$JOB_DIR/output

echo "Running job: $JOB"
echo "Mount directory: $MNT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Scripts directory: $SCRIPTS_DIR"

# create output directory
mkdir -p $OUTPUT_DIR

# script arguments
echo "Input file: $IFN" > $OUTPUT_DIR/run.log

# replace this with job-specific parameters
echo "XXX: $XXX" >> $OUTPUT_DIR/run.log

# replace this with your job code
wc -l $JOB_DIR/$IFN > $OUTPUT_DIR/result.txt
