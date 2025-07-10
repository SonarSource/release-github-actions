# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file from the root of the action repo
COPY ../../../tools/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire tools directory into the container
COPY ../../../tools/ .

# Specify the entrypoint for the container.
ENTRYPOINT ["python", "/app/create_release_ticket_for_action.py"]
