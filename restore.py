from powershell_utils import run_powershell, ensure_admin
import logging
from datetime import datetime
import time

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
    try:
        print("Creating system restore point...")
        logging.info("Creating system restore point")
        
        # Check for admin privileges
        if not ensure_admin():
            print("System restore requires administrator privileges. Please run the application as administrator.")
            logging.warning("System restore requires administrator privileges")
            return False
        
        date_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        description = f"Gaming Bloatware Remover - {date_string}"
        
        # Check if system restore service is running
        ps_cmd_check = "Get-Service -Name SRSERVICE | Select-Object -ExpandProperty Status"
        success, output = run_powershell(ps_cmd_check)
        
        if not success or "Running" not in output:
            # Try to enable the System Restore service
            print("System Restore service not running. Attempting to enable it...")
            ps_cmd_enable_service = "Set-Service -Name SRSERVICE -StartupType Manual; Start-Service -Name SRSERVICE -ErrorAction SilentlyContinue"
            run_powershell(ps_cmd_enable_service)
            
            # Give it a moment to start
            time.sleep(2)
        
        # Enable System Restore on C drive
        ps_cmd_enable = "Enable-ComputerRestore -Drive \"C:\\\" -ErrorAction SilentlyContinue"
        success, output = run_powershell(ps_cmd_enable)
        
        if not success and "Access denied" in output:
            print("Warning: Could not enable system restore (access denied). Ensure you're running as administrator.")
            logging.warning(f"Could not enable system restore: {output}")
            return False
        
        # Create the restore point
        ps_cmd = f"Checkpoint-Computer -Description \"{description}\" -RestorePointType \"APPLICATION_UNINSTALL\" -ErrorAction SilentlyContinue"
        success, output = run_powershell(ps_cmd)
        
        if success:
            print("System restore point created successfully")
            logging.info("System restore point created successfully")
            return True
        else:
            reason = "Unknown error"
            if "Access denied" in output:
                reason = "Access denied - run as administrator"
            elif "service cannot be started because it is disabled" in output:
                reason = "System Restore service is disabled in Windows settings"
            
            print(f"Warning: Could not create system restore point. Reason: {reason}")
            logging.warning(f"Could not create system restore point: {output}")
            return False
    except Exception as e:
        logging.error(f"Error in create_restore_point: {str(e)}")
        print(f"Error creating restore point: {str(e)}")
        return False

def check_app_installed(app_name):
    """Check if an app is already installed on the system.
    
    Args:
        app_name (str): The name of the app to check
        
    Returns:
        bool: True if installed, False otherwise
    """
    try:
        ps_cmd = f"Get-AppxPackage -AllUsers *{app_name}*"
        success, output = run_powershell(ps_cmd)
        
        # If command was successful and returned non-empty output, app exists
        return success and len(output.strip()) > 0
    except Exception as e:
        logging.error(f"Error checking if {app_name} is installed: {str(e)}")
        # Assume not installed on error to be safe
        return False

def get_available_apps_for_reinstall():
    """Get a list of apps that can be reinstalled.
    
    Returns:
        dict: Dictionary with app_name as key and installed status as value
    """
    try:
        # Get app list from app_actions.py
        from app_actions import APPS
        from powershell_utils import run_batch_app_check
        
        # Run batch check for all apps at once
        app_names = list(APPS.keys())
        installed_status = run_batch_app_check(app_names)
        
        # Format the results
        available_apps = {}
        for app_name in app_names:
            is_installed = installed_status.get(app_name, False)
            available_apps[app_name] = {
                "description": APPS[app_name]["description"] if "description" in APPS[app_name] else app_name,
                "installed": is_installed
            }
        
        return available_apps
    except Exception as e:
        logging.error(f"Error in get_available_apps_for_reinstall: {str(e)}")
        return {}

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
    
    # Check for admin privileges
    if not ensure_admin():
        print("App reinstallation requires administrator privileges. Please run the application as administrator.")
        logging.warning("App reinstallation requires administrator privileges")
        return 0, len(app_list)
    
    print("Reinstalling selected apps...")
    logging.info(f"Starting reinstallation of selected apps: {', '.join(app_list)}")
    
    # Create a restore point before making changes
    create_restore_point()
    
    success_count = 0
    failed_count = 0
    
    for app_name in app_list:
        try:
            print(f"Attempting to reinstall {app_name}...")
            logging.info(f"Attempting to reinstall {app_name}")
            
            # Check if already installed
            was_installed = check_app_installed(app_name)
            
            # Method 1: Try to register from existing package
            ps_cmd1 = f"Get-AppxPackage -AllUsers *{app_name}* | ForEach-Object {{Add-AppxPackage -DisableDevelopmentMode -Register \"$($_.InstallLocation)\\AppXManifest.xml\" -ErrorAction SilentlyContinue}}"
            success1, _ = run_powershell(ps_cmd1)
            
            # Method 2: Try to reinstall from the provisioned source
            ps_cmd2 = f"Get-AppxProvisionedPackage -Online | Where-Object {{$_.DisplayName -like '*{app_name}*'}} | ForEach-Object {{Add-AppxProvisionedPackage -Online -PackagePath $_.PackagePath -SkipLicense -ErrorAction SilentlyContinue}}"
            success2, _ = run_powershell(ps_cmd2)
            
            # Method 3: Try to register from package family
            ps_cmd3 = f"Add-AppxPackage -RegisterByFamilyName -MainPackage {app_name} -ErrorAction SilentlyContinue"
            success3, _ = run_powershell(ps_cmd3)
            
            # Check if reinstall was successful
            now_installed = check_app_installed(app_name)
            
            if now_installed:
                print(f"Successfully reinstalled {app_name}")
                logging.info(f"Successfully reinstalled {app_name}")
                success_count += 1
            else:
                print(f"Initial reinstall attempts failed for {app_name}, trying alternative methods...")
                
                # Method 4: Try direct reinstall from Microsoft Store (if app wasn't initially installed)
                if not was_installed:
                    ps_cmd4 = f"Add-AppxPackage -RegisterByFamilyName -MainPackage {app_name}"
                    success4, output4 = run_powershell(ps_cmd4)
                    
                    if success4 or check_app_installed(app_name):
                        print(f"Successfully reinstalled {app_name} from store")
                        logging.info(f"Successfully reinstalled {app_name} from store")
                        success_count += 1
                    else:
                        print(f"Failed to reinstall {app_name}")
                        logging.warning(f"Failed to reinstall {app_name}")
                        failed_count += 1
                else:
                    print(f"Failed to reinstall {app_name}")
                    logging.warning(f"Failed to reinstall {app_name}")
                    failed_count += 1
        except Exception as e:
            print(f"Error reinstalling {app_name}: {str(e)}")
            logging.error(f"Error reinstalling {app_name}: {str(e)}")
            failed_count += 1
    
    # Final results
    result_msg = f"Reinstallation complete. Successfully reinstalled {success_count} apps."
    if failed_count > 0:
        result_msg += f" Failed to reinstall {failed_count} apps."
        result_msg += " Some apps may need to be manually reinstalled from the Microsoft Store."
    
    print(result_msg)
    logging.info(result_msg)
    
    return success_count, failed_count

def restore_defaults():
    """Restore system defaults by reinstalling removed apps.
    
    Returns:
        bool: True if successful (at least some apps restored), False otherwise
    """
    try:
        print("Restoring defaults to the system...")
        logging.info("Starting system defaults restoration")
        
        # Check for admin privileges
        if not ensure_admin():
            print("Restore defaults requires administrator privileges. Please run the application as administrator.")
            logging.warning("Restore defaults requires administrator privileges")
            return False
        
        # Create a restore point first
        create_restore_point()
        
        # Get app list from app_actions.py
        from app_actions import APPS
        
        # Step 1: Try to restore existing packages first
        print("Attempting to restore existing packages...")
        ps_cmd1 = "Get-AppxPackage -AllUsers | ForEach-Object {Add-AppxPackage -DisableDevelopmentMode -Register \"$($_.InstallLocation)\\AppXManifest.xml\" -ErrorAction SilentlyContinue}"
        run_powershell(ps_cmd1)
        
        # Step 2: Reinstall known apps from Windows Store
        print("\nAttempting to reinstall apps from Windows Store...")
        
        success_count = 0
        failed_count = 0
        
        for app_name in APPS.keys():
            try:
                print(f"Attempting to restore {app_name}...")
                
                # Check if already installed
                was_installed = check_app_installed(app_name)
                if was_installed:
                    print(f"{app_name} is already installed")
                    success_count += 1
                    continue
                
                # Method 1: Try to reinstall from the provisioned source
                ps_cmd = (f"Get-AppxProvisionedPackage -Online | Where-Object {{$_.DisplayName -like '*{app_name}*'}} | "
                        f"ForEach-Object {{Add-AppxProvisionedPackage -Online -PackagePath $_.PackagePath -SkipLicense -ErrorAction SilentlyContinue}}")
                success1, _ = run_powershell(ps_cmd)
                
                # Method 2: For Store apps, try to register package
                ps_cmd = f"Add-AppxPackage -RegisterByFamilyName -MainPackage {app_name} -ErrorAction SilentlyContinue"
                success2, _ = run_powershell(ps_cmd)
                
                # Check if now installed
                now_installed = check_app_installed(app_name)
                
                if now_installed:
                    print(f"Successfully restored {app_name}")
                    logging.info(f"Successfully restored {app_name}")
                    success_count += 1
                else:
                    print(f"Failed to restore {app_name}")
                    logging.warning(f"Failed to restore {app_name}")
                    failed_count += 1
            except Exception as e:
                print(f"Error restoring {app_name}: {str(e)}")
                logging.error(f"Error restoring {app_name}: {str(e)}")
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
    except Exception as e:
        logging.error(f"Error in restore_defaults: {str(e)}")
        print(f"Error restoring defaults: {str(e)}")
        return False

def uninstall_onedrive():
    """Uninstall OneDrive and clean up residual files.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("Uninstalling OneDrive...")
        logging.info("Starting OneDrive uninstallation")
        
        # Check for admin privileges
        if not ensure_admin():
            print("OneDrive uninstallation requires administrator privileges. Please run the application as administrator.")
            logging.warning("OneDrive uninstallation requires administrator privileges")
            return False
        
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
            print(f"Failed to completely uninstall OneDrive: {output}")
            logging.error(f"OneDrive uninstallation error: {output}")
        
        return success
    except Exception as e:
        logging.error(f"Error in uninstall_onedrive: {str(e)}")
        print(f"Error uninstalling OneDrive: {str(e)}")
        return False