# Cloud-based Auto-scaling Flask Application

This project implements a cloud-based auto-scaling system for a Flask web application. It uses Google Cloud Platform (GCP) to automatically deploy additional instances when the local system resources exceed defined thresholds.

## Features

- Automatic VM creation in GCP when local system resources are overloaded
- Load balancing using Nginx
- Monitoring with Prometheus and Grafana
- Docker containerization for consistent deployment
- Auto-scaling based on CPU and memory usage

## Prerequisites

- Google Cloud Platform account
- Google Cloud SDK (gcloud CLI)
- Docker and Docker Compose
- Python 3.9+
- Git

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/a19hu/assignemt_vcc.git
cd assignemt_vcc
```

### 2. Set Up Google Cloud Platform

#### Install Google Cloud SDK

Follow the instructions for your operating system:
https://cloud.google.com/sdk/docs/install

#### Initialize Google Cloud SDK

```bash
gcloud init
```

#### Create a GCP Project

```bash
gcloud projects create PROJECT_ID
```

Replace `PROJECT_ID` with your desired project ID (e.g., `vcca19hu`).

#### List Available Projects

```bash
gcloud projects list
```

#### Set the Current Project

```bash
gcloud config set project PROJECT_ID
```

#### Enable the Compute Engine API

```bash
gcloud services enable compute.googleapis.com --project=PROJECT_ID
```

### 3. Configure Environment Variables

Create a `.env` file based on the provided `.env.example`:

```bash
cp .env.example .env
```

Edit the `.env` file with your specific configuration:

```
PROJECT_ID=your_project_id
ZONE=us-central1-f
VM_NAME=autoscaled-vm1
MACHINE_TYPE=e2-medium
IMAGE_FAMILY=debian-11
IMAGE_PROJECT=debian-cloud
DOCKER_USERNAME=your_docker_username
APP_NAME=your_app_name
```

### 4. Build and Run the Application

Build and start all services using Docker Compose:

```bash
docker compose up --build
```

This will start:
- The Flask application container
- Nginx load balancer
- Prometheus for metrics collection
- Grafana for visualization

### 5. Start the Auto-scaling Controller

In a separate terminal, run the main Python script:

```bash
python3 main.py
```

This script monitors system resources and automatically creates/deletes GCP VM instances based on load.

## How It Works

1. The main application continuously monitors local CPU and memory usage
2. When usage exceeds a threshold (default: 3%), it creates a VM in GCP
3. The Flask application is deployed to the VM using Docker
4. Nginx is updated to include the VM in its load balancing
5. When the load decreases, the VM is automatically terminated

## Accessing the Services

- Flask Application: http://localhost:5000
- Nginx Load Balancer: http://localhost:80
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

## Project Structure

- `api/`: Contains the Flask application code
- `nginx/`: Nginx configuration files
- `monitoring/`: Prometheus configuration
- `grafana/`: Grafana dashboards and configuration
- `main.py`: Auto-scaling controller script
- `Dockerfile`: For building the controller container
- `docker-compose.yml`: Defines all services
- `requirements.txt`: Python dependencies

## Troubleshooting

If you encounter issues with GCP authentication, ensure you're properly authenticated:

```bash
gcloud auth login
gcloud auth application-default login
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.


