import tkinter as tk
from tkinter import ttk, messagebox
import logging
import psutil
import threading
from app_actions import remove_selected_apps
from restore import create_restore_point, reinstall_selected_apps, get_available_apps_for_reinstall
from powershell_utils import ensure_admin

class CPURamMonitor(tk.Frame):
    """Widget to display CPU and RAM usage with circular progress indicators"""
    def __init__(self, parent):
        try:
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
        except Exception as e:
            logging.error(f"Error initializing CPURamMonitor: {str(e)}")
            # Create a minimal fallback UI if initialization fails
            label = tk.Label(self, text="System Monitor Unavailable", bg="#e0e0e0", fg="red")
            label.pack(pady=20)
    
    def update_values(self):
        """Update CPU and RAM usage values"""
        try:
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
        except Exception as e:
            # Log but don't crash on update errors
            logging.error(f"Error updating system monitor: {str(e)}")


class AppSelectionFrame(tk.Frame):
    """Frame for selecting apps to remove"""
    def __init__(self, parent, apps, app_descriptions):
        try:
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
            self.checkbox_window = self.canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")
            
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
            
            # Add category selection buttons
            self.button_frame = tk.Frame(self.checkbox_frame, bg="#d4d4d4")
            self.button_frame.pack(fill=tk.X, pady=10, padx=5)
            
            select_all_btn = tk.Button(
                self.button_frame,
                text="Select All",
                command=self.select_all,
                relief=tk.GROOVE,
                bg="#d4d4d4"
            )
            select_all_btn.pack(side=tk.LEFT, padx=5)
            
            select_none_btn = tk.Button(
                self.button_frame,
                text="Clear All",
                command=self.select_none,
                relief=tk.GROOVE,
                bg="#d4d4d4"
            )
            select_none_btn.pack(side=tk.LEFT, padx=5)
            
            # Update scrollregion after all checkboxes are added
            self.checkbox_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            
            # Bind canvas resize event
            self.canvas.bind("<Configure>", self.on_canvas_configure)
            
            # Status label
            self.status_label = tk.Label(
                self,
                text="Select apps to remove",
                font=("Arial", 10),
                bg="#d4d4d4",
                fg="#555555"
            )
            self.status_label.pack(pady=5)
            
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
        except Exception as e:
            logging.error(f"Error initializing AppSelectionFrame: {str(e)}")
            # Create a minimal fallback UI if initialization fails
            label = tk.Label(self, text=f"Error loading app selection: {str(e)}", bg="#d4d4d4", fg="red")
            label.pack(pady=20)
    
    def on_canvas_configure(self, event):
        """Update scrollregion when canvas is resized"""
        try:
            self.canvas.itemconfig(self.checkbox_window, width=event.width)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            logging.error(f"Error in on_canvas_configure: {str(e)}")
    
    def select_all(self):
        """Select all apps"""
        try:
            for var in self.app_vars.values():
                var.set(True)
        except Exception as e:
            logging.error(f"Error in select_all: {str(e)}")
    
    def select_none(self):
        """Deselect all apps"""
        try:
            for var in self.app_vars.values():
                var.set(False)
        except Exception as e:
            logging.error(f"Error in select_none: {str(e)}")
    
    def remove_selected(self):
        """Remove selected apps"""
        try:
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
                # Check for admin privileges
                if not ensure_admin():
                    messagebox.showwarning(
                        "Administrator Privileges Required",
                        "This operation requires administrator privileges.\n"
                        "Please restart the application as administrator."
                    )
                    return
                
                # Update status
                self.status_label.config(text="Removing apps... Please wait.")
                self.remove_button.config(state=tk.DISABLED)
                
                # Start thread for removal
                threading.Thread(target=lambda: self._perform_removal(selected_apps), daemon=True).start()
        except Exception as e:
            logging.error(f"Error in remove_selected: {str(e)}")
            messagebox.showerror("Error", f"Error preparing to remove apps: {str(e)}")
    
    def _perform_removal(self, selected_apps):
        """Perform the actual removal in a separate thread"""
        try:
            # Create restore point first (just in case)
            create_restore_point()
            
            # Call the removal function from app_actions.py
            success = remove_selected_apps(selected_apps)
            
            # Update UI on main thread
            self.after(0, lambda: self._removal_complete(success, selected_apps))
        except Exception as e:
            logging.error(f"Error removing apps: {str(e)}")
            self.after(0, lambda: self.status_label.config(text=f"Error removing apps"))
            self.after(0, lambda: self.remove_button.config(state=tk.NORMAL))
            self.after(0, lambda: messagebox.showerror("Error", f"Error removing apps: {str(e)}"))
    
    def _removal_complete(self, success, selected_apps):
        """Handle completion of app removal"""
        try:
            if success:
                self.status_label.config(text="Removal complete")
                messagebox.showinfo(
                    "Removal Complete",
                    f"Successfully removed {len(selected_apps)} app(s)."
                )
                
                # Reset checkboxes for removed apps
                for app in selected_apps:
                    if app in self.app_vars:
                        self.app_vars[app].set(False)
            else:
                self.status_label.config(text="Removal failed")
                messagebox.showerror(
                    "Removal Failed", 
                    "Failed to remove some or all apps. Check the log for details."
                )
        except Exception as e:
            logging.error(f"Error in _removal_complete: {str(e)}")
        finally:
            # Re-enable the button
            self.remove_button.config(state=tk.NORMAL)


class RestorePointFrame(tk.Frame):
    """Frame for creating restore points"""
    def __init__(self, parent):
        try:
            super().__init__(parent, bg="#d4d4d4")
            
            # Title
            self.title_label = tk.Label(
                self, 
                text="System Protection", 
                font=("Arial", 14),
                bg="#d4d4d4"
            )
            self.title_label.pack(pady=(10, 5))
            
            # Description
            self.desc_label = tk.Label(
                self,
                text="Create a system restore point to revert changes if needed",
                font=("Arial", 10),
                bg="#d4d4d4",
                fg="#555555"
            )
            self.desc_label.pack(pady=(0, 10))
            
            # Restore Point button
            self.restore_button = tk.Button(
                self,
                text="Create Restore Point",
                font=("Arial", 12),
                bg="#d4d4d4",
                relief=tk.GROOVE,
                command=self.create_restore_point
            )
            self.restore_button.pack(pady=10)
            
            # Status label
            self.status_label = tk.Label(
                self,
                text="",
                font=("Arial", 10),
                bg="#d4d4d4",
                fg="#555555"
            )
            self.status_label.pack(pady=(0, 10))
        except Exception as e:
            logging.error(f"Error initializing RestorePointFrame: {str(e)}")
            # Create a minimal fallback UI if initialization fails
            label = tk.Label(self, text=f"Error loading restore point panel: {str(e)}", bg="#d4d4d4", fg="red")
            label.pack(pady=20)
    
    def create_restore_point(self):
        """Create a system restore point"""
        try:
            # Check for admin privileges
            if not ensure_admin():
                messagebox.showwarning(
                    "Administrator Privileges Required",
                    "Creating a restore point requires administrator privileges.\n"
                    "Please restart the application as administrator."
                )
                return
            
            # Update UI
            self.status_label.config(text="Creating restore point...")
            self.restore_button.config(state=tk.DISABLED)
            
            # Show a message that the operation is in progress
            messagebox.showinfo(
                "Restore Point",
                "Creating system restore point...\nThis may take a moment."
            )
            
            # Run the restore point creation in a separate thread
            threading.Thread(target=self._create_restore_point_thread, daemon=True).start()
        except Exception as e:
            logging.error(f"Error preparing to create restore point: {str(e)}")
            self.status_label.config(text=f"Error: {str(e)[:50]}...")
            messagebox.showerror("Error", f"Error preparing to create restore point: {str(e)}")
    
    def _create_restore_point_thread(self):
        """Create restore point in a separate thread to not freeze the UI"""
        try:
            # Call the actual function from restore.py
            success = create_restore_point()
            
            # Update UI on main thread
            self.after(0, lambda: self._restore_point_complete(success))
        except Exception as e:
            logging.error(f"Error creating restore point: {str(e)}")
            self.after(0, lambda: self.status_label.config(text=f"Error: {str(e)[:50]}..."))
            self.after(0, lambda: self.restore_button.config(state=tk.NORMAL))
            self.after(0, lambda: messagebox.showerror(
                "Restore Point Error",
                f"An error occurred while creating restore point:\n{str(e)}"
            ))
    
    def _restore_point_complete(self, success):
        """Handle completion of restore point creation"""
        try:
            if success:
                self.status_label.config(text="Restore point created successfully")
                messagebox.showinfo(
                    "Restore Point",
                    "System restore point created successfully."
                )
            else:
                self.status_label.config(text="Failed to create restore point")
                messagebox.showerror(
                    "Restore Point Error",
                    "Failed to create system restore point.\nCheck the logs for more information."
                )
        except Exception as e:
            logging.error(f"Error in _restore_point_complete: {str(e)}")
        finally:
            # Re-enable the button
            self.restore_button.config(state=tk.NORMAL)


class AppReinstallFrame(tk.Frame):
    """Frame for selecting apps to reinstall"""
    def __init__(self, parent):
        try:
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
        except Exception as e:
            logging.error(f"Error initializing AppReinstallFrame: {str(e)}")
            # Create a minimal fallback UI if initialization fails
            label = tk.Label(self, text=f"Error loading app reinstall panel: {str(e)}", bg="#d4d4d4", fg="red")
            label.pack(pady=20)
    
    def on_canvas_configure(self, event):
        """Update scrollregion when canvas is resized"""
        try:
            self.canvas.itemconfig(self.canvas_window, width=event.width)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            logging.error(f"Error in on_canvas_configure: {str(e)}")
    
    def _start_load_thread(self):
        """Start a thread to load app data"""
        try:
            # Disable reload button
            self.reload_button.config(state=tk.DISABLED)
            self.status_label.config(text="Loading available apps...")
            
            # Start thread for loading data
            threading.Thread(target=self._load_app_data, daemon=True).start()
        except Exception as e:
            logging.error(f"Error starting load thread: {str(e)}")
            self.status_label.config(text=f"Error: {str(e)[:50]}...")
            self.reload_button.config(state=tk.NORMAL)
    
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
                text=f"Error loading apps: {str(e)[:50]}..."
            ))
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
            self.status_label.config(text=f"Error updating apps: {str(e)[:50]}...")
        finally:
            # Re-enable reload button
            self.reload_button.config(state=tk.NORMAL)
    
    def select_all_apps(self):
        """Select all apps"""
        try:
            for var in self.app_vars.values():
                var.set(True)
        except Exception as e:
            logging.error(f"Error in select_all_apps: {str(e)}")
    
    def select_missing_apps(self):
        """Select only missing apps"""
        try:
            for app_name, var in self.app_vars.items():
                # Select if app is not installed
                var.set(not self.available_apps[app_name]["installed"])
        except Exception as e:
            logging.error(f"Error in select_missing_apps: {str(e)}")
    
    def clear_selection(self):
        """Clear all selections"""
        try:
            for var in self.app_vars.values():
                var.set(False)
        except Exception as e:
            logging.error(f"Error in clear_selection: {str(e)}")
    
    def reinstall_selected(self):
        """Reinstall selected apps"""
        try:
            # Check for admin privileges
            if not ensure_admin():
                messagebox.showwarning(
                    "Administrator Privileges Required",
                    "App reinstallation requires administrator privileges.\n"
                    "Please restart the application as administrator."
                )
                return
            
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
                threading.Thread(target=lambda: self._perform_reinstall(selected_apps), daemon=True).start()
        except Exception as e:
            logging.error(f"Error preparing to reinstall apps: {str(e)}")
            messagebox.showerror("Error", f"Error preparing to reinstall apps: {str(e)}")
    
    def _perform_reinstall(self, selected_apps):
        """Perform the actual reinstall in a separate thread"""
        try:
            # Create restore point first
            create_restore_point()
            
            # Call the reinstall function
            success_count, failed_count = reinstall_selected_apps(selected_apps)
            
            # Update UI on main thread
            self.after(0, lambda count1=success_count, count2=failed_count: self._reinstall_complete(count1, count2))
        except Exception as e:
            logging.error(f"Error reinstalling apps: {str(e)}")
            
            # Show error message on main thread
            self.after(0, lambda msg=str(e): messagebox.showerror(
                "Error",
                f"An error occurred while reinstalling apps:\n{msg}"
            ))
            
            # Re-enable buttons on main thread
            self.after(0, lambda: self.status_label.config(text="Reinstall failed. Try again."))
            self.after(0, lambda: self.reinstall_button.config(state=tk.NORMAL))
            self.after(0, lambda: self.reload_button.config(state=tk.NORMAL))
    
    def _reinstall_complete(self, success_count, failed_count):
        """Handle completion of app reinstallation"""
        try:
            # Show success message
            messagebox.showinfo(
                "Reinstall Complete",
                f"Successfully reinstalled {success_count} app(s).\n"
                f"Failed to reinstall {failed_count} app(s)."
            )
            
            # Reload app list to show updated status
            self._start_load_thread()
        except Exception as e:
            logging.error(f"Error in _reinstall_complete: {str(e)}")
            self.status_label.config(text="Error updating status after reinstall")
        finally:
            # Re-enable buttons
            self.reinstall_button.config(state=tk.NORMAL)
            self.reload_button.config(state=tk.NORMAL)