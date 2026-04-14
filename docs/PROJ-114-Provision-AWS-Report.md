# EC2 Server Setup and Execution Report

## Overview
This report details the process of provisioning an Amazon EC2 instance, configuring the environment, troubleshooting networking and application binding issues, and successfully running the TRUST multi-process application (Flask + Hardhat).

## 1. AWS Infrastructure Setup

### Provisioning the Instance
- Launched a **t3.micro** EC2 instance running **Ubuntu 24.04 LTS**.
- Assigned a new key pair (`trust-key.pem`) for secure SSH access.

### Configuring the Security Group (Firewall)
By default, AWS blocks all traffic except SSH (Port 22). To allow external web traffic to reach the Flask application:
- Added an **Inbound Rule**:
  - **Type**: Custom TCP
  - **Port Range**: 8000
  - **Source**: Anywhere-IPv4 (`0.0.0.0/0`)

## 2. Server Environment Configuration

Once connected to the instance via SSH, the environment was prepared for both Python and Node.js dependencies.

```bash
# Update packages and install Python tools
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Install Node.js 22.x (Required for Hardhat)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

## 3. Application Setup & Troubleshooting

### Cloning and Branch Management
The application code was cloned to the server. Initially, the server was tracking the `main` branch which lacked the `host="0.0.0.0"` update. This caused the app to not accept connections.

**Fix applied:**
```bash
git fetch
git checkout <working-branch-name>
git pull origin <working-branch-name>
```

### Database Connection
A `.env` file was created in the root directory and populated with the Neon PostgreSQL database URL to prevent the application from freezing during the `run_sql_schema.py` initialization phase.

## 4. How to Start the Server

To launch the application manually, SSH into the EC2 instance and run the following commands:

```bash
# 1. Navigate to the project directory
cd trust

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Start the multi-process application (Hardhat + Flask)
python start_app.py
```

The application will compile the smart contracts, initialize the database, and start the Flask web server. It can then be accessed securely in a web browser using the EC2 instance's Public IPv4 address:

`http://<EC2-PUBLIC-IP>:8000`