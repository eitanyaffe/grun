#!/bin/bash
# Generated local Docker run command
docker run -it --rm -v /Users/eitany/work/git/grun/local_bucket:/mnt/disks/share --gpus all -e MNT_DIR=/mnt/disks/share -e JOB=grun-test-v1 -e CUDA_VISIBLE_DEVICES=0 -e INPUT=some_table.txt -e B=11 --workdir /mnt/disks/share gcr.io/relman-yaffe/eitany/grun-shared bash /mnt/disks/share/scripts/run_job.sh
