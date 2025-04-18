import subprocess
import logging
import ctypes
import sys
import os

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bloatware_remover.log'
)

def is_admin():
    """Check if the current process has admin privileges."""
    try:
        # Make sure we return a proper boolean value
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
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
            # Get the full path to the executable
            if getattr(sys, 'frozen', False):
                # If the application is frozen (compiled)
                application_path = sys.executable
            else:
                # If running from script
                application_path = os.path.abspath(sys.argv[0])
            
            # Execute with admin privileges
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", application_path, " ".join(sys.argv[1:]), None, 1
            )
            return False  # Indicate we've restarted
        except Exception as e:
            logging.error(f"Failed to restart with admin privileges: {e}")
            return False
    return True  # Already admin

def run_powershell(cmd, timeout=120, silent=True):
    """Run a PowerShell command and return success status and output.
    
    Args:
        cmd (str): PowerShell command to execute
        timeout (int): Timeout in seconds
        silent (bool): Whether to hide the PowerShell window
        
    Returns:
        tuple: (success, output) where success is a boolean indicating if the command succeeded,
               and output is the command output or error message
    """
    try:
        # Build PowerShell arguments
        powershell_args = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command", cmd
        ]
        
        # Creation flags to hide window if silent is True
        creation_flags = subprocess.CREATE_NO_WINDOW if silent and os.name == 'nt' else 0
        
        # Log a sanitized version of the command for debugging
        cmd_preview = (cmd[:100] + '...') if len(cmd) > 100 else cmd
        logging.debug(f"Running PowerShell command: {cmd_preview}")
        
        # Run the command
        result = subprocess.run(
            powershell_args,
            capture_output=True, 
            text=True,
            timeout=timeout,
            creationflags=creation_flags
        )
        
        # Check for errors
        if result.returncode != 0:
            error_message = result.stderr.strip() if result.stderr else f"Unknown error (return code {result.returncode})"
            logging.error(f"Error running command: {cmd_preview}")
            logging.error(f"Error details: {error_message}")
            return False, error_message
        else:
            # For successful commands, log the command but not necessarily all output
            output_preview = (result.stdout[:100] + '...') if len(result.stdout) > 100 else result.stdout
            logging.info(f"Successfully ran command: {cmd_preview}")
            if output_preview.strip():
                logging.debug(f"Command output: {output_preview}")
            return True, result.stdout.strip()
    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds"
        logging.error(f"{error_msg}: {cmd_preview}")
        return False, error_msg
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Exception running PowerShell command: {error_msg}")
        return False, error_msg

def run_batch_app_check(app_names, timeout=180):
    """Run a batch check of multiple apps in a single PowerShell process.
    
    Args:
        app_names (list): List of app names to check
        timeout (int): Timeout in seconds
        
    Returns:
        dict: Dictionary with app_name as key and installed status as value
    """
    try:
        # Build PowerShell command to check all apps at once
        ps_commands = []
        
        for app_name in app_names:
            # Format a command that outputs app name and status
            # Use a more precise check that ensures we match the exact app name
            ps_commands.append(
                f"Write-Output '{app_name}---START---';"
                f"$pkg = Get-AppxPackage -AllUsers | Where-Object {{$_.Name -eq '{app_name}' -or $_.PackageFullName -eq '{app_name}'}};"
                f"if ($pkg) {{ "
                f"Write-Output 'INSTALLED' }} else {{ "
                f"Write-Output 'NOT_INSTALLED' }};"
                f"Write-Output '---END---';"
            )
        
        # Join all commands and run as a single PowerShell process
        full_command = " ".join(ps_commands)
        success, output = run_powershell(full_command, timeout=timeout)
        
        # Parse the results
        results = {}
        if success:
            lines = output.strip().split('\n')
            current_app = None
            
            for line in lines:
                line = line.strip()
                if '---START---' in line:
                    current_app = line.split('---START---')[0]
                elif line == 'INSTALLED' and current_app:
                    results[current_app] = True
                elif line == 'NOT_INSTALLED' and current_app:
                    results[current_app] = False
                elif line == '---END---':
                    current_app = None
                    
            # Make sure we have a result for each app
            for app_name in app_names:
                if app_name not in results:
                    results[app_name] = False
        
        return results
    except Exception as e:
        logging.error(f"Error in batch app check: {str(e)}")
        return {}