import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
from app_actions import remove_selected_apps
from powershell_utils import ensure_admin
from restore import create_restore_point
from unused_apps import get_unused_apps

class UnusedAppsFrame(tk.Frame):
    """Frame for displaying and managing apps that haven't been used in a while"""
    def __init__(self, parent, days_threshold=90):
        super().__init__(parent, bg="#d4d4d4")
        
        # Store the days threshold
        self.days_threshold = days_threshold
        
        # Title
        self.title_label = tk.Label(
            self, 
            text=f"Unused Apps (Last {days_threshold} Days)", 
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
            text="Loading unused apps...",
            font=("Arial", 10),
            bg="#d4d4d4",
            fg="#555555"
        )
        self.status_label.pack(pady=(0, 5))
        
        # Refresh button
        self.refresh_button = tk.Button(
            self,
            text="↻ Refresh List",
            font=("Arial", 10),
            bg="#d4d4d4",
            relief=tk.GROOVE,
            command=self._start_scan_thread
        )
        self.refresh_button.pack(pady=(0, 5))
        
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
        
        # App checkboxes and variables
        self.app_vars = {}
        self.unused_apps = []
        
        # Bind canvas resize event
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Schedule loading after the window is initialized
        self.after(100, self._start_scan_thread)
    
    def on_canvas_configure(self, event):
        """Update scrollregion when canvas is resized"""
        try:
            self.canvas.itemconfig(self.canvas_window, width=event.width)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            logging.error(f"Error in on_canvas_configure: {str(e)}")
    
    def _start_scan_thread(self):
        """Start a thread to scan for unused apps"""
        try:
            # Disable refresh button
            self.refresh_button.config(state=tk.DISABLED)
            self.status_label.config(text=f"Scanning for apps unused for {self.days_threshold} days...")
            
            # Start thread for scanning
            threading.Thread(target=self._scan_unused_apps, daemon=True).start()
        except Exception as e:
            logging.error(f"Error starting unused apps scan thread: {str(e)}")
            self.status_label.config(text=f"Error: {str(e)[:50]}...")
            self.refresh_button.config(state=tk.NORMAL)
    
    def _scan_unused_apps(self):
        """Scan for unused apps in a background thread"""
        try:
            # Get unused apps
            unused_apps = get_unused_apps(self.days_threshold)
            
            # Schedule UI update on main thread
            self.after(0, lambda: self._update_ui_with_apps(unused_apps))
        except Exception as e:
            logging.error(f"Error scanning for unused apps: {str(e)}")
            self.after(0, lambda e=e: self.status_label.config(
                text=f"Error scanning for unused apps: {str(e)[:50]}..."
            ))
            self.after(0, lambda: self.refresh_button.config(state=tk.NORMAL))
    
    def _update_ui_with_apps(self, unused_apps):
        """Update UI with scanned unused apps (called on main thread)"""
        try:
            # Check for error
            if isinstance(unused_apps, dict) and "error" in unused_apps:
                self.status_label.config(text=f"Error: {unused_apps['error']}")
                return
            
            self.unused_apps = unused_apps
            
            # Clear existing checkboxes
            for widget in self.checkbox_frame.winfo_children():
                widget.destroy()
            
            # Re-create all app variables
            self.app_vars = {}
            
            # If no unused apps were found
            if not self.unused_apps:
                no_apps_label = tk.Label(
                    self.checkbox_frame,
                    text=f"No apps found that haven't been used in the last {self.days_threshold} days.",
                    font=("Arial", 10),
                    bg="#d4d4d4",
                    fg="#555555"
                )
                no_apps_label.pack(pady=20)
                
                self.status_label.config(text="No unused apps found")
            else:
                # Create checkboxes for all unused apps
                for app in self.unused_apps:
                    app_name = app["name"]
                    var = tk.BooleanVar(value=False)
                    self.app_vars[app_name] = var
                    
                    # Create a frame for each app
                    app_frame = tk.Frame(self.checkbox_frame, bg="#d4d4d4", pady=2)
                    app_frame.pack(fill=tk.X, padx=5)
                    
                    # Create checkbox
                    display_name = app.get("display_name", app_name)
                    checkbox = ttk.Checkbutton(
                        app_frame,
                        text=display_name,
                        variable=var,
                        style="TCheckbutton"
                    )
                    checkbox.pack(side=tk.LEFT)
                    
                    # Days since used label
                    days_text = f"{app['days_since_used']} days" if app['days_since_used'] != "Never or unknown" else "Never used"
                    days_label = tk.Label(
                        app_frame,
                        text=days_text,
                        font=("Arial", 8),
                        bg="#d4d4d4",
                        fg="#800000"  # Red color
                    )
                    days_label.pack(side=tk.RIGHT, padx=5)
                
                # Add 'Select All' and 'Clear All' buttons
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
                
                clear_btn = tk.Button(
                    buttons_frame,
                    text="Clear All",
                    command=self.clear_selection,
                    relief=tk.GROOVE,
                    bg="#d4d4d4",
                    font=("Arial", 9)
                )
                clear_btn.pack(side=tk.LEFT, padx=5)
                
                # Update status
                self.status_label.config(text=f"Found {len(self.unused_apps)} apps unused for {self.days_threshold}+ days")
            
            # Update scrollregion after all checkboxes are added
            self.checkbox_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            logging.error(f"Error updating UI with unused apps: {str(e)}")
            self.status_label.config(text=f"Error: {str(e)[:50]}...")
        finally:
            # Re-enable refresh button
            self.refresh_button.config(state=tk.NORMAL)
    
    def select_all_apps(self):
        """Select all unused apps"""
        try:
            for var in self.app_vars.values():
                var.set(True)
        except Exception as e:
            logging.error(f"Error in select_all_apps: {str(e)}")
    
    def clear_selection(self):
        """Clear all selections"""
        try:
            for var in self.app_vars.values():
                var.set(False)
        except Exception as e:
            logging.error(f"Error in clear_selection: {str(e)}")
    
    def remove_selected(self):
        """Remove selected unused apps"""
        try:
            # Check for admin privileges
            if not ensure_admin():
                messagebox.showwarning(
                    "Administrator Privileges Required",
                    "This operation requires administrator privileges.\n"
                    "Please restart the application as administrator."
                )
                return
            
            # Get list of selected apps
            selected_apps = [app_name for app_name, var in self.app_vars.items() if var.get()]
            
            if not selected_apps:
                messagebox.showinfo("No Selection", "No apps were selected for removal.")
                return
            
            # Get display names for selected apps for better user experience
            display_names = []
            for app_name in selected_apps:
                for app in self.unused_apps:
                    if app["name"] == app_name:
                        display_names.append(app.get("display_name", app_name))
                        break
            
            # Confirm removal
            app_list = "\n".join(display_names)
            response = messagebox.askyesno(
                "Confirm Removal",
                f"Are you sure you want to remove these unused apps?\n\n{app_list}"
            )
            
            if response:
                # Disable buttons during removal
                self.status_label.config(text="Removing selected apps... This may take a while.")
                self.remove_button.config(state=tk.DISABLED)
                self.refresh_button.config(state=tk.DISABLED)
                
                # Start removal in a separate thread
                threading.Thread(target=lambda: self._perform_removal(selected_apps), daemon=True).start()
        except Exception as e:
            logging.error(f"Error in remove_selected: {str(e)}")
            messagebox.showerror("Error", f"Error preparing to remove apps: {str(e)}")
    
    def _perform_removal(self, selected_apps):
        """Perform the actual removal in a separate thread"""
        try:
            # Create restore point first
            create_restore_point()
            
            # Call the removal function from app_actions.py
            success = remove_selected_apps(selected_apps)
            
            # Show success message (needs to be run on the main thread)
            self.after(0, lambda: messagebox.showinfo(
                "Removal Complete",
                f"Successfully removed {len(selected_apps)} unused app(s)."
            ))
            
            # Refresh unused apps list
            self.after(0, self._start_scan_thread)
                    
        except Exception as e:
            # Log the error
            logging.error(f"Error removing unused apps: {str(e)}")
            
            # Show error message
            self.after(0, lambda: messagebox.showerror(
                "Error",
                f"An error occurred while removing apps:\n{str(e)}"
            ))
            
            # Re-enable buttons
            self.after(0, lambda: self.status_label.config(text="Removal failed. Try again."))
            self.after(0, lambda: self.remove_button.config(state=tk.NORMAL))
            self.after(0, lambda: self.refresh_button.config(state=tk.NORMAL))
        else:
            # Re-enable buttons
            self.after(0, lambda: self.status_label.config(text="Removal complete. Refresh list to see updates."))
            self.after(0, lambda: self.remove_button.config(state=tk.NORMAL))
            self.after(0, lambda: self.refresh_button.config(state=tk.NORMAL))