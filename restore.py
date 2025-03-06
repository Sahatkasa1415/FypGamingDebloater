from powershell_utils import run_powershell
import logging
from powershell_utils import run_powershell
import logging
from datetime import datetime  # Add this line here

# Setup logging if not already configured
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='bloatware_remover.log'
    )
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