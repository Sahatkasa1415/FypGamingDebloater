import sys
import logging
import os
from app_actions import remove_unneeded_apps
from selection import choose_selected_apps, choose_apps_to_reinstall
from restore import create_restore_point, restore_defaults

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bloatware_remover.log',
    filemode='a'
)

def show_menu():
    """Show the main menu and handle user input."""
    print("\n" + "="*50)
    print("Gaming Bloatware Remover - Command Line Interface")
    print("="*50)
    print("\nChoose an option:")
    print("1. Remove all unneeded apps (One-click delete)")
    print("2. Remove specific apps")
    print("3. Reinstall specific apps (NEW)")
    print("4. Restore system defaults")
    print("5. Create system restore point")
    print("6. Exit")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    try:
        if choice == '1':
            confirm = input("\nThis will remove ALL predefined unneeded apps. Continue? (y/n): ").strip().lower()
            if confirm == 'y':
                logging.info("User selected to remove all unneeded apps")
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
                logging.info("User selected to restore defaults")
                restore_defaults()
            else:
                logging.info("Restore defaults cancelled by user")
                print("Operation cancelled.")
                
        elif choice == '5':
            logging.info("User selected to create system restore point")
            create_restore_point()
            
        elif choice == '6':
            print("\nExiting program. Goodbye!")
            sys.exit(0)
            
        else:
            print("\nInvalid choice. Please enter a number between 1 and 6.")
            
    except Exception as e:
        logging.critical(f"Critical error in main: {str(e)}")
        print(f"\nAn error occurred: {str(e)}")
    
    # Return to menu after operation completes
    input("\nPress Enter to return to the main menu...")
    show_menu()

if __name__ == "__main__":
    # Create a system restore point when the app starts
    try:
        create_restore_point()
    except Exception as e:
        logging.error(f"Error creating initial restore point: {str(e)}")
        print(f"Warning: Could not create initial restore point: {str(e)}")

    show_menu()