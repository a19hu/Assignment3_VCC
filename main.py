import time
import psutil
from google.cloud import compute_v1
import subprocess
import docker
from dotenv import load_dotenv
import os

NGINX_BACKEND_FILE = "./nginx/backend_servers.conf"
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

def check_usage(threshold=3):
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    print(f"CPU Usage: {cpu_usage}% | Memory Usage: {memory_usage}%")
    return cpu_usage > threshold or memory_usage > threshold

def create_vm():
    try:
        command = [
            "gcloud", "compute", "instances", "create", VM_NAME,
            f"--project={PROJECT_ID}",
            f"--zone={ZONE}",
            f"--machine-type={MACHINE_TYPE}",
            f"--image-family={IMAGE_FAMILY}",
            f"--image-project={IMAGE_PROJECT}",
            "--network=default",
            "--subnet=default",
            "--tags=http-server,https-server",
            "--boot-disk-size=10GB",
            "--boot-disk-type=pd-standard"
        ]
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error creating VM: {e}")

    
def get_vm_external_ip():
    instance = instance_client.get(project=PROJECT_ID, zone=ZONE, instance=VM_NAME)

    try:
        return instance.network_interfaces[0].access_configs[0].nat_i_p
    except IndexError:
        return "No external IP found."

def enable_firewall_rule():
    try:
        check_command = [
            "gcloud", "compute", "firewall-rules", "describe", "allow-port-5000",
            f"--project={PROJECT_ID}"
        ]
        subprocess.run(check_command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        try:
            command = [
                "gcloud", "compute", "firewall-rules", "create", "allow-port-5000",
                f"--project={PROJECT_ID}",
                "--direction=INGRESS",
                "--priority=1000",
                "--network=default",
                "--action=ALLOW",
                "--rules=tcp:5000",
                "--source-ranges=0.0.0.0/0",
                "--target-tags=http-server,https-server"
            ]
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error creating firewall rule: {e}")

def delete_vm():
    operation = instance_client.delete(project=PROJECT_ID, zone=ZONE, instance=VM_NAME)
    print(f"VM deletion initiated: {operation.name}")
    return operation.name

def vm_exists():
    try:
        instance_client.get(project=PROJECT_ID, zone=ZONE, instance=VM_NAME)
        return True
    except Exception:
        return False

def update_nginx_config(vm_ip,new_port):
    print("Updating NGINX configuration...")
    with open(NGINX_BACKEND_FILE, "w") as f:
        f.write(f"server {vm_ip}:{new_port};\n")
    client.containers.get("nginx-lb").restart()

def deploy_docker_app(vm_ip):
    print("Deploying application on the VM...")
    try:
        ssh_command = f"""
        gcloud compute ssh {VM_NAME} --zone={ZONE} --project={PROJECT_ID} --command="sudo bash -c '
        echo Updating the system... &&
        sudo apt-get update -y &&
        echo Installing Docker... &&
        sudo apt install docker.io -y &&
        sudo systemctl start docker &&
        sudo systemctl enable docker &&
        echo Pulling Docker image... &&
        sudo docker pull {DOCKER_IMAGE} &&
        echo Running Docker container... &&
        sudo docker run -d -p 5000:5000 -e APP_NAME=GCP_VM {DOCKER_IMAGE} &&
        echo Docker container running... &&
        echo Listing Docker containers... &&
        sudo docker ps
        '"
        """
        os.system(ssh_command)
    except Exception as e:
        print(f"Error deploying application: {e}")

def loop():
    while True:
        if check_usage() and not vm_exists():
            print("Creating a new VM...")
            create_vm()
            vm_ip = get_vm_external_ip()
            enable_firewall_rule()
            time.sleep(30)
            deploy_docker_app(vm_ip)
            update_nginx_config(vm_ip, 5000)
            print("Your application is running: http://localhost:5000 and http://"+vm_ip+":5000")
        elif not check_usage() and vm_exists():
            delete_vm()
            time.sleep(90)
            print("your application is running only on http://localhost:5000")
        elif check_usage() and vm_exists():
            vm_ip = get_vm_external_ip()
            print("your application is running on http://localhost:5000 and http://"+vm_ip+":5000")            


if __name__ == "__main__":
    if vm_exists():
        print(f"Deleting existing VM '{VM_NAME}'...")
        delete_vm()
        time.sleep(90)
        loop()
    else:
        loop()

