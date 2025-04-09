# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies and Google Cloud SDK
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    lsb-release && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && apt-get install -y google-cloud-sdk && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# # Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY main.py .
COPY .env .


# Expose the port the app runs on
EXPOSE 5002

# Set the command to run the application
# CMD ["python", "main.py"]