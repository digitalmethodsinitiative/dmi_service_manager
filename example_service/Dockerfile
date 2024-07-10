# Basic python environment
FROM python:3.8-slim
# GPU nvidia environment
#FROM nvidia/cuda:12.1.1-devel-ubuntu20.04

RUN apt-get update && apt install -y \
    # General requirements:
    libpq-dev \
    python3-dev \
    python3-pip \
    git \
    wget

# Set working directory
WORKDIR /app/

# Copy entire project
COPY . /app/
# Copy only certain files
#COPY docker-entrypoint.sh /app/
#COPY requirements.txt /app/

RUN pip3 install -r requirements.txt

# Ensure that the script is executable
RUN chmod +x docker-entrypoint.sh

# Set default command when container runs
CMD ["./docker-entrypoint.sh"]
