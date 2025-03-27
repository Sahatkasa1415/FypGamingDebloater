import subprocess
import logging
import ctypes
import sys

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bloatware_remover.log'
)

def is_admin():
    """Check if the current process has admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logging.error(f"Error checking admin status: {e}")
        return False

def ensure_admin():
    """Ensure the application is running with admin privileges.
    
    Returns:
        bool: True if already admin or successfully restarted, False otherwise
    """
    if not is_admin():
        try:
            logging.info("Requesting admin privileges for operation")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return False  # Indicate we've restarted
        except Exception as e:
            logging.error(f"Failed to restart with admin privileges: {e}")
            return False
    return True  # Already admin

def run_powershell(cmd):
    """Run a PowerShell command and return success status and output.
    
    Args:
        cmd (str): PowerShell command to execute
        
    Returns:
        tuple: (success, output) where success is a boolean indicating if the command succeeded,
               and output is the command output or error message
    """
    try:
        # Run PowerShell with timeout to prevent hanging
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            capture_output=True, 
            text=True,
            timeout=120  # 2-minute timeout
        )
        
        # Log the command for debugging (but avoid logging huge outputs)
        logging.debug(f"Running PowerShell command: {cmd[:200]}...")
        
        if result.returncode != 0:
            error_message = result.stderr.strip() if result.stderr else "Unknown error"
            logging.error(f"Error running command: {cmd[:200]}...")
            logging.error(f"Error details: {error_message[:500]}")
            return False, error_message
        else:
            logging.info(f"Successfully ran command: {cmd[:200]}...")
            return True, result.stdout.strip()
    except subprocess.TimeoutExpired:
        logging.error(f"Command timed out after 120 seconds: {cmd[:200]}...")
        return False, "Command execution timed out after 120 seconds"
    except Exception as e:
        logging.error(f"Exception running PowerShell command: {str(e)}")
        return False, str(e)