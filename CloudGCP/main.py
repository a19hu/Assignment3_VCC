import time
import psutil
from google.cloud import compute_v1
import subprocess
import docker
from dotenv import load_dotenv
import os

NGINX_BACKEND_FILE = "../nginx/backend_servers.conf"
client = docker.from_env()
instance_client = compute_v1.InstancesClient()

load_dotenv()

# GCP Configuration
PROJECT_ID = os.getenv("PROJECT_ID")
ZONE = os.getenv("ZONE")
VM_NAME = os.getenv("VM_NAME")
MACHINE_TYPE = os.getenv("MACHINE_TYPE")
IMAGE_FAMILY = os.getenv("IMAGE_FAMILY")
IMAGE_PROJECT = os.getenv("IMAGE_PROJECT")
DOCKER_IMAGE = os.getenv("DOCKER_USERNAME")+"/flask-app:latest"

# Function to check system resource usage
def check_usage(threshold=3):
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent

    print(f"CPU Usage: {cpu_usage}% | Memory Usage: {memory_usage}%")

    return cpu_usage > threshold or memory_usage > threshold

# Function to create a new VM
def create_vm():

    # VM configuration
    instance = compute_v1.Instance()
    instance.name = VM_NAME
    instance.zone = ZONE
    instance.machine_type = f"zones/{ZONE}/machineTypes/{MACHINE_TYPE}"

    # Disk configuration
    disk = compute_v1.AttachedDisk()
    disk.auto_delete = True
    disk.boot = True
    disk.initialize_params.source_image = f"projects/{IMAGE_PROJECT}/global/images/family/{IMAGE_FAMILY}"
    instance.disks = [disk]

    # Network configuration
    network_interface = compute_v1.NetworkInterface()
    network_interface.name = "global/networks/default"
    instance.network_interfaces = [network_interface]

    operation = instance_client.insert(project=PROJECT_ID, zone=ZONE, instance_resource=instance)
    print(f"VM creation initiated: {operation.name}")

    
# Function to get external IP of the VM
def get_vm_external_ip():
    instance = instance_client.get(project=PROJECT_ID, zone=ZONE, instance=VM_NAME)
    
    try:
        return instance.network_interfaces[0].network_i_p
    except IndexError:
        return "No external IP found."

# Function to delete an existing VM
def delete_vm():
        operation = instance_client.delete(project=PROJECT_ID, zone=ZONE, instance=VM_NAME)
        print(f"VM deletion initiated: {operation.name}")
        return operation.name

# Function to check if a VM already exists
def vm_exists():
    try:
        instance_client.get(project=PROJECT_ID, zone=ZONE, instance=VM_NAME)
        return True
    except Exception:
        return False

def update_nginx_config(vm_ip,new_port):
    with open(NGINX_BACKEND_FILE, "w") as f:
        f.write(f"server {vm_ip}:{new_port};\n")
    client.containers.get("nginx-lb").restart()
    print("Nginx configuration updated.")

def deploy_docker_app(vm_ip):
    print("Deploying application on the VM...")
    try:

        ssh_command = f"""
        gcloud compute ssh {VM_NAME} --zone={ZONE} --project={PROJECT_ID} --command="
        sudo apt-get update -y &&
        sudo apt-get upgrade -y &&
        curl -fsSL https://get.docker.com -o get-docker.sh &&
        sudo sh get-docker.sh &&
        sudo docker ps
        "
        """
        os.system(ssh_command)
        print(f"Application deployed on VM {VM_NAME} at {vm_ip}")
    except Exception as e:
        print(f"Error deploying application: {e}")

# Auto-scale logic
def loop():
    while True:
        if check_usage() and not vm_exists():
            print("Creating a new VM...")
            create_vm()
            vm_ip = get_vm_external_ip()
            print(f"VM created with external IP: {vm_ip}")
            update_nginx_config(vm_ip, 5000)
            deploy_docker_app(vm_ip)
        elif not check_usage() and vm_exists():
            print("CPU usage is normal. Skipping VM creation.")
            delete_vm()
        else:
            print("CPU usage is high but VM already exists. Skipping VM creation.")

if __name__ == "__main__":
    # if vm_exists():
    #     print(f"Deleting existing VM '{VM_NAME}'...")
    #     delete_vm()
    #     time.sleep(90)
    #     loop()
    # else:
    #     loop()
    vm_ip = get_vm_external_ip()
    deploy_docker_app(vm_ip)