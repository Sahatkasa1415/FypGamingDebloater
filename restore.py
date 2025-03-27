from powershell_utils import run_powershell
import logging
from datetime import datetime

# Setup logging if not already configured
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='bloatware_remover.log'
    )

def create_restore_point():
    """Create a system restore point before making changes."""
    print("Creating system restore point...")
    logging.info("Creating system restore point")
    
    date_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    description = f"Gaming Bloatware Remover - {date_string}"
    
    # Check if system restore is enabled
    check_cmd = "Get-ComputerRestorePoint"
    success, output = run_powershell(check_cmd)
    
    if not success or "failed" in output.lower():
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

def check_app_installed(app_name):
    """Check if an app is already installed on the system.
    
    Args:
        app_name (str): The name of the app to check
        
    Returns:
        bool: True if installed, False otherwise
    """
    ps_cmd = f"Get-AppxPackage -AllUsers *{app_name}*"
    success, output = run_powershell(ps_cmd)
    
    # If command was successful and returned non-empty output, app exists
    return success and len(output.strip()) > 0

def get_available_apps_for_reinstall():
    """Get a list of apps that can be reinstalled.
    
    Returns:
        dict: Dictionary with app_name as key and installed status as value
    """
    # Get app list from app_actions.py
    from app_actions import APPS
    
    available_apps = {}
    
    for app_name in APPS.keys():
        is_installed = check_app_installed(app_name)
        available_apps[app_name] = {
            "description": APPS[app_name]["description"] if "description" in APPS[app_name] else app_name,
            "installed": is_installed
        }
    
    return available_apps

def reinstall_selected_apps(app_list):
    """Reinstall selected apps.
    
    Args:
        app_list (list): List of app names to reinstall
        
    Returns:
        tuple: (success_count, failed_count)
    """
    if not app_list:
        print("No apps selected for reinstallation.")
        logging.info("No apps selected for reinstallation")
        return 0, 0
    
    print("Reinstalling selected apps...")
    logging.info(f"Starting reinstallation of selected apps: {', '.join(app_list)}")
    
    # Create a restore point before making changes
    create_restore_point()
    
    success_count = 0
    failed_count = 0
    
    for app_name in app_list:
        print(f"Attempting to reinstall {app_name}...")
        logging.info(f"Attempting to reinstall {app_name}")
        
        # Try various restoration methods
        # Method 1: Try to reinstall from the package
        ps_cmd = f"Get-AppxPackage -AllUsers *{app_name}* | Add-AppxPackage -Register \"$($_.InstallLocation)\\AppXManifest.xml\" -DisableDevelopmentMode -ErrorAction SilentlyContinue"
        success1, _ = run_powershell(ps_cmd)
        
        # Method 2: Try to reinstall from the provisioned source
        ps_cmd = f"Get-AppxProvisionedPackage -Online | Where-Object {{$_.DisplayName -like '*{app_name}*'}} | " + \
                 f"ForEach-Object {{Add-AppxProvisionedPackage -Online -PackagePath $_.PackagePath -SkipLicense -ErrorAction SilentlyContinue}}"
        success2, _ = run_powershell(ps_cmd)
        
        # Method 3: For Store apps, try to download from store
        ps_cmd = f"Add-AppxPackage -RegisterByFamilyName -MainPackage {app_name} -ErrorAction SilentlyContinue"
        success3, _ = run_powershell(ps_cmd)
        
        # Check if reinstall was successful
        is_installed = check_app_installed(app_name)
        
        if is_installed:
            print(f"Successfully reinstalled {app_name}")
            logging.info(f"Successfully reinstalled {app_name}")
            success_count += 1
        else:
            print(f"Failed to reinstall {app_name}")
            logging.warning(f"Failed to reinstall {app_name}")
            failed_count += 1
            
            # Try one last method - direct download from store
            print(f"Attempting store download for {app_name}...")
            ps_cmd = f"Add-AppxPackage -RegisterByFamilyName -MainPackage {app_name}"
            success, _ = run_powershell(ps_cmd)
            
            if success and check_app_installed(app_name):
                print(f"Successfully downloaded and installed {app_name} from store")
                logging.info(f"Successfully downloaded and installed {app_name} from store")
                success_count += 1
                failed_count -= 1  # Correct the count since we succeeded
    
    # Final results
    result_msg = f"Reinstallation complete. Successfully reinstalled {success_count} apps."
    if failed_count > 0:
        result_msg += f" Failed to reinstall {failed_count} apps."
        result_msg += " Some apps may need to be manually reinstalled from the Microsoft Store."
    
    print(result_msg)
    logging.info(result_msg)
    
    return success_count, failed_count

def restore_defaults():
    """Restore system defaults by reinstalling removed apps."""
    print("Restoring defaults to the system...")
    logging.info("Starting system defaults restoration")
    
    # Get app list from app_actions.py
    from app_actions import APPS
    
    # Step 1: Try to restore existing packages first (this is what your current code does)
    print("Attempting to restore existing packages...")
    ps_cmd1 = "Get-AppxPackage -AllUsers | Foreach {Add-AppxPackage -DisableDevelopmentMode -Register \"$($_.InstallLocation)\\AppXManifest.xml\" -ErrorAction SilentlyContinue}"
    run_powershell(ps_cmd1)
    
    # Step 2: Reinstall known apps from Windows Store
    print("\nAttempting to reinstall apps from Windows Store...")
    
    success_count = 0
    failed_count = 0
    
    for app_name in APPS.keys():
        print(f"Attempting to restore {app_name}...")
        
        # Try various restoration methods
        # Method 1: Try to get it from the store
        ps_cmd = f"Get-AppxPackage -AllUsers -Name *{app_name}* | Reset-AppxPackage -ErrorAction SilentlyContinue"
        success1, _ = run_powershell(ps_cmd)
        
        # Method 2: Try to reinstall from the provisioned source
        ps_cmd = f"Get-AppxProvisionedPackage -Online | Where-Object {{$_.DisplayName -like '*{app_name}*'}} | " + \
                 f"ForEach-Object {{Add-AppxProvisionedPackage -Online -PackagePath $_.PackagePath -SkipLicense -ErrorAction SilentlyContinue}}"
        success2, _ = run_powershell(ps_cmd)
        
        # Method 3: For Store apps, try to download from store
        ps_cmd = f"Add-AppxPackage -RegisterByFamilyName -MainPackage {app_name} -ErrorAction SilentlyContinue"
        success3, _ = run_powershell(ps_cmd)
        
        if success1 or success2 or success3:
            print(f"Successfully restored {app_name}")
            success_count += 1
        else:
            print(f"Failed to restore {app_name}")
            failed_count += 1
    
    # Step 3: Repair Windows Store if needed
    print("\nAttempting to repair Windows Store...")
    ps_cmd = "WSReset.exe"
    run_powershell(ps_cmd)
    
    # Final results
    result_msg = f"Restoration complete. Successfully restored {success_count} apps."
    if failed_count > 0:
        result_msg += f" Failed to restore {failed_count} apps."
        result_msg += " Some apps may need to be manually reinstalled from the Microsoft Store."
    
    print(result_msg)
    logging.info(result_msg)
    
    return success_count > 0

def uninstall_onedrive():
    """Uninstall OneDrive and clean up residual files."""
    print("Uninstalling OneDrive...")
    logging.info("Starting OneDrive uninstallation")
    
    # Stop OneDrive processes
    run_powershell("Stop-Process -Name OneDrive* -Force -ErrorAction SilentlyContinue")
    
    # Run the OneDrive uninstaller
    commands = [
        # Find OneDrive setup executable
        "$onedrive = \"$env:SYSTEMROOT\\SysWOW64\\OneDriveSetup.exe\"",
        "if (!(Test-Path $onedrive)) { $onedrive = \"$env:SYSTEMROOT\\System32\\OneDriveSetup.exe\" }",
        # Run the uninstaller
        "if (Test-Path $onedrive) { Start-Process $onedrive -ArgumentList \"/uninstall\" -Wait }",
        # Clean up additional files
        "Remove-Item -Path \"$env:USERPROFILE\\OneDrive\" -Force -Recurse -ErrorAction SilentlyContinue",
        "Remove-Item -Path \"$env:LOCALAPPDATA\\Microsoft\\OneDrive\" -Force -Recurse -ErrorAction SilentlyContinue",
        "Remove-Item -Path \"$env:PROGRAMDATA\\Microsoft OneDrive\" -Force -Recurse -ErrorAction SilentlyContinue",
        # Disable OneDrive via registry
        "if (!(Test-Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\OneDrive')) { New-Item -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\OneDrive' -Force }",
        "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\OneDrive' -Name 'DisableFileSyncNGSC' -Value 1 -Type DWord -Force"
    ]
    
    # Execute all commands in a single PowerShell session
    ps_script = "; ".join(commands)
    success, output = run_powershell(ps_script)
    
    if success:
        print("OneDrive uninstalled successfully.")
        logging.info("OneDrive uninstalled successfully")
    else:
        print("Failed to completely uninstall OneDrive.")
        logging.error(f"OneDrive uninstallation error: {output}")
    
    return success