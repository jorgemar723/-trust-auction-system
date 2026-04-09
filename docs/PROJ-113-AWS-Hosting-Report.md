
# AWS Hosting & Deployment Research Report

  

**Jira Task:** Currently, TRUST relies on a Flask web server and a locally running Hardhat blockchain node. We need to evaluate the best AWS services to host this multi-process setup, as well as store auction images. Also, we need to research how to use a process manager (such as systemd, pm2, or supervisor) to run the app continuously, as well as Gunicorn, which is a production-grade WSGI server that serves the Flask application instead of the built-in development server.

  

## App Hosting Options

  

### Possible AWS Services

-  **AWS App Runner:** A fully managed service that makes it easy to deploy containerized web applications and APIs.

-  **AWS Elastic Beanstalk:** An easy-to-use service for deploying and scaling web applications developed with Java, .NET, PHP, Node.js, Python, Ruby, Go, and Docker.

-  **AWS Lambda (with API Gateway):** A serverless compute service that lets you run code without provisioning or managing servers.

-  **Amazon EC2 (Elastic Compute Cloud):** Provides scalable computing capacity in the AWS Cloud, essentially offering virtual servers where you can run any software.

  

### Chosen Service: Amazon EC2

**Why EC2?**

While AWS App Runner is a fantastic tool for containerized applications, it does not offer a free tier and can become costly just running idle. Additionally, our application currently relies on a multi-process setup (running a local Hardhat blockchain node in the background alongside the Flask web server). Serverless options like AWS Lambda or App Runner are designed for stateless web requests and will shut down background processes once the request is fulfilled. By using a free-tier eligible EC2 instance, we can continuously run both the Hardhat node and the Flask application 24/7 without unexpected problems.

  

## Image Storage Options

  

### Possible AWS Services

-  **Amazon S3 (Simple Storage Service):** An object storage service that offers industry-leading scalability, data availability, security, and performance.

-  **Amazon EBS (Elastic Block Store):** Provides block level storage volumes for use with EC2 instances.

-  **Amazon EFS (Elastic File System):** A simple, serverless, set-and-forget elastic file system for AWS compute services.

  

### Chosen Service: Amazon S3

**Why S3?**

We are choosing Amazon S3 for storing auction images. Currently, images are saved locally to the Flask app's static upload folder. On a cloud server, storing user-uploaded media on the local disk (EBS) is a bad practice because if the server goes down or needs to scale, the files could be lost. S3 provides a dedicated, highly durable, and inexpensive object storage solution. We can upload the images directly to an S3 bucket and save their public URLs in our database, offloading the storage and bandwidth overhead from our main EC2 instance.

  

## Process Management

  

### Chosen Process Manager: systemd

To run our application continuously, we will use **systemd**.

  

**How it works with the app:**

`systemd` is the default service and system manager for modern Linux distributions (including Ubuntu, which we will use on our EC2 instance). Instead of running `start_app.py` in a terminal where it could crash and stay dead, we will create `systemd` service files for both our Hardhat node and our Flask application. `systemd` will automatically start these processes when the server boots, run them continuously in the background and automatically restart them if they crash.

  

## Production-Grade Web Server

  

### What is Gunicorn?

Gunicorn (Green Unicorn) is a Python WSGI (Web Server Gateway Interface) HTTP server for UNIX. It is a pre-fork worker model that acts as the interface between the web server and your Python web application.

  

### How we will use Gunicorn

Currently, we are running our Flask application using its built-in development server (`app.run(debug=True)`). The Flask documentation explicitly states that this built-in server is not designed for production use, as it scales poorly and is not secure.

  

We will use Gunicorn to serve our Flask application. Gunicorn will spin up multiple worker processes to handle concurrent incoming requests efficiently. Instead of directly executing `flask_app.py` directly through Python, our `systemd` service will launch Gunicorn, point it to our Flask `app` object, and bind it to the appropriate port to handle live traffic securely and robustly.