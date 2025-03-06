import subprocess
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bloatware_remover.log'
)

def run_powershell(cmd):
    """Run a PowerShell command and return success status and output.
    
    Args:
        cmd (str): PowerShell command to execute
        
    Returns:
        tuple: (success, output) where success is a boolean indicating if the command succeeded,
               and output is the command output or error message
    """
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", cmd],
            capture_output=True, 
            text=True
        )
        
        # Log the command for debugging
        logging.debug(f"Running PowerShell command: {cmd}")
        
        if result.returncode != 0:
            logging.error(f"Error running command: {cmd}")
            logging.error(f"Error details: {result.stderr}")
            return False, result.stderr
        else:
            logging.info(f"Successfully ran command: {cmd}")
            logging.debug(f"Command output: {result.stdout}")
            return True, result.stdout
    except Exception as e:
        logging.error(f"Exception running PowerShell command: {e}")
        return False, str(e)