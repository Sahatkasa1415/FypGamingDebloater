from app_actions import APPS, SELECTABLE_APPS, remove_selected_apps
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
                    chosen_apps.append(SELECTABLE_APPS[i-1]) ayush
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
            logging.info(f"User confirmed removal of selected apps: {', '.join(chosen_apps)}")
            remove_selected_apps(chosen_apps)
            return
        else:
            print("Operation cancelled.")
            logging.info("App removal cancelled by user")
            return