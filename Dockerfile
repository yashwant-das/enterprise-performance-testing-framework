# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y build-essential curl

# Install system dependencies required for locust-plugins
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /usr/src/app
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the locustfiles directory into the container
COPY locustfiles/ /mnt/locust/

# The command to run locust is provided in the docker-compose.yml
# EXPOSE 8089 5557 5558
