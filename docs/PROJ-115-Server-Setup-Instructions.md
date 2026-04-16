# Production Server Setup Guide

This guide details how to transition the TRUST application from the local development server to a continuous production setup on AWS EC2 using `systemd` and `Gunicorn`.

## 1. Prerequisites

Before configuring the services, ensure your AWS EC2 instance is fully provisioned with Python, Node.js, and the `.env` file containing your `DATABASE_URL`.

You also need to install **Gunicorn**, the production WSGI server, inside your virtual environment.

```bash
cd /home/ubuntu/trust
source .venv/bin/activate
pip install gunicorn
```

## 2. Setting Up systemd Services

We will use `systemd` to keep the background Hardhat node and the Flask web application running continuously. Two service configuration files are already provided in the repository's `services` directory:

- `trust-hardhat.service`: Manages the local blockchain node.
- `trust-web.service`: Manages the Gunicorn web server, handles deployment delays, and initializes the database.

### Copy the Service Files

Copy both configuration files into the systemd directory:

```bash
sudo cp /home/ubuntu/trust/docs/trust-hardhat.service /etc/systemd/system/hardhat.service
sudo cp /home/ubuntu/trust/docs/trust-web.service /etc/systemd/system/trust-web.service
```

*Note: The `trust-web.service` file explicitly requires `hardhat.service` to be running. It also executes pre-start commands to compile/deploy the factory contract, wipe and reset the database, and bind Gunicorn to port `8000` with 4 workers.*

## 3. Enable and Start the Application

With the service files in place, reload `systemd` so it recognizes them:

```bash
sudo systemctl daemon-reload
```

Enable both services to start automatically if the server reboots:

```bash
sudo systemctl enable hardhat.service
sudo systemctl enable trust-web.service
```

Start the web service. Because it explicitly requires the Hardhat node, `systemd` will automatically start Hardhat first:

```bash
sudo systemctl start trust-web.service
```

## 4. Verification and Troubleshooting

You can verify the status of the processes at any time:
```bash
sudo systemctl status hardhat.service
sudo systemctl status trust-web.service
```

If you need to view live logs (for example, to see Flask application errors or Hardhat RPC requests):
```bash
# View Hardhat node logs
sudo journalctl -u hardhat.service -f

# View Flask/Gunicorn logs
sudo journalctl -u trust-web.service -f
```
