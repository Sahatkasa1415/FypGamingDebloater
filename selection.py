from app_actions import APPS, SELECTABLE_APPS, remove_selected_apps
from restore import get_available_apps_for_reinstall, reinstall_selected_apps, create_restore_point
from powershell_utils import ensure_admin
import logging

# Setup logging if not already configured
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='bloatware_remover.log'
    )

def choose_selected_apps():
    """Let the user choose which apps to remove from SELECTABLE_APPS."""
    try:
        print("\nSelect which apps to remove (comma-separated indices or 'all' for all apps):")
        
        # Display the app list with descriptions
        for i, app_name in enumerate(SELECTABLE_APPS, start=1):
            description = APPS[app_name]["description"] if app_name in APPS and "description" in APPS[app_name] else app_name
            print(f"{i}. {description} ({app_name})")
        
        # Add an option to cancel
        print("0. Cancel and return to menu")
        
        while True:
            choice = input("\nEnter your choice: ").strip().lower()
            
            # Check for cancel option
            if choice == '0':
                print("Operation cancelled.")
                logging.info("App selection cancelled by user")
                return
            
            # Check for "all" option
            if choice == 'all':
                confirm = input("\nAre you sure you want to remove ALL listed apps? (y/n): ").strip().lower()
                if confirm == 'y':
                    # Check for admin privileges
                    if not ensure_admin():
                        print("Removing apps requires administrator privileges. Please run as administrator.")
                        logging.warning("Removing apps requires administrator privileges")
                        return
                    
                    # Create restore point first
                    create_restore_point()
                    
                    logging.info("User selected all apps for removal")
                    remove_selected_apps(SELECTABLE_APPS)
                    return
                else:
                    print("Operation cancelled.")
                    logging.info("All apps removal cancelled by user")
                    return
            
            # Process comma-separated indices
            indices = choice.split(",")
            chosen_apps = []
            invalid_selections = []
            
            for idx in indices:
                idx = idx.strip()
                if idx.isdigit():
                    i = int(idx)
                    if 1 <= i <= len(SELECTABLE_APPS):
                        chosen_apps.append(SELECTABLE_APPS[i-1])
                    else:
                        invalid_selections.append(idx)
                else:
                    invalid_selections.append(idx)
            
            # If there were invalid selections, notify the user
            if invalid_selections:
                print(f"Invalid selection(s): {', '.join(invalid_selections)}")
                print("Please enter valid numbers from the list.")
                continue
            
            # If no valid apps were selected, ask again
            if not chosen_apps:
                print("No valid apps selected. Please try again.")
                continue
            
            # Show selected apps and confirm
            print("\nYou've selected the following apps for removal:")
            for app_name in chosen_apps:
                description = APPS[app_name]["description"] if app_name in APPS and "description" in APPS[app_name] else app_name
                print(f"- {description} ({app_name})")
            
            confirm = input("\nConfirm removal? (y/n): ").strip().lower()
            if confirm == 'y':
                # Check for admin privileges
                if not ensure_admin():
                    print("Removing apps requires administrator privileges. Please run as administrator.")
                    logging.warning("Removing apps requires administrator privileges")
                    return
                
                # Create restore point first
                create_restore_point()
                
                logging.info(f"User confirmed removal of selected apps: {', '.join(chosen_apps)}")
                remove_selected_apps(chosen_apps)
                return
            else:
                print("Operation cancelled.")
                logging.info("App removal cancelled by user")
                return
    except Exception as e:
        logging.error(f"Error in choose_selected_apps: {str(e)}")
        print(f"Error selecting apps: {str(e)}")

def choose_apps_to_reinstall():
    """Let the user choose which apps to reinstall."""
    try:
        print("\nLoading list of available apps...")
        
        # Get the available apps and their status
        available_apps = get_available_apps_for_reinstall()
        app_list = list(available_apps.keys())
        
        print("\nSelect which apps to reinstall (comma-separated indices, 'all' for all apps, or 'missing' for missing apps):")
        
        # Display the app list with descriptions and status
        for i, app_name in enumerate(app_list, start=1):
            description = available_apps[app_name]["description"]
            installed = available_apps[app_name]["installed"]
            status = "Installed" if installed else "Not Installed"
            print(f"{i}. {description} ({app_name}) - {status}")
        
        # Add an option to cancel
        print("0. Cancel and return to menu")
        
        while True:
            choice = input("\nEnter your choice: ").strip().lower()
            
            # Check for cancel option
            if choice == '0':
                print("Operation cancelled.")
                logging.info("App reinstall selection cancelled by user")
                return
            
            # Check for "all" option
            if choice == 'all':
                confirm = input("\nAre you sure you want to reinstall ALL listed apps? (y/n): ").strip().lower()
                if confirm == 'y':
                    # Check for admin privileges
                    if not ensure_admin():
                        print("Reinstalling apps requires administrator privileges. Please run as administrator.")
                        logging.warning("Reinstalling apps requires administrator privileges")
                        return
                    
                    # Create restore point first
                    create_restore_point()
                    
                    logging.info("User selected all apps for reinstall")
                    reinstall_selected_apps(app_list)
                    return
                else:
                    print("Operation cancelled.")
                    logging.info("All apps reinstall cancelled by user")
                    return
            
            # Check for "missing" option
            if choice == 'missing':
                missing_apps = [app for app in app_list if not available_apps[app]["installed"]]
                if not missing_apps:
                    print("No missing apps found. All apps are already installed.")
                    continue
                
                print("\nYou've selected to reinstall all missing apps:")
                for app_name in missing_apps:
                    description = available_apps[app_name]["description"]
                    print(f"- {description} ({app_name})")
                
                confirm = input("\nConfirm reinstall of all missing apps? (y/n): ").strip().lower()
                if confirm == 'y':
                    # Check for admin privileges
                    if not ensure_admin():
                        print("Reinstalling apps requires administrator privileges. Please run as administrator.")
                        logging.warning("Reinstalling apps requires administrator privileges")
                        return
                    
                    # Create restore point first
                    create_restore_point()
                    
                    logging.info(f"User confirmed reinstall of missing apps: {', '.join(missing_apps)}")
                    reinstall_selected_apps(missing_apps)
                    return
                else:
                    print("Operation cancelled.")
                    logging.info("Missing apps reinstall cancelled by user")
                    return
            
            # Process comma-separated indices
            indices = choice.split(",")
            chosen_apps = []
            invalid_selections = []
            
            for idx in indices:
                idx = idx.strip()
                if idx.isdigit():
                    i = int(idx)
                    if 1 <= i <= len(app_list):
                        chosen_apps.append(app_list[i-1])
                    else:
                        invalid_selections.append(idx)
                else:
                    invalid_selections.append(idx)
            
            # If there were invalid selections, notify the user
            if invalid_selections:
                print(f"Invalid selection(s): {', '.join(invalid_selections)}")
                print("Please enter valid numbers from the list.")
                continue
            
            # If no valid apps were selected, ask again
            if not chosen_apps:
                print("No valid apps selected. Please try again.")
                continue
            
            # Show selected apps and confirm
            print("\nYou've selected the following apps for reinstall:")
            for app_name in chosen_apps:
                description = available_apps[app_name]["description"]
                status = "Installed" if available_apps[app_name]["installed"] else "Not Installed"
                print(f"- {description} ({app_name}) - {status}")
            
            confirm = input("\nConfirm reinstall? (y/n): ").strip().lower()
            if confirm == 'y':
                # Check for admin privileges
                if not ensure_admin():
                    print("Reinstalling apps requires administrator privileges. Please run as administrator.")
                    logging.warning("Reinstalling apps requires administrator privileges")
                    return
                
                # Create restore point first
                create_restore_point()
                
                logging.info(f"User confirmed reinstall of selected apps: {', '.join(chosen_apps)}")
                reinstall_selected_apps(chosen_apps)
                return
            else:
                print("Operation cancelled.")
                logging.info("App reinstall cancelled by user")
                return
    except Exception as e:
        logging.error(f"Error in choose_apps_to_reinstall: {str(e)}")
        print(f"Error selecting apps to reinstall: {str(e)}")