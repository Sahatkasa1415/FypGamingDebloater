import tkinter as tk
from tkinter import ttk, messagebox
import logging
import psutil
import threading
from app_actions import remove_selected_apps
from restore import create_restore_point

class CPURamMonitor(tk.Frame):
    """Widget to display CPU and RAM usage with circular progress indicators"""
    def __init__(self, parent):
        super().__init__(parent, bg="#e0e0e0")
        
        # CPU Frame
        self.cpu_frame = tk.Frame(self, bg="#e0e0e0")
        self.cpu_frame.pack(fill=tk.X, pady=10)
        
        self.cpu_label = tk.Label(
            self.cpu_frame, 
            text="CPU", 
            font=("Arial", 14),
            bg="#e0e0e0",
            fg="#555555"
        )
        self.cpu_label.pack(pady=5)
        
        # CPU canvas for drawing the circle
        self.cpu_canvas = tk.Canvas(
            self.cpu_frame, 
            width=150, 
            height=150, 
            bg="#e0e0e0",
            highlightthickness=0
        )
        self.cpu_canvas.pack(pady=5)
        
        # Draw CPU circle base (background)
        self.cpu_bg = self.cpu_canvas.create_oval(10, 10, 140, 140, outline="#d7c0c7", width=10)
        # CPU usage indicator (will be updated)
        self.cpu_indicator = self.cpu_canvas.create_arc(
            10, 10, 140, 140, 
            start=90, extent=0, 
            outline="#9e4e6a", 
            style=tk.ARC, 
            width=10
        )
        # CPU percentage text
        self.cpu_text = self.cpu_canvas.create_text(
            75, 75, 
            text="0%", 
            font=("Arial", 16, "bold"),
            fill="#555555"
        )
        
        # RAM Frame
        self.ram_frame = tk.Frame(self, bg="#e0e0e0")
        self.ram_frame.pack(fill=tk.X, pady=10)
        
        self.ram_label = tk.Label(
            self.ram_frame, 
            text="RAM", 
            font=("Arial", 14),
            bg="#e0e0e0",
            fg="#555555"
        )
        self.ram_label.pack(pady=5)
        
        # RAM canvas for drawing the circle
        self.ram_canvas = tk.Canvas(
            self.ram_frame, 
            width=150, 
            height=150, 
            bg="#e0e0e0",
            highlightthickness=0
        )
        self.ram_canvas.pack(pady=5)
        
        # Draw RAM circle base (background)
        self.ram_bg = self.ram_canvas.create_oval(10, 10, 140, 140, outline="#d7c0c7", width=10)
        # RAM usage indicator (will be updated)
        self.ram_indicator = self.ram_canvas.create_arc(
            10, 10, 140, 140, 
            start=90, extent=0, 
            outline="#9e4e6a", 
            style=tk.ARC, 
            width=10
        )
        # RAM percentage text
        self.ram_text = self.ram_canvas.create_text(
            75, 75, 
            text="0%", 
            font=("Arial", 16, "bold"),
            fill="#555555"
        )
    
    def update_values(self):
        """Update CPU and RAM usage values"""
        # Get CPU usage (average across all cores)
        cpu_percent = psutil.cpu_percent()
        # Get RAM usage
        ram_percent = psutil.virtual_memory().percent
        
        # Update CPU display
        self.cpu_canvas.itemconfig(self.cpu_indicator, extent=3.6 * cpu_percent)
        self.cpu_canvas.itemconfig(self.cpu_text, text=f"{int(cpu_percent)}%")
        
        # Update RAM display
        self.ram_canvas.itemconfig(self.ram_indicator, extent=3.6 * ram_percent)
        self.ram_canvas.itemconfig(self.ram_text, text=f"{int(ram_percent)}%")


class AppSelectionFrame(tk.Frame):
    """Frame for selecting apps to remove"""
    def __init__(self, parent, apps, app_descriptions):
        super().__init__(parent, bg="#d4d4d4")
        
        # Store the apps and their descriptions
        self.apps = apps
        self.app_descriptions = app_descriptions
        
        # Title
        self.title_label = tk.Label(
            self, 
            text="Selective Removal", 
            font=("Arial", 16),
            bg="#d4d4d4"
        )
        self.title_label.pack(pady=10)
        
        # Create a frame for the app list with scrollbar
        self.list_frame = tk.Frame(self, bg="#d4d4d4")
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbar
        self.scrollbar = tk.Scrollbar(self.list_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox-like container with checkboxes (using a Frame and Canvas for scrolling)
        self.canvas = tk.Canvas(
            self.list_frame, 
            bg="#d4d4d4",
            highlightthickness=0,
            yscrollcommand=self.scrollbar.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar.config(command=self.canvas.yview)
        
        # Frame inside canvas for checkboxes
        self.checkbox_frame = tk.Frame(self.canvas, bg="#d4d4d4")
        self.canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")
        
        # App checkboxes and variables
        self.app_vars = {}
        
        # Create checkboxes for all apps
        for app_name in self.apps:
            var = tk.BooleanVar(value=False)
            self.app_vars[app_name] = var
            
            # Get description if available
            description = self.app_descriptions[app_name]["description"] if app_name in self.app_descriptions and "description" in self.app_descriptions[app_name] else app_name
            
            # Create checkbox
            checkbox = ttk.Checkbutton(
                self.checkbox_frame,
                text=description,
                variable=var,
                style="TCheckbutton"
            )
            checkbox.pack(anchor="w", pady=2, padx=5)
        
        # Update scrollregion after all checkboxes are added
        self.checkbox_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        # Remove button
        self.remove_button = tk.Button(
            self,
            text="Remove Selected",
            font=("Arial", 12),
            bg="#d4d4d4",
            relief=tk.GROOVE,
            command=self.remove_selected
        )
        self.remove_button.pack(pady=10)
    
    def remove_selected(self):
        """Remove selected apps"""
        # Get list of selected apps
        selected_apps = [app for app, var in self.app_vars.items() if var.get()]
        
        if not selected_apps:
            messagebox.showinfo("No Selection", "No apps were selected for removal.")
            return
        
        # Confirm removal
        app_list = "\n".join([self.app_descriptions[app]["description"] if app in self.app_descriptions and "description" in self.app_descriptions[app] else app for app in selected_apps])
        response = messagebox.askyesno(
            "Confirm Removal",
            f"Are you sure you want to remove the following apps?\n\n{app_list}"
        )
        
        if response:
            # In a real implementation, this would be executed in a thread
            # to prevent UI freezing during the operation
            threading.Thread(target=lambda: self._perform_removal(selected_apps)).start()
    
    def _perform_removal(self, selected_apps):
        """Perform the actual removal in a separate thread"""
        try:
            # Call the removal function from app_actions.py
            remove_selected_apps(selected_apps)
            
            # Show success message (needs to be run on the main thread)
            self.after(0, lambda: messagebox.showinfo(
                "Removal Complete",
                f"Successfully removed {len(selected_apps)} app(s)."
            ))
            
            # Reset checkboxes for removed apps
            for app in selected_apps:
                if app in self.app_vars:
                    self.app_vars[app].set(False)
                    
        except Exception as e:
            # Log the error
            logging.error(f"Error removing apps: {str(e)}")
            
            # Show error message
            self.after(0, lambda: messagebox.showerror(
                "Error",
                f"An error occurred while removing apps:\n{str(e)}"
            ))


class RestorePointFrame(tk.Frame):
    """Frame for creating restore points"""
    def __init__(self, parent):
        super().__init__(parent, bg="#d4d4d4")
        
        # Restore Point button
        self.restore_button = tk.Button(
            self,
            text="Restore Point",
            font=("Arial", 12),
            bg="#d4d4d4",
            relief=tk.GROOVE,
            command=self.create_restore_point
        )
        self.restore_button.pack(pady=10)
    
    def create_restore_point(self):
        """Create a system restore point"""
        # Show a message that the operation is in progress
        messagebox.showinfo(
            "Restore Point",
            "Creating system restore point...\nThis may take a moment."
        )
        
        # Run the restore point creation in a separate thread
        threading.Thread(target=self._create_restore_point_thread).start()
    
    def _create_restore_point_thread(self):
        """Create restore point in a separate thread to not freeze the UI"""
        try:
            # Call the actual function from restore.py
            success = create_restore_point()
            
            if success:
                # Show success message (needs to be run on the main thread)
                self.after(0, lambda: messagebox.showinfo(
                    "Restore Point",
                    "System restore point created successfully."
                ))
            else:
                # Show error message
                self.after(0, lambda: messagebox.showerror(
                    "Restore Point Error",
                    "Failed to create system restore point.\nCheck the logs for more information."
                ))
                
        except Exception as e:
            # Log the error
            logging.error(f"Error creating restore point: {str(e)}")
            
            # Show error message
            self.after(0, lambda: messagebox.showerror(
                "Restore Point Error",
                f"An error occurred while creating restore point:\n{str(e)}"
            ))