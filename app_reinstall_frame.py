import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
from restore import get_available_apps_for_reinstall, reinstall_selected_apps

class AppReinstallFrame(tk.Frame):
    """Frame for selecting apps to reinstall"""
    def __init__(self, parent):
        super().__init__(parent, bg="#d4d4d4")
        
        # Title
        self.title_label = tk.Label(
            self, 
            text="Selective Reinstall", 
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
        self.canvas_window = self.canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")
        
        # Status label
        self.status_label = tk.Label(
            self,
            text="Loading available apps...",
            font=("Arial", 10),
            bg="#d4d4d4",
            fg="#555555"
        )
        self.status_label.pack(pady=(0, 5))
        
        # Reload button
        self.reload_button = tk.Button(
            self,
            text="↻ Refresh List",
            font=("Arial", 10),
            bg="#d4d4d4",
            relief=tk.GROOVE,
            command=self._start_load_thread
        )
        self.reload_button.pack(pady=(0, 5))
        
        # Reinstall button
        self.reinstall_button = tk.Button(
            self,
            text="Reinstall Selected",
            font=("Arial", 12),
            bg="#d4d4d4",
            relief=tk.GROOVE,
            command=self.reinstall_selected
        )
        self.reinstall_button.pack(pady=10)
        
        # App checkboxes and variables
        self.app_vars = {}
        self.available_apps = {}
        
        # Bind canvas resize event
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Schedule loading after the window is initialized
        self.after(100, self._start_load_thread)
    
    def on_canvas_configure(self, event):
        """Update scrollregion when canvas is resized"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _start_load_thread(self):
        """Start a thread to load app data"""
        # Disable reload button
        self.reload_button.config(state=tk.DISABLED)
        self.status_label.config(text="Loading available apps...")
        
        # Start thread for loading data
        threading.Thread(target=self._load_app_data).start()
    
    def _load_app_data(self):
        """Load app data in a background thread"""
        try:
            # Get available apps without touching the UI
            apps = get_available_apps_for_reinstall()
            
            # Schedule UI update on main thread
            self.after(0, lambda: self._update_ui_with_apps(apps))
        except Exception as e:
            logging.error(f"Error loading available apps: {str(e)}")
            self.after(0, lambda e=e: self.status_label.config(
                text=f"Error loading apps: {str(e)}")
            )
            self.after(0, lambda: self.reload_button.config(state=tk.NORMAL))
    
    def _update_ui_with_apps(self, apps):
        """Update UI with loaded app data (called on main thread)"""
        try:
            self.available_apps = apps
            
            # Clear existing checkboxes
            for widget in self.checkbox_frame.winfo_children():
                widget.destroy()
            
            # Re-create all app variables (on the main thread)
            self.app_vars = {}
            
            # Create checkboxes for all apps
            for app_name, app_info in self.available_apps.items():
                var = tk.BooleanVar(value=False)
                self.app_vars[app_name] = var
                
                # Get description
                description = app_info["description"]
                installed = app_info["installed"]
                
                # Create a frame for each app
                app_frame = tk.Frame(self.checkbox_frame, bg="#d4d4d4", pady=2)
                app_frame.pack(fill=tk.X, padx=5)
                
                # Create checkbox
                checkbox = ttk.Checkbutton(
                    app_frame,
                    text=description,
                    variable=var,
                    style="TCheckbutton"
                )
                checkbox.pack(side=tk.LEFT)
                
                # Status label (installed or not)
                status_color = "#008000" if installed else "#800000"  # Green if installed, red if not
                status_text = "Installed" if installed else "Not Installed"
                
                status_label = tk.Label(
                    app_frame,
                    text=status_text,
                    font=("Arial", 8),
                    bg="#d4d4d4",
                    fg=status_color
                )
                status_label.pack(side=tk.RIGHT, padx=5)
            
            # Update status
            app_count = len(self.available_apps)
            installed_count = sum(1 for app_info in self.available_apps.values() if app_info["installed"])
            
            self.status_label.config(text=f"Found {app_count} apps ({installed_count} installed)")
            
            # Add 'Select All' and 'Select Missing' buttons
            buttons_frame = tk.Frame(self.checkbox_frame, bg="#d4d4d4", pady=5)
            buttons_frame.pack(fill=tk.X, padx=5)
            
            select_all_btn = tk.Button(
                buttons_frame,
                text="Select All",
                command=self.select_all_apps,
                relief=tk.GROOVE,
                bg="#d4d4d4",
                font=("Arial", 9)
            )
            select_all_btn.pack(side=tk.LEFT, padx=5)
            
            select_missing_btn = tk.Button(
                buttons_frame,
                text="Select Missing",
                command=self.select_missing_apps,
                relief=tk.GROOVE,
                bg="#d4d4d4",
                font=("Arial", 9)
            )
            select_missing_btn.pack(side=tk.LEFT, padx=5)
            
            clear_btn = tk.Button(
                buttons_frame,
                text="Clear All",
                command=self.clear_selection,
                relief=tk.GROOVE,
                bg="#d4d4d4",
                font=("Arial", 9)
            )
            clear_btn.pack(side=tk.LEFT, padx=5)
            
            # Update scrollregion after all checkboxes are added
            self.checkbox_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            logging.error(f"Error updating UI with apps: {str(e)}")
            self.status_label.config(text=f"Error: {str(e)}")
        finally:
            # Re-enable reload button
            self.reload_button.config(state=tk.NORMAL)
    
    def select_all_apps(self):
        """Select all apps"""
        for var in self.app_vars.values():
            var.set(True)
    
    def select_missing_apps(self):
        """Select only missing apps"""
        for app_name, var in self.app_vars.items():
            # Select if app is not installed
            var.set(not self.available_apps[app_name]["installed"])
    
    def clear_selection(self):
        """Clear all selections"""
        for var in self.app_vars.values():
            var.set(False)
    
    def reinstall_selected(self):
        """Reinstall selected apps"""
        # Get list of selected apps
        selected_apps = [app for app, var in self.app_vars.items() if var.get()]
        
        if not selected_apps:
            messagebox.showinfo("No Selection", "No apps were selected for reinstallation.")
            return
        
        # Confirm reinstall
        app_list = "\n".join([self.available_apps[app]["description"] for app in selected_apps])
        response = messagebox.askyesno(
            "Confirm Reinstall",
            f"Are you sure you want to reinstall the following apps?\n\n{app_list}"
        )
        
        if response:
            # Disable buttons during reinstallation
            self.status_label.config(text="Reinstalling selected apps... This may take a while.")
            self.reinstall_button.config(state=tk.DISABLED)
            self.reload_button.config(state=tk.DISABLED)
            
            # Start reinstallation in a separate thread
            threading.Thread(target=lambda: self._perform_reinstall(selected_apps)).start()
    
    def _perform_reinstall(self, selected_apps):
        """Perform the actual reinstall in a separate thread"""
        try:
            # Call the reinstall function
            success_count, failed_count = reinstall_selected_apps(selected_apps)
            
            # Show success message (needs to be run on the main thread)
            self.after(0, lambda: messagebox.showinfo(
                "Reinstall Complete",
                f"Successfully reinstalled {success_count} app(s).\n"
                f"Failed to reinstall {failed_count} app(s)."
            ))
            
            # Reload app list to show updated status
            self.after(0, self._start_load_thread)
                    
        except Exception as e:
            # Log the error
            logging.error(f"Error reinstalling apps: {str(e)}")
            
            # Show error message
            self.after(0, lambda: messagebox.showerror(
                "Error",
                f"An error occurred while reinstalling apps:\n{str(e)}"
            ))
            
            # Re-enable buttons
            self.after(0, lambda: self.status_label.config(text="Reinstall failed. Try again."))
            self.after(0, lambda: self.reinstall_button.config(state=tk.NORMAL))
            self.after(0, lambda: self.reload_button.config(state=tk.NORMAL))
        else:
            # Re-enable buttons
            self.after(0, lambda: self.status_label.config(text="Reinstall complete. Refresh list to see updates."))
            self.after(0, lambda: self.reinstall_button.config(state=tk.NORMAL))
            self.after(0, lambda: self.reload_button.config(state=tk.NORMAL))