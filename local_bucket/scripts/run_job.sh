#!/bin/sh

set -e -o pipefail
trap 'echo "Command failed, exiting."; exit 1' ERR

# Define your log file
LOG_FILE=$MNT_DIR/jobs/$JOB/output/run.log

# Create parent dir in advance if needed
mkdir -p "$(dirname "$LOG_FILE")"

# Run everything inside this block and tee output
{
    SCRIPTS_DIR=$MNT_DIR/scripts
    JOB_DIR=$MNT_DIR/jobs/$JOB
    OUTPUT_DIR=$JOB_DIR/output

    echo "Running job: $JOB"
    echo "Mount directory: $MNT_DIR"
    echo "Output directory: $OUTPUT_DIR"
    echo "Scripts directory: $SCRIPTS_DIR"

    # create output directory
    mkdir -p "$OUTPUT_DIR"

    # NOTE: replace below with your job code

    # script arguments, defined by USER_PARAMETERS
    echo "Input file: $IFN"
    echo "PARAM1: $PARAM1"

    # this is a placeholder for your job code
    wc -l "$JOB_DIR/$IFN" > "$OUTPUT_DIR/result.txt"
} 2>&1 | tee "$LOG_FILE"
