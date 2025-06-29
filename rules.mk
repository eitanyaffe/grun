include config.mk

# local bucket directory
LOCAL_BUCKET_DIR?=local_bucket

#####################################################################################
# build and upload docker image to GCR
#####################################################################################

# build docker image and push to GCR
setup_docker:
	bash scripts/build_docker.sh $(DOCKER_DIR) $(IMAGE_NAME)
	docker tag $(IMAGE_NAME) $(DOCKER_IMAGE)
	docker push $(DOCKER_IMAGE)

#####################################################################################
# prepare GCR bucket with model, scripts, configs
#####################################################################################

# create working bucket
create_bucket:
	gsutil ls -b gs://$(BUCKET_NAME) >/dev/null 2>&1 || gsutil mb -l $(LOCATION) gs://$(BUCKET_NAME)

# wrapper script sh path in container
RUN_SCRIPT_PATH?=scripts/run_job.sh

# upload running script to bucket
upload_code:
ifeq ($(RUN_LOCAL),F)
	gsutil -m cp $(RUN_SCRIPT) gs://$(BUCKET_NAME)/$(RUN_SCRIPT_PATH)
else
	mkdir -p $(LOCAL_BUCKET_DIR)/scripts
	cp $(RUN_SCRIPT) $(LOCAL_BUCKET_DIR)/$(RUN_SCRIPT_PATH)
endif

# setup bucket and upload code
setup_bucket:
	$(MAKE) create_bucket upload_code

#####################################################################################
# prepare and submit job
#####################################################################################

# job directory
JOB_DIR?=jobs/$(JOB_TAG)

# job json
JOB_JSON?=$(JOB_DIR)/job.json

## input file short name
INPUT_FILE_SHORT?=$(shell basename $(INPUT_FILE))

# upload file to bucket
upload_file:
ifeq ($(RUN_LOCAL),F)
	gsutil -m cp $(INPUT_FILE) gs://$(BUCKET_NAME)/jobs/$(JOB_TAG)/$(INPUT_FILE_SHORT)
else
	mkdir -p $(LOCAL_BUCKET_DIR)/jobs/$(JOB_TAG)
	cp $(INPUT_FILE) $(LOCAL_BUCKET_DIR)/jobs/$(JOB_TAG)/$(INPUT_FILE_SHORT)
endif

## build json file
build_json:
	mkdir -p $(JOB_DIR)
	python3 scripts/build_json.py \
		--output_file_path $(JOB_JSON) \
		--remote_path $(BUCKET_NAME) \
		--image_uri $(DOCKER_IMAGE) \
		--job_env $(JOB_TAG) \
		--machine_type $(MACHINE_TYPE) \
		--disk_size_gb $(DISK_SIZE_GB) \
		--provisioning_model $(PROVISIONING_MODEL) \
		--accelerator_type $(ACCELERATOR_TYPE) \
		--accelerator_count $(ACCELERATOR_COUNT) \
		--run_script_path $(RUN_SCRIPT_PATH) \
		--user_parameters "$(USER_PARAMETERS)"

# submit job
submit: build_json
	bash scripts/submit_job.sh \
		--job-name $(JOB_TAG) \
		--location $(LOCATION) \
		--job-json $(JOB_JSON) \
		--wait $(WAIT)

#####################################################################################
# run job locally
#####################################################################################

RUN_LOCAL_SCRIPT?=/tmp/run_local.sh

# prepare local data directory and generate docker command
prepare_local:
	python3 scripts/build_local_docker.py \
		--local_bucket_dir $(LOCAL_BUCKET_DIR) \
		--image_uri $(DOCKER_IMAGE) \
		--job_env $(JOB_TAG) \
		--run_script_path $(RUN_SCRIPT_PATH) \
		--user_parameters "$(USER_PARAMETERS)" \
		--output_file $(RUN_LOCAL_SCRIPT)

# run docker command
run_local: 
	@$(MAKE) upload_code upload_file prepare_local RUN_LOCAL=T
	bash $(RUN_LOCAL_SCRIPT)
	@echo "Job completed, output in $(LOCAL_BUCKET_DIR)/jobs/$(JOB_TAG)/output"

#####################################################################################
# download results to local computer
#####################################################################################

# download results
download:
	@mkdir -p $(OUTPUT_DIR)/$(JOB_TAG)
	@echo "downloading results to $(OUTPUT_DIR)/$(JOB_TAG)"
	gsutil -m cp -r gs://$(BUCKET_NAME)/jobs/$(JOB_TAG)/output/* $(OUTPUT_DIR)/$(JOB_TAG)


#####################################################################################
# monitering jobs and debugging
#####################################################################################

# show job directory
show:
	gsutil ls gs://$(BUCKET_NAME)/jobs/$(JOB_TAG)

# list jobs
list_jobs:
	gcloud batch jobs list --location=$(LOCATION)

# show space usage per job in bucket
space:
	python3 scripts/space_usage.py --bucket_name $(BUCKET_NAME)

# clean jobs from bucket (all jobs JOB is set to all)
clean:
	python3 scripts/clean_jobs.py --bucket_name $(BUCKET_NAME) --job_tag $(JOB_TAG)
