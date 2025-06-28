import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Build a local Docker run command for a job.")

    # Required arguments
    parser.add_argument("--local_bucket_dir", required=True, help="Local directory to mount (replaces GCS bucket).")
    parser.add_argument("--image_uri", required=True, help="The Docker image URI (e.g., \"gcr.io/relman-yaffe/evo2\").")
    parser.add_argument("--job_env", required=True, help="Value for the JOB environment variable.")
    parser.add_argument("--run_script_path", required=True, help="Path to the execution script within the container (e.g., \"scripts/run_job.sh\").")

    # Optional arguments
    parser.add_argument("--accelerator_count", type=int, default=0, help="The number of accelerators.")
    parser.add_argument("--user_parameters", required=True, help="User-defined parameters.")
    parser.add_argument("--output_file", help="Optional file to write the command to.")

    args = parser.parse_args()

    # construct the command for the container
    container_command = f"bash /mnt/disks/share/{args.run_script_path}"

    # build environment variables
    env_vars = []
    env_vars.append("-e MNT_DIR=/mnt/disks/share")
    env_vars.append(f"-e JOB={args.job_env}")
    
    # add CUDA_VISIBLE_DEVICES if accelerators are used
    if args.accelerator_count > 0:
        cuda_visible_devices = ",".join(map(str, range(args.accelerator_count)))
        env_vars.append(f"-e CUDA_VISIBLE_DEVICES={cuda_visible_devices}")
    
    # parse user parameters
    if args.user_parameters:
        for param in args.user_parameters.split():
            if '=' in param:
                key, value = param.split('=', 1)
                env_vars.append(f"-e {key}={value}")

    # build docker run command
    docker_options = []
    docker_options.append("-it --rm")
    docker_options.append(f"-v {os.path.abspath(args.local_bucket_dir)}:/mnt/disks/share")
    
    # add GPU support if accelerators are requested
    if args.accelerator_count > 0:
        docker_options.append("--gpus all")
    
    docker_options.extend(env_vars)
    docker_options.append(f'--workdir /mnt/disks/share')
    
    docker_cmd = f"docker run {' '.join(docker_options)} {args.image_uri} {container_command}"
    
    print("Local Docker run command:")
    print(docker_cmd)
    
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(f"#!/bin/bash\n")
            f.write(f"# Generated local Docker run command\n")
            f.write(f"{docker_cmd}\n")
        os.chmod(args.output_file, 0o755)
        print(f"\nCommand written to executable script: {args.output_file}")

if __name__ == "__main__":
    main() 