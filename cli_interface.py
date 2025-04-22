import sys
import logging
import os
from app_actions import remove_unneeded_apps, remove_selected_apps
from selection import choose_selected_apps, choose_apps_to_reinstall
from restore import create_restore_point, restore_defaults
from powershell_utils import ensure_admin, run_powershell
import json
from datetime import datetime, timedelta

# Setup logging
try:
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='bloatware_remover.log',
        filemode='a'
    )
except Exception as e:
    print(f"Error setting up logging: {e}")
    # Continue anyway - the app can work without logging

def get_unused_apps(days_threshold=90):
    """
    Get list of installed apps that haven't been used for a specified number of days.
    
    Args:
        days_threshold (int): Number of days to consider an app as "unused"
        
    Returns:
        list: List of dictionaries containing app info for unused apps
    """
    try:
        logging.info(f"Scanning for apps unused for {days_threshold} days")
        
        # Check for admin privileges (needed to access usage data)
        if not ensure_admin():
            logging.warning("Admin privileges required to scan app usage data")
            return {"error": "Admin privileges required"}
        
        # PowerShell command to get installed apps with their package info
        # We'll get installed modern apps and then check usage data for them
        ps_cmd = """
        # Get installed apps
        $installedApps = Get-AppxPackage -AllUsers | Select-Object Name, PackageFamilyName, DisplayName
        
        # Convert to JSON
        $installedApps | ConvertTo-Json
        """
        
        success, output = run_powershell(ps_cmd)
        if not success or not output:
            logging.error("Failed to get installed apps")
            return {"error": "Failed to get installed apps"}
        
        # Parse the installed apps
        installed_apps = json.loads(output)
        
        # If we just got one app, make sure we have a list
        if isinstance(installed_apps, dict):
            installed_apps = [installed_apps]
        
        # Now get app usage data from the registry
        ps_cmd_usage = """
        # Get app usage data from registry
        $usageData = Get-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Search\\RecentApps\\*" | 
            Select-Object PSChildName, LastAccessedTime, AppId, LaunchCount
                
        # Convert to JSON
        $usageData | ConvertTo-Json
        """
        
        success, usage_output = run_powershell(ps_cmd_usage)
        
        # Create a dictionary to hold usage data, keyed by app ID
        usage_data = {}
        current_date = datetime.now()
        
        if success and usage_output:
            try:
                usage_items = json.loads(usage_output)
                
                # Handle case of single item
                if isinstance(usage_items, dict):
                    usage_items = [usage_items]
                
                # Process usage data
                for item in usage_items:
                    if item and "AppId" in item and "LastAccessedTime" in item:
                        app_id = item["AppId"]
                        last_accessed = item["LastAccessedTime"]
                        
                        # Parse the filetime format if it exists
                        if last_accessed:
                            # Convert filetime to datetime
                            try:
                                # Parse 18-digit filetime if that's the format
                                if isinstance(last_accessed, int) or (isinstance(last_accessed, str) and last_accessed.isdigit() and len(last_accessed) >= 18):
                                    filetime = int(last_accessed)
                                    # Convert Windows filetime to Python datetime (minus 11644473600 seconds for Unix epoch difference)
                                    seconds_since_epoch = filetime / 10000000 - 11644473600
                                    last_date = datetime.fromtimestamp(seconds_since_epoch)
                                else:
                                    # Try to parse as a date string
                                    last_date = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
                                
                                days_since_used = (current_date - last_date).days
                                usage_data[app_id] = {
                                    "last_used": last_date.strftime("%Y-%m-%d %H:%M:%S"),
                                    "days_since_used": days_since_used,
                                    "launch_count": item.get("LaunchCount", 0)
                                }
                            except Exception as e:
                                logging.warning(f"Couldn't parse date for {app_id}: {e}")
            except Exception as e:
                logging.error(f"Error processing usage data: {str(e)}")
                # Continue with what we have
        
        # Get additional app usage data from Timeline (Activity History)
        ps_cmd_timeline = """
        # Get app usage data from Activity History
        try {
            $activities = Get-WinEvent -LogName "Microsoft-Windows-Application-Experience/Program-Inventory" -MaxEvents 1000 -ErrorAction SilentlyContinue |
                Where-Object { $_.Id -eq 500 -or $_.Id -eq 501 } |
                Select-Object TimeCreated, Message
                
            $activities | ConvertTo-Json
        } catch {
            Write-Output "[]"
        }
        """
        
        success, timeline_output = run_powershell(ps_cmd_timeline)
        
        if success and timeline_output and timeline_output != "[]":
            try:
                timeline_items = json.loads(timeline_output)
                
                # Handle case of single item
                if isinstance(timeline_items, dict):
                    timeline_items = [timeline_items]
                
                # Process timeline data
                for item in timeline_items:
                    if item and "Message" in item and "TimeCreated" in item:
                        # Extract app info from message
                        message = item["Message"]
                        if "Application Id=" in message:
                            app_id = message.split("Application Id=")[1].split(",")[0].strip()
                            time_created = item["TimeCreated"]
                            
                            # Parse the date if it exists
                            if time_created:
                                try:
                                    last_date = datetime.fromisoformat(time_created.replace('Z', '+00:00'))
                                    days_since_used = (current_date - last_date).days
                                    
                                    # Only update if this is more recent than existing data
                                    if app_id not in usage_data or days_since_used < usage_data[app_id]["days_since_used"]:
                                        usage_data[app_id] = {
                                            "last_used": last_date.strftime("%Y-%m-%d %H:%M:%S"),
                                            "days_since_used": days_since_used,
                                            "launch_count": 1  # We don't have this info from timeline
                                        }
                                except Exception as e:
                                    logging.warning(f"Couldn't parse timeline date for {app_id}: {e}")
            except Exception as e:
                logging.error(f"Error processing timeline data: {str(e)}")
                # Continue with what we have
        
        # Match usage data with installed apps
        unused_apps = []
        
        for app in installed_apps:
            # Skip system apps and framework packages
            if not app.get("Name") or "framework" in app.get("Name", "").lower():
                continue
                
            app_name = app.get("Name", "")
            display_name = app.get("DisplayName", app_name)
            
            # Check if we have usage data for this app
            app_id_to_check = f"App\\{app.get('PackageFamilyName', '')}"
            
            if app_id_to_check in usage_data:
                days_since_used = usage_data[app_id_to_check]["days_since_used"]
                
                # If app hasn't been used in threshold days, add to unused_apps
                if days_since_used >= days_threshold:
                    unused_apps.append({
                        "name": app_name,
                        "display_name": display_name,
                        "days_since_used": days_since_used,
                        "last_used": usage_data[app_id_to_check]["last_used"],
                        "launch_count": usage_data[app_id_to_check].get("launch_count", 0)
                    })
            else:
                # No usage data found, likely never used or usage not tracked
                # We'll consider it unused for our purposes
                unused_apps.append({
                    "name": app_name,
                    "display_name": display_name,
                    "days_since_used": days_threshold,  # Set to threshold as minimum
                    "last_used": "Never or unknown",
                    "launch_count": 0
                })
        
        # Sort by days since used (most unused first)
        unused_apps.sort(key=lambda x: x["days_since_used"], reverse=True)
        
        logging.info(f"Found {len(unused_apps)} apps unused for {days_threshold}+ days")
        return unused_apps
        
    except Exception as e:
        logging.error(f"Error in get_unused_apps: {str(e)}")
        return {"error": f"Error scanning for unused apps: {str(e)}"}

def show_unused_apps():
    """Display and manage apps that haven't been used in the last 90 days."""
    try:
        print("\nScanning for apps that haven't been used in the last 90 days...")
        
        # Check for admin privileges
        if not ensure_admin():
            print("Scanning for unused apps requires administrator privileges. Please run as administrator.")
            logging.warning("Scanning for unused apps requires administrator privileges")
            return
        
        # Get unused apps
        unused_apps = get_unused_apps(days_threshold=90)
        
        # Check for error
        if isinstance(unused_apps, dict) and "error" in unused_apps:
            print(f"Error: {unused_apps['error']}")
            return
        
        # Display the results
        if not unused_apps:
            print("No apps found that haven't been used in the last 90 days.")
            return
        
        print(f"\nFound {len(unused_apps)} apps that haven't been used in the last 90 days:\n")
        
        # Display app list with indices
        for i, app in enumerate(unused_apps, start=1):
            display_name = app.get("display_name", app["name"])
            days = app.get("days_since_used", "Unknown")
            last_used = app.get("last_used", "Unknown")
            print(f"{i}. {display_name} ({app['name']}) - Last used: {last_used} ({days} days ago)")
        
        # Add option to remove selected apps
        print("\n0. Cancel and return to menu")
        print("A. Remove all unused apps")
        
        choice = input("\nEnter app numbers to remove (comma-separated) or 'A' for all: ").strip()
        
        if choice.lower() == '0':
            print("Operation cancelled.")
            return
        
        selected_apps = []
        
        if choice.lower() == 'a':
            # User wants to remove all unused apps
            confirm = input(f"\nAre you sure you want to remove ALL {len(unused_apps)} unused apps? (y/n): ").strip().lower()
            if confirm != 'y':
                print("Operation cancelled.")
                return
            
            # Select all unused apps
            selected_apps = [app["name"] for app in unused_apps]
        else:
            # Process comma-separated indices
            indices = choice.split(",")
            invalid_selections = []
            
            for idx in indices:
                idx = idx.strip()
                if idx.isdigit():
                    i = int(idx)
                    if 1 <= i <= len(unused_apps):
                        selected_apps.append(unused_apps[i-1]["name"])
                    else:
                        invalid_selections.append(idx)
                else:
                    invalid_selections.append(idx)
            
            # If there were invalid selections, notify the user
            if invalid_selections:
                print(f"Invalid selection(s): {', '.join(invalid_selections)}")
                print("Please enter valid numbers from the list.")
                return
            
            # If no valid apps were selected, ask again
            if not selected_apps:
                print("No valid apps selected.")
                return
            
            # Show selected apps and confirm
            selected_display_names = []
            for app_name in selected_apps:
                for app in unused_apps:
                    if app["name"] == app_name:
                        selected_display_names.append(app.get("display_name", app_name))
                        break
            
            print("\nYou've selected the following apps for removal:")
            for name in selected_display_names:
                print(f"- {name}")
            
            confirm = input("\nConfirm removal? (y/n): ").strip().lower()
            if confirm != 'y':
                print("Operation cancelled.")
                return
        
        # Create restore point first
        create_restore_point()
        
        # Perform the removal
        print("\nRemoving selected apps...")
        success = remove_selected_apps(selected_apps)
        
        if success:
            print(f"Successfully removed {len(selected_apps)} unused app(s).")
        else:
            print("Failed to remove some or all apps. Check the logs for details.")
    except Exception as e:
        logging.error(f"Error in show_unused_apps: {str(e)}")
        print(f"Error: {str(e)}")

def show_menu():
    """Show the main menu and handle user input."""
    try:
        print("\n" + "="*50)
        print("Gaming Bloatware Remover - Command Line Interface")
        print("="*50)
        print("\nChoose an option:")
        print("1. Remove all unneeded apps (One-click delete)")
        print("2. Remove specific apps")
        print("3. Reinstall specific apps")
        print("4. Restore system defaults")
        print("5. Create system restore point")
        print("6. Find & remove unused apps (Last 90 days)")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            confirm = input("\nThis will remove ALL predefined unneeded apps. Continue? (y/n): ").strip().lower()
            if confirm == 'y':
                # Check for admin privileges
                if not ensure_admin():
                    print("Removing apps requires administrator privileges. Please run as administrator.")
                    logging.warning("Removing apps requires administrator privileges")
                else:
                    logging.info("User selected to remove all unneeded apps")
                    create_restore_point()  # Create a restore point first
                    remove_unneeded_apps()
            else:
                logging.info("One-click delete cancelled by user")
                print("Operation cancelled.")
                
        elif choice == '2':
            logging.info("User selected to remove specific apps")
            choose_selected_apps()
            
        elif choice == '3':
            logging.info("User selected to reinstall specific apps")
            choose_apps_to_reinstall()
            
        elif choice == '4':
            confirm = input("\nThis will attempt to restore ALL system apps to their default state. Continue? (y/n): ").strip().lower()
            if confirm == 'y':
                # Check for admin privileges
                if not ensure_admin():
                    print("Restoring defaults requires administrator privileges. Please run as administrator.")
                    logging.warning("Restoring defaults requires administrator privileges")
                else:
                    logging.info("User selected to restore defaults")
                    restore_defaults()
            else:
                logging.info("Restore defaults cancelled by user")
                print("Operation cancelled.")
                
        elif choice == '5':
            logging.info("User selected to create system restore point")
            
            # Check for admin privileges
            if not ensure_admin():
                print("Creating a restore point requires administrator privileges. Please run as administrator.")
                logging.warning("Creating a restore point requires administrator privileges")
            else:
                success = create_restore_point()
                if success:
                    print("System restore point created successfully.")
                else:
                    print("Failed to create system restore point. Check the logs for details.")
        
        elif choice == '6':
            logging.info("User selected to find and remove unused apps")
            show_unused_apps()
            
        elif choice == '7':
            print("\nExiting program. Goodbye!")
            sys.exit(0)
            
        else:
            print("\nInvalid choice. Please enter a number between 1 and 7.")
            
    except KeyboardInterrupt:
        print("\n\nProgram interrupted. Returning to main menu...")
    except Exception as e:
        logging.critical(f"Critical error in main: {str(e)}")
        print(f"\nAn error occurred: {str(e)}")
    
    # Return to menu after operation completes
    input("\nPress Enter to return to the main menu...")
    show_menu()

if __name__ == "__main__":
    try:
        # Print welcome message
        print("\nWelcome to Gaming Bloatware Remover!")
        print("This tool will help you remove unwanted apps from your system.")
        
        # Create a system restore point when the app starts
        print("\nAttempting to create an initial system restore point...")
        try:
            if ensure_admin():
                success = create_restore_point()
                if success:
                    print("System restore point created successfully.")
                else:
                    print("Warning: Could not create initial restore point. Proceed with caution.")
            else:
                print("Warning: Administrator privileges are required for full functionality.")
                print("Some operations may not work without running as administrator.")
                logging.warning("Application started without admin privileges")
        except Exception as e:
            logging.error(f"Error creating initial restore point: {str(e)}")
            print(f"Warning: Could not create initial restore point: {str(e)}")

        # Show the main menu
        show_menu()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Unhandled exception in main: {str(e)}")
        print(f"\nA critical error occurred: {str(e)}")
        print("The application will now exit.")
        sys.exit(1)