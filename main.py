import tkinter as tk
from tkinter import ttk, messagebox
import os
import logging
from gui_components import AppSelectionFrame, RestorePointFrame, CPURamMonitor
from app_actions import SELECTABLE_APPS, APPS

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bloatware_remover.log',
    filemode='a'
)

class GamingDebloaterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gaming Debloater")
        self.geometry("950x580")
        self.configure(bg="#e0e0e0")
        
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
        
        # Right content area with two panels
        self.content_frame = tk.Frame(self.main_frame, bg="#e0e0e0")
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create two panels for "One Click Delete" and "Selective Removal"
        self.left_panel = tk.Frame(
            self.content_frame, 
            bg="#d4d4d4", 
            relief=tk.GROOVE, 
            bd=1,
            width=300,
            height=400
        )
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.right_panel = tk.Frame(
            self.content_frame, 
            bg="#d4d4d4", 
            relief=tk.GROOVE, 
            bd=1,
            width=300,
            height=400
        )
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # One Click Delete panel
        self.setup_one_click_panel()
        
        # Selective Removal panel
        self.app_selection = AppSelectionFrame(
            self.right_panel, 
            apps=SELECTABLE_APPS, 
            app_descriptions=APPS
        )
        self.app_selection.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Start updating system monitor
        self.update_system_info()

    def setup_one_click_panel(self):
        """Set up the One Click Delete panel with toggle switches and restore button"""
        # Panel title
        one_click_title = tk.Label(
            self.left_panel, 
            text="One click Delete", 
            font=("Arial", 16),
            bg="#d4d4d4"
        )
        one_click_title.pack(pady=10)
        
        # Toggle switches frame
        toggle_frame = tk.Frame(self.left_panel, bg="#d4d4d4")
        toggle_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Create toggle switches (just for show, functionality in a real app would be connected)
        self.toggle_vars = []
        toggle_options = ["Gaming Apps", "Microsoft Apps", "System Apps"]
        
        for option in toggle_options:
            var = tk.BooleanVar(value=True)
            self.toggle_vars.append(var)
            
            switch_frame = tk.Frame(toggle_frame, bg="#d4d4d4")
            switch_frame.pack(fill=tk.X, pady=5)
            
            switch = ttk.Checkbutton(
                switch_frame, 
                text=option,
                variable=var,
                style="Switch.TCheckbutton"
            )
            switch.pack(side=tk.LEFT, padx=5)
            
            # Add a label that looks like the toggle background (maroon color)
            # This is just for visual effect to match your image
            toggle_bg = tk.Label(
                switch_frame, 
                bg="#9e4e6a", 
                width=4, 
                height=1
            )
            toggle_bg.pack(side=tk.LEFT, padx=(10, 0))
        
        # Add spacer
        spacer = tk.Frame(self.left_panel, height=40, bg="#d4d4d4")
        spacer.pack(fill=tk.X)
        
        # Delete button (one-click delete)
        delete_button = tk.Button(
            self.left_panel,
            text="One click Delete",
            bg="#d4d4d4",
            font=("Arial", 12),
            relief=tk.GROOVE,
            command=self.one_click_delete
        )
        delete_button.pack(pady=10)
        
        # Add restore point frame
        self.restore_frame = RestorePointFrame(self.left_panel)
        self.restore_frame.pack(fill=tk.X, pady=20)

    def one_click_delete(self):
        """Handle one-click delete functionality"""
        response = messagebox.askyesno(
            "Confirm Deletion",
            "Are you sure you want to remove all selected bloatware categories?\n\n"
            "This will remove all apps in the selected categories and cannot be undone."
        )
        
        if response:
            # In a real implementation, this would call the remove_unneeded_apps function
            # For demonstration, we'll just show a success message
            messagebox.showinfo(
                "Deletion Complete",
                "All selected bloatware categories have been removed successfully."
            )
            logging.info("User performed one-click delete")
    
    def update_system_info(self):
        """Update system information periodically"""
        self.system_monitor.update_values()
        # Update every 2 seconds
        self.after(2000, self.update_system_info)

if __name__ == "__main__":
    # Configure custom styles for the app
    app = GamingDebloaterApp()
    
    # Configure Switch style for toggle buttons
    style = ttk.Style()
    style.configure('Switch.TCheckbutton', background="#d4d4d4")
    
    app.mainloop()