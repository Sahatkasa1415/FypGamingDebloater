from powershell_utils import run_powershell
import logging

# Setup logging if not already configured
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='bloatware_remover.log'
    )

# Dictionary of apps with their registry keys
# This combines both the list of apps and their registry keys in one place
APPS = {
    # Gaming & Entertainment
    "Microsoft.XboxApp": {
        "description": "Xbox Console Companion",
        "registry_keys": [
            r"Registry::HKEY_CLASSES_ROOT\Extensions\ContractId\Windows.Launch\PackageId\Microsoft.XboxApp",
            r"Registry::HKEY_CLASSES_ROOT\Extensions\ContractId\Windows.Protocol\PackageId\Microsoft.XboxApp"
        ]
    },
    "Microsoft.Xbox.TCUI": {
        "description": "Xbox Live UI",
        "registry_keys": []
    },
    "Microsoft.XboxGameOverlay": {
        "description": "Xbox Game Overlay",
        "registry_keys": []
    },
    "Microsoft.XboxGamingOverlay": {
        "description": "Xbox Game Bar",
        "registry_keys": []
    },
    "Microsoft.XboxIdentityProvider": {
        "description": "Xbox Identity Provider",
        "registry_keys": []
    },
    "Microsoft.XboxSpeechToTextOverlay": {
        "description": "Xbox Voice Overlay",
        "registry_keys": []
    },
    "Microsoft.MicrosoftSolitaireCollection": {
        "description": "Microsoft Solitaire Collection",
        "registry_keys": []
    },
    "Microsoft.ZuneMusic": {
        "description": "Groove Music",
        "registry_keys": []
    },
    "Microsoft.ZuneVideo": {
        "description": "Movies & TV",
        "registry_keys": []
    },
    "king.com.CandyCrushSaga": {
        "description": "Candy Crush Saga",
        "registry_keys": [
            r"Registry::HKEY_CLASSES_ROOT\Extensions\ContractId\Windows.Launch\PackageId\King.CandyCrushSaga",
            r"Registry::HKEY_CLASSES_ROOT\Extensions\ContractId\Windows.Protocol\PackageId\King.CandyCrushSaga"
        ]
    },
    
    # Productivity & Office
    "Microsoft.Office.OneNote": {
        "description": "OneNote",
        "registry_keys": []
    },
    "Microsoft.MicrosoftOfficeHub": {
        "description": "Office Hub",
        "registry_keys": []
    },
    "Microsoft.MicrosoftStickyNotes": {
        "description": "Sticky Notes",
        "registry_keys": []
    },
    
    # System Tools & Utilities
    "Microsoft.WindowsAlarms": {
        "description": "Alarms & Clock",
        "registry_keys": []
    },
    "Microsoft.WindowsCamera": {
        "description": "Windows Camera",
        "registry_keys": []
    },
    "Microsoft.WindowsFeedbackHub": {
        "description": "Feedback Hub",
        "registry_keys": []
    },
    "Microsoft.WindowsMaps": {
        "description": "Windows Maps",
        "registry_keys": []
    },
    "Microsoft.WindowsSoundRecorder": {
        "description": "Voice Recorder",
        "registry_keys": []
    },
    "Microsoft.GetHelp": {
        "description": "Get Help",
        "registry_keys": []
    },
    "Microsoft.Getstarted": {
        "description": "Tips/Get Started",
        "registry_keys": []
    },
    "Microsoft.Microsoft3DViewer": {
        "description": "3D Viewer",
        "registry_keys": []
    },
    "Microsoft.Paint3D": {
        "description": "Paint 3D",
        "registry_keys": [
            r"Registry::HKEY_CLASSES_ROOT\Extensions\ContractId\Windows.Launch\PackageId\Microsoft.MSPaint",
            r"Registry::HKEY_CLASSES_ROOT\Extensions\ContractId\Windows.Protocol\PackageId\Microsoft.MSPaint"
        ]
    },
    "Microsoft.StorePurchaseApp": {
        "description": "Store Purchase App",
        "registry_keys": []
    },
    
    # Communication & Social
    "Microsoft.SkypeApp": {
        "description": "Skype",
        "registry_keys": [
            r"HKCR:\Extensions\ContractId\Windows.Launch\PackageId\Microsoft.SkypeApp",
            r"HKCR:\Extensions\ContractId\Windows.Protocol\PackageId\Microsoft.SkypeApp"
        ]
    },
    "Microsoft.YourPhone": {
        "description": "Your Phone/Phone Link",
        "registry_keys": []
    },
    "microsoft.windowscommunicationsapps": {
        "description": "Mail and Calendar",
        "registry_keys": []
    },
    "Microsoft.People": {
        "description": "People",
        "registry_keys": []
    },
    
    # News & Information
    "Microsoft.BingWeather": {
        "description": "Weather",
        "registry_keys": []
    },
    
    # Optional items (uncomment if you want to remove these)
    "Microsoft.Windows.Photos": {
        "description": "Windows Photos",
        "registry_keys": []
    },
}

# Default list of unneeded apps - can be modified separately if needed
UNNEEDED_APPS = list(APPS.keys())

# Selectable apps for user selection - same as UNNEEDED_APPS for now
SELECTABLE_APPS = list(APPS.keys())

def remove_app(app_name):
    """Remove a single app and its registry entries.
    
    Args:
        app_name (str): The name of the app to remove
        
    Returns:
        bool: True if successful, False otherwise
    """
    logging.info(f"Attempting to remove {app_name}")
    
    # 1. Remove the AppX package
    ps_cmd = f"Get-AppxPackage -AllUsers *{app_name}* | Remove-AppxPackage"
    success, output = run_powershell(ps_cmd)
    
    if success:
        logging.info(f"Successfully removed app {app_name}")
        print(f"Successfully removed {app_name}")
        
        # 2. Remove associated registry keys if defined
        if app_name in APPS and "registry_keys" in APPS[app_name]:
            all_keys_removed = True
            for key in APPS[app_name]["registry_keys"]:
                rm_cmd = f"if (Test-Path '{key}') {{ Remove-Item -Path '{key}' -Recurse -Force }}"
                key_success, key_output = run_powershell(rm_cmd)
                
                if not key_success:
                    all_keys_removed = False
                    logging.warning(f"Failed to remove registry key {key}")
            
            if all_keys_removed:
                logging.info(f"Successfully removed all registry keys for {app_name}")
            else:
                logging.warning(f"Some registry keys for {app_name} could not be removed")
                
        return True
    else:
        error_msg = f"Failed to remove {app_name}"
        logging.error(error_msg)
        if output:
            logging.error(f"Error details: {output}")
        print(error_msg)
        return False

def disable_copilot():
    """Disable Copilot via registry settings."""
    print("Disabling Copilot...")
    logging.info("Attempting to disable Copilot")
    
    cmds = [
        "New-Item -Path 'HKCU:\\Software\\Policies\\Microsoft\\Windows' -Name 'WindowsCopilot' -Force",
        "New-ItemProperty -Path 'HKCU:\\Software\\Policies\\Microsoft\\Windows\\WindowsCopilot' -Name 'TurnOffWindowsCopilot' -Value 1 -PropertyType DWORD -Force"
    ]
    
    success = True
    for cmd in cmds:
        cmd_success, cmd_output = run_powershell(cmd)
        if not cmd_success:
            success = False
            logging.error(f"Failed to execute command: {cmd}")
            logging.error(f"Error details: {cmd_output}")
    
    if success:
        print("Copilot disabled successfully.")
        logging.info("Copilot disabled successfully")
    else:
        print("Failed to fully disable Copilot.")
        logging.error("Failed to fully disable Copilot")
    
    return success

def remove_unneeded_apps():
    """Remove all predefined unneeded apps."""
    print("Removing all unneeded apps...")
    logging.info("Starting removal of all unneeded apps")
    
    successful_removals = 0
    failed_removals = 0
    
    for app in UNNEEDED_APPS:
        if remove_app(app):
            successful_removals += 1
        else:
            failed_removals += 1
    
    # Also disable Copilot
    disable_copilot()
    
    result_msg = f"Removal complete. Successfully removed {successful_removals} apps."
    if failed_removals > 0:
        result_msg += f" Failed to remove {failed_removals} apps."
    
    print(result_msg)
    logging.info(result_msg)
    return successful_removals > 0

def remove_selected_apps(app_list):
    """Remove a given list of apps by name, and then remove associated registry keys."""
    if not app_list:
        print("No apps selected for removal.")
        logging.info("No apps selected for removal")
        return False
    
    print("Removing selected apps...")
    logging.info(f"Starting removal of selected apps: {', '.join(app_list)}")
    
    successful_removals = 0
    failed_removals = 0
    
    for app in app_list:
        if remove_app(app):
            successful_removals += 1+1
        else:
            failed_removals += 1
    
    # Check if Copilot should be disabled
    if "Microsoft.Copilot" in app_list:
        disable_copilot()
    
    result_msg = f"Removal complete. Successfully removed {successful_removals} apps."
    if failed_removals > 0:
        result_msg += f" Failed to remove {failed_removals} apps."
    
    print(result_msg)
    logging.info(result_msg)
    return successful_removals > 0