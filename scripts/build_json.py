import argparse
import json

def main():
    parser = argparse.ArgumentParser(description="Build a JSON configuration file for a Google Cloud Batch job.")

    # Required arguments
    parser.add_argument("--output_file_path", required=True, help="Path to save the generated JSON file.")
    parser.add_argument("--remote_path", required=True, help="The GCS bucket path (e.g., \"relman-evo2\").")
    parser.add_argument("--image_uri", required=True, help="The Docker image URI (e.g., \"gcr.io/relman-yaffe/evo2\").")
    parser.add_argument("--job_env", required=True, help="Value for the JOB environment variable.")
    parser.add_argument("--run_script_path", required=True, help="Path to the execution script within the container (e.g., \"scripts/run.sh\").")

    # Optional arguments
    parser.add_argument("--machine_type", default="a3-highgpu-1g", help="The machine type.")
    parser.add_argument("--disk_size_gb", type=int, default=100, help="The boot disk size in GB.")
    parser.add_argument("--accelerator_type", default="nvidia-h100-80gb", help="The accelerator type.")
    parser.add_argument("--accelerator_count", type=int, default=1, help="The number of accelerators.")
    parser.add_argument("--provisioning_model", default="SPOT", help="The provisioning model (e.g., SPOT, STANDARD).")
    parser.add_argument("--max_retry_count", type=int, default=0, help="The maximum retry count for the task.")
    parser.add_argument("--user_parameters", required=True, help="User-defined parameters.")

    args = parser.parse_args()

    # Construct the command for the container
    # The script path is relative to the mount point /mnt/disks/share
    container_command = f"bash /mnt/disks/share/{args.run_script_path}"

    cuda_visible_devices = ",".join(map(str, range(args.accelerator_count)))

    environment_variables = {
        "MNT_DIR": "/mnt/disks/share",
        "JOB": args.job_env,
        "CUDA_VISIBLE_DEVICES": cuda_visible_devices
    }
    if args.user_parameters:
        for param in args.user_parameters.split():
            if '=' in param:
                key, value = param.split('=', 1)
                environment_variables[key] = value

    allocation_policy = {
        "instances": [
            {
                "policy": {
                    "machineType": args.machine_type,
                    "bootDisk": {
                        "type": "pd-ssd",
                        "sizeGb": args.disk_size_gb
                    },
                    "provisioningModel": args.provisioning_model
                }
            }
        ]
    }

    if args.accelerator_count > 0:
        allocation_policy["instances"][0]["installGpuDrivers"] = True
        allocation_policy["instances"][0]["policy"]["accelerators"] = [
            {
                "type": args.accelerator_type,
                "count": args.accelerator_count
            }
        ]

    job_config = {
        "taskGroups": [
            {
                "name": "gpu-task-group",
                "taskSpec": {
                    "runnables": [
                        {
                            "container": {
                                "imageUri": args.image_uri,
                                "entrypoint": "/bin/bash",
                                "commands": [
                                    "-c",
                                    container_command
                                ],
                                "options": "--workdir /mnt/disks/share"
                            }
                        }
                    ],
                    "environment": {
                        "variables": environment_variables
                    },
                    "volumes": [
                        {
                            "gcs": {
                                "remotePath": args.remote_path
                            },
                            "mountPath": "/mnt/disks/share"
                        }
                    ],
                    "maxRetryCount": args.max_retry_count
                },
                "taskCount": 1
            }
        ],
        "allocationPolicy": allocation_policy,
        "logsPolicy": {
            "destination": "CLOUD_LOGGING"
        }
    }

    with open(args.output_file_path, 'w') as f:
        json.dump(job_config, f, indent=4)

    print(f"Successfully generated job configuration file at: {args.output_file_path}")

if __name__ == "__main__":
    main() 