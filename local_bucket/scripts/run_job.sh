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
echo "Input file: $INPUT" > $OUTPUT_DIR/run.log
echo "B: $B" >> $OUTPUT_DIR/run.log

wc -l $JOB_DIR/$INPUT > $OUTPUT_DIR/result.txt 2>&1 | tee $OUTPUT_DIR/run.log
