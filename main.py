from app_actions import remove_unneeded_apps
from restore import restore_defaults, create_restore_point
from selection import choose_selected_apps
import logging
import os
import sys

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='logs/bloatware_remover.log',
    filemode='a'
)

def print_header():
    """Print an attractive header for the application."""
    header = """
    ╔════════════════════════════════════════════════════════╗
    ║                                                        ║
    ║             GAMING BLOATWARE REMOVER                   ║
    ║                                                        ║
    ║             Optimize your system for gaming            ║
    ║                                                        ║
    ╚════════════════════════════════════════════════════════╝
    """
    print(header)

def main():
    """Main entry point of the application."""
    try:
        print_header()
        logging.info("Application started")
        
        # Create a restore point at startup for safety
        create_restore_point()
        
        while True:
            print("\nMenu:")
            print("1. Remove All Unneeded Apps")
            print("2. Restore Defaults")
            print("3. Remove Selected Apps")
            print("4. Exit")
            
            try:
                choice = input("\nEnter your choice (1-4): ")
                
                if choice == "1":
                    confirm = input("Are you sure you want to remove all unneeded apps? (y/n): ").strip().lower()
                    if confirm == 'y':
                        logging.info("User selected to remove all unneeded apps")
                        remove_unneeded_apps()
                    else:
                        print("Operation cancelled.")
                        logging.info("Remove all unneeded apps cancelled by user")
                
                elif choice == "2":
                    confirm = input("Are you sure you want to restore defaults? This might reinstall removed apps. (y/n): ").strip().lower()
                    if confirm == 'y':
                        logging.info("User selected to restore defaults")
                        restore_defaults()
                    else:
                        print("Operation cancelled.")
                        logging.info("Restore defaults cancelled by user")
                
                elif choice == "3":
                    logging.info("User selected to remove specific apps")
                    choose_selected_apps()
                
                elif choice == "4":
                    print("Thank you for using Gaming Bloatware Remover. Exiting...")
                    logging.info("Application exited by user")
                    break
                
                else:
                    print("Invalid option, please enter a number between 1 and 4.")
            
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                logging.info("Operation interrupted by user")
            
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                logging.error(f"Unexpected error: {str(e)}")
                
    except Exception as e:
        print(f"Critical error: {str(e)}")
        logging.critical(f"Critical error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()