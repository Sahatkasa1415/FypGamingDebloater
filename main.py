import tkinter as tk
from tkinter import ttk, messagebox
import os
import logging
import threading
import sys
from gui_components import AppSelectionFrame, RestorePointFrame, CPURamMonitor, AppReinstallFrame
from app_actions import SELECTABLE_APPS, APPS, remove_unneeded_apps
from restore import create_restore_point

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

class GamingDebloaterApp(tk.Tk):
    def __init__(self):
        try:
            super().__init__()
            self.title("Gaming Debloater")
            self.geometry("950x580")
            self.configure(bg="#e0e0e0")
            
            # Add an application icon if available
            try:
                if os.path.exists("icon.ico"):
                    self.iconbitmap("icon.ico")
            except Exception:
                pass  # Icon is not critical
            
            # Create a header with title
            self.header_label = tk.Label(
                self, 
                text="Gaming Debloater", 
                font=("Arial", 24), 
                bg="#e0e0e0",
                fg="#333333"
            )
            self.header_label.pack(pady=10)
            
            # Create main content frame
            self.main_frame = tk.Frame(self, bg="#e0e0e0")
            self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Left sidebar for CPU/RAM monitor
            self.sidebar_frame = tk.Frame(self.main_frame, bg="#e0e0e0", width=200)
            self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
            
            # CPU and RAM monitor
            self.system_monitor = CPURamMonitor(self.sidebar_frame)
            self.system_monitor.pack(fill=tk.Y, expand=True)
            
            # Right content area with notebook for tabs
            self.content_frame = tk.Frame(self.main_frame, bg="#e0e0e0")
            self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            # Set up styles before creating the notebook
            self.setup_styles()
            
            # Create notebook (tabbed interface)
            self.notebook = ttk.Notebook(self.content_frame)
            self.notebook.pack(fill=tk.BOTH, expand=True)
            
            # Tab 1: One Click Delete
            self.one_click_tab = tk.Frame(self.notebook, bg="#d4d4d4")
            self.notebook.add(self.one_click_tab, text="One Click Delete")
            self.setup_one_click_panel()
            
            # Tab 2: Selective Removal
            self.removal_tab = tk.Frame(self.notebook, bg="#d4d4d4")
            self.notebook.add(self.removal_tab, text="Selective Removal")
            
            # Selective Removal panel
            self.app_selection = AppSelectionFrame(
                self.removal_tab, 
                apps=SELECTABLE_APPS, 
                app_descriptions=APPS
            )
            self.app_selection.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Tab 3: Selective Reinstall
            self.reinstall_tab = tk.Frame(self.notebook, bg="#d4d4d4")
            self.notebook.add(self.reinstall_tab, text="Selective Reinstall")
            
            # Selective Reinstall panel
            self.app_reinstall = AppReinstallFrame(self.reinstall_tab)
            self.app_reinstall.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Add status bar
            self.status_bar = tk.Label(
                self, 
                text="Ready", 
                bd=1, 
                relief=tk.SUNKEN, 
                anchor=tk.W,
                bg="#e0e0e0",
                fg="#555555"
            )
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Start updating system monitor
            self.update_system_info()
            
            # Log application start
            logging.info("Application started")
        except Exception as e:
            logging.error(f"Error initializing application: {str(e)}")
            messagebox.showerror("Initialization Error", f"Error initializing the application: {str(e)}")
    
    def setup_styles(self):
        """Set up custom styles for the application."""
        try:
            style = ttk.Style()
            style.configure('TNotebook', background="#e0e0e0")
            style.configure('TNotebook.Tab', background="#d0d0d0", padding=[10, 2])
            style.map('TNotebook.Tab', background=[('selected', "#9e4e6a")], foreground=[('selected', 'white')])
            style.configure('Switch.TCheckbutton', background="#d4d4d4")
            style.configure('TCheckbutton', background="#d4d4d4")
        except Exception as e:
            logging.error(f"Error setting up styles: {str(e)}")

    def setup_one_click_panel(self):
        """Set up the One Click Delete panel with toggle switches and restore button"""
        try:
            # Panel title
            one_click_title = tk.Label(
                self.one_click_tab, 
                text="One click Delete", 
                font=("Arial", 16),
                bg="#d4d4d4"
            )
            one_click_title.pack(pady=10)
            
            # Toggle switches frame
            toggle_frame = tk.Frame(self.one_click_tab, bg="#d4d4d4")
            toggle_frame.pack(fill=tk.X, padx=20, pady=10)
            
            # Create toggle switches
            self.toggle_vars = {}
            toggle_categories = {
                "gaming_apps": "Gaming Apps",
                "microsoft_apps": "Microsoft Apps",
                "system_apps": "System Apps",
            }
            
            for key, value in toggle_categories.items():
                var = tk.BooleanVar(value=True)
                self.toggle_vars[key] = var
                
                switch_frame = tk.Frame(toggle_frame, bg="#d4d4d4")
                switch_frame.pack(fill=tk.X, pady=5)
                
                switch = ttk.Checkbutton(
                    switch_frame, 
                    text=value,
                    variable=var,
                    style="Switch.TCheckbutton"
                )
                switch.pack(side=tk.LEFT, padx=5)
                
                # Add a label that looks like the toggle background
                toggle_bg = tk.Label(
                    switch_frame, 
                    bg="#9e4e6a", 
                    width=4, 
                    height=1
                )
                toggle_bg.pack(side=tk.LEFT, padx=(10, 0))
            
            # Add spacer
            spacer = tk.Frame(self.one_click_tab, height=40, bg="#d4d4d4")
            spacer.pack(fill=tk.X)
            
            # Delete button (one-click delete)
            delete_button = tk.Button(
                self.one_click_tab,
                text="One click Delete",
                bg="#d4d4d4",
                font=("Arial", 12),
                relief=tk.GROOVE,
                command=self.one_click_delete
            )
            delete_button.pack(pady=10)
            
            # Add restore point frame
            self.restore_frame = RestorePointFrame(self.one_click_tab)
            self.restore_frame.pack(fill=tk.X, pady=20)
        except Exception as e:
            logging.error(f"Error setting up one-click panel: {str(e)}")
            messagebox.showerror("Setup Error", f"Error setting up one-click panel: {str(e)}")

    def one_click_delete(self):
        """Handle one-click delete functionality"""
        try:
            response = messagebox.askyesno(
                "Confirm Deletion",
                "Are you sure you want to remove all selected bloatware categories?\n\n"
                "This will remove all apps in the selected categories and cannot be undone."
            )
            
            if response:
                # Update status
                self.status_bar.config(text="Removing bloatware...")
                
                # Run in a separate thread to avoid freezing UI
                threading.Thread(target=self._run_one_click_delete, daemon=True).start()
        except Exception as e:
            logging.error(f"Error in one_click_delete: {str(e)}")
            messagebox.showerror("Error", f"Error initiating one-click delete: {str(e)}")
    
    def _run_one_click_delete(self):
        """Execute one-click delete in a separate thread"""
        try:
            # Create restore point first
            create_restore_point()
            
            # Call the actual removal function
            success = remove_unneeded_apps()
            
            # Update UI on main thread
            self.after(0, lambda: self._one_click_delete_complete(success))
        except Exception as e:
            logging.error(f"Error running one-click delete: {str(e)}")
            self.after(0, lambda: self.status_bar.config(text=f"Error: {str(e)[:50]}..."))
            self.after(0, lambda: messagebox.showerror("Error", f"Error running one-click delete: {str(e)}"))
    
    def _one_click_delete_complete(self, success):
        """Handle completion of one-click delete"""
        if success:
            self.status_bar.config(text="Bloatware removal complete")
            messagebox.showinfo("Deletion Complete", "All selected bloatware categories have been removed successfully.")
        else:
            self.status_bar.config(text="Bloatware removal failed")
            messagebox.showerror("Deletion Failed", "Failed to remove some or all bloatware. Check the log for details.")
    
    def update_system_info(self):
        """Update system information periodically"""
        try:
            self.system_monitor.update_values()
            # Update every 2 seconds
            self.after(2000, self.update_system_info)
        except Exception as e:
            logging.error(f"Error updating system info: {str(e)}")
            # Try again after a delay
            self.after(5000, self.update_system_info)

def show_error_and_exit(message):
    """Show error message and exit application"""
    import tkinter.messagebox as mb
    mb.showerror("Critical Error", message)
    logging.critical(message)
    sys.exit(1)

if __name__ == "__main__":
    try:
        # Configure custom styles for the app
        app = GamingDebloaterApp()
        app.mainloop()
    except Exception as e:
        error_message = f"Critical application error: {str(e)}"
        show_error_and_exit(error_message)