# Use the official Ubuntu base image
FROM ubuntu:latest

# Install updates and basic utilities
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set default command
CMD ["bash"]
