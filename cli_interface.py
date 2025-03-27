import sys
import logging
import os
from app_actions import remove_unneeded_apps
from selection import choose_selected_apps, choose_apps_to_reinstall
from restore import create_restore_point, restore_defaults
from powershell_utils import ensure_admin

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
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
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
            print("\nExiting program. Goodbye!")
            sys.exit(0)
            
        else:
            print("\nInvalid choice. Please enter a number between 1 and 6.")
            
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