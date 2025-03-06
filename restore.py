from powershell_utils import run_powershell
import logging
import os
from datetime import datetime

# Setup logging if not already configured
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='bloatware_remover.log'
    )

def create_restore_point():
    """Create a system restore point before making changes.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("Creating system restore point...")
    logging.info("Creating system restore point")
    
    date_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    description = f"Gaming Bloatware Remover - {date_string}"
    
    # Enable System Restore if not already enabled
    ps_cmd_enable = "Enable-ComputerRestore -Drive \"C:\\\""
    success, output = run_powershell(ps_cmd_enable)
    
    if not success:
        print("Warning: Could not enable system restore")
        logging.warning(f"Could not enable system restore: {output}")
    
    # Create the restore point
    ps_cmd = f"Checkpoint-Computer -Description \"{description}\" -RestorePointType \"APPLICATION_UNINSTALL\""
    success, output = run_powershell(ps_cmd)
    
    if success:
        print("System restore point created successfully")
        logging.info("System restore point created successfully")
        return True
    else:
        print("Warning: Could not create system restore point")
        logging.warning(f"Could not create system restore point: {output}")
        return False

def restore_app(app_name):
    """Try to restore a specific app that was removed.
    
    Args:
        app_name (str): The name of the app to restore
        
    Returns:
        bool: True if the restoration was successful, False otherwise
    """
    print(f"Attempting to restore {app_name}...")
    logging.info(f"Attempting to restore {app_name}")
    
    # Check if the app is already installed
    check_cmd = f"Get-AppxPackage -AllUsers *{app_name}*"
    success, output = run_powershell(check_cmd)
    
    if success and output.strip():
        print(f"{app_name} is already installed.")
        logging.info(f"{app_name} is already installed")
        return True
    
    # Try to restore the app from the Windows store
    ps_cmd = f"Get-AppxPackage -AllUsers *{app_name}* | Add-AppxPackage -DisableDevelopmentMode -Register \"$($_.InstallLocation)\\AppXManifest.xml\""
    success, output = run_powershell(ps_cmd)
    
    if success:
        print(f"Successfully restored {app_name}")
        logging.info(f"Successfully restored {app_name}")
        return True
    else:
        # If the above doesn't work, try another approach
        ps_cmd2 = f"Add-AppxPackage -RegisterByFamilyName -MainPackage {app_name}"
        success2, output2 = run_powershell(ps_cmd2)
        
        if success2:
            print(f"Successfully restored {app_name}")
            logging.info(f"Successfully restored {app_name}")
            return True
        else:
            print(f"Failed to restore {app_name}")
            logging.error(f"Failed to restore {app_name}: {output}, {output2}")
            return False

def restore_defaults():
    """Restore system defaults. Creates a restore point first and then tries to reinstall built-in apps."""
    print("Restoring defaults to the system...")
    logging.info("Starting system defaults restoration")
    
    # First create a restore point
    create_restore_point()
    
    # Use a more targeted approach rather than trying to reinstall everything
    from app_actions import APPS
    
    successful_restores = 0
    failed_restores = 0
    
    for app_name in APPS.keys():
        if restore_app(app_name):
            successful_restores += 1
        else:
            failed_restores += 1
    
    result_msg = f"Restoration complete. Successfully restored {successful_restores} apps."
    if failed_restores > 0:
        result_msg += f" Failed to restore {failed_restores} apps."
    
    print(result_msg)
    logging.info(result_msg)
    return successful_restores > 0