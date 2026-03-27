import subprocess
import time
import os
import sys
import atexit

def get_venv_python():
    """Returns the correct path to the venv Python executable based on the OS."""
    if sys.platform == "win32":
        return os.path.join(".venv", "Scripts", "python.exe")
    return os.path.join(".venv", "bin", "python")

def get_npx_cmd():
    """Returns the correct npx command based on the OS."""
    return "npx.cmd" if sys.platform == "win32" else "npx"

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    hardhat_dir = os.path.join(base_dir, "Hardhat testing Node")
    venv_python = os.path.join(base_dir, get_venv_python())
    npx_cmd = get_npx_cmd()

    if not os.path.exists(venv_python):
        print(f"Error: Could not find virtual environment Python at {venv_python}")
        print("Please ensure your venv is created and located at the 'venv' directory.")
        sys.exit(1)

    print("=> Starting Hardhat local node...")
    # Start Hardhat node as a background process
    hardhat_node = subprocess.Popen(
        [npx_cmd, "hardhat", "node"],
        cwd=hardhat_dir
    )

    def cleanup():
        print("\n=> Shutting down background processes...")
        if hardhat_node.poll() is None:
            hardhat_node.terminate()
            hardhat_node.wait()

    # Ensure the node gets cleaned up when the script exits
    atexit.register(cleanup)

    # Give the node a few seconds to spin up and be ready for RPC connections
    print("=> Waiting for Hardhat node to initialize (5 seconds)...")
    time.sleep(5)

    print("=> Deploying factory contract...")
    # Run the deployment script and wait for it to finish
    deploy_process = subprocess.Popen(
        [npx_cmd, "hardhat", "run", "scripts/deploy_factory.js", "--network", "localhost"],
        cwd=hardhat_dir
    )
    deploy_process.wait()

    if deploy_process.returncode != 0:
        print("=> Error: Deployment failed. Exiting.")
        sys.exit(1)

    print("=> Re-initializing database to prevent stale contract address conflicts...")
    # This will wipe the DB and apply the schema, fixing the duplicate key issue on restart
    init_db_process = subprocess.Popen(
        [venv_python, os.path.join("db", "run_sql_schema.py")],
        cwd=base_dir
    )
    init_db_process.wait()

    if init_db_process.returncode != 0:
        print("=> Error: Database initialization failed. Exiting.")
        sys.exit(1)

    print("=> Starting Flask app...")
    # Start the Flask app using the virtual environment's Python
    flask_process = subprocess.Popen(
        [venv_python, "flask_app.py"],
        cwd=base_dir
    )

    try:
        # Keep the main script alive and wait for Flask to finish
        flask_process.wait()
    except KeyboardInterrupt:
        print("\n=> Received interrupt signal. Stopping Flask app...")
        flask_process.terminate()
        flask_process.wait()

if __name__ == "__main__":
    main()
