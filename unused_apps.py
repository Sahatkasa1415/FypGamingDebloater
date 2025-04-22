from powershell_utils import run_powershell, ensure_admin
import logging
import json
from datetime import datetime, timedelta

def get_unused_apps(days_threshold=90):
    """
    Get list of installed apps that haven't been used for a specified number of days.
    
    Args:
        days_threshold (int): Number of days to consider an app as "unused"
        
    Returns:
        list: List of dictionaries containing app info for unused apps
    """
    try:
        logging.info(f"Scanning for apps unused for {days_threshold} days")
        
        # Check for admin privileges (needed to access usage data)
        if not ensure_admin():
            logging.warning("Admin privileges required to scan app usage data")
            return {"error": "Admin privileges required"}
        
        # PowerShell command to get installed apps with their package info
        # We'll get installed modern apps and then check usage data for them
        ps_cmd = """
        # Get installed apps
        $installedApps = Get-AppxPackage -AllUsers | Select-Object Name, PackageFamilyName, DisplayName
        
        # Convert to JSON
        $installedApps | ConvertTo-Json
        """
        
        success, output = run_powershell(ps_cmd)
        if not success or not output:
            logging.error("Failed to get installed apps")
            return {"error": "Failed to get installed apps"}
        
        # Parse the installed apps
        installed_apps = json.loads(output)
        
        # If we just got one app, make sure we have a list
        if isinstance(installed_apps, dict):
            installed_apps = [installed_apps]
        
        # Now get app usage data from the registry
        ps_cmd_usage = """
        # Get app usage data from registry
        $usageData = Get-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Search\\RecentApps\\*" | 
            Select-Object PSChildName, LastAccessedTime, AppId, LaunchCount
                
        # Convert to JSON
        $usageData | ConvertTo-Json
        """
        
        success, usage_output = run_powershell(ps_cmd_usage)
        
        # Create a dictionary to hold usage data, keyed by app ID
        usage_data = {}
        current_date = datetime.now()
        
        if success and usage_output:
            try:
                usage_items = json.loads(usage_output)
                
                # Handle case of single item
                if isinstance(usage_items, dict):
                    usage_items = [usage_items]
                
                # Process usage data
                for item in usage_items:
                    if item and "AppId" in item and "LastAccessedTime" in item:
                        app_id = item["AppId"]
                        last_accessed = item["LastAccessedTime"]
                        
                        # Parse the filetime format if it exists
                        if last_accessed:
                            # Convert filetime to datetime
                            try:
                                # Parse 18-digit filetime if that's the format
                                if isinstance(last_accessed, int) or (isinstance(last_accessed, str) and last_accessed.isdigit() and len(last_accessed) >= 18):
                                    filetime = int(last_accessed)
                                    # Convert Windows filetime to Python datetime (minus 11644473600 seconds for Unix epoch difference)
                                    seconds_since_epoch = filetime / 10000000 - 11644473600
                                    last_date = datetime.fromtimestamp(seconds_since_epoch)
                                else:
                                    # Try to parse as a date string
                                    last_date = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
                                
                                days_since_used = (current_date - last_date).days
                                usage_data[app_id] = {
                                    "last_used": last_date.strftime("%Y-%m-%d %H:%M:%S"),
                                    "days_since_used": days_since_used,
                                    "launch_count": item.get("LaunchCount", 0)
                                }
                            except Exception as e:
                                logging.warning(f"Couldn't parse date for {app_id}: {e}")
            except Exception as e:
                logging.error(f"Error processing usage data: {str(e)}")
                # Continue with what we have
        
        # Get additional app usage data from Timeline (Activity History)
        ps_cmd_timeline = """
        # Get app usage data from Activity History
        try {
            $activities = Get-WinEvent -LogName "Microsoft-Windows-Application-Experience/Program-Inventory" -MaxEvents 1000 -ErrorAction SilentlyContinue |
                Where-Object { $_.Id -eq 500 -or $_.Id -eq 501 } |
                Select-Object TimeCreated, Message
                
            $activities | ConvertTo-Json
        } catch {
            Write-Output "[]"
        }
        """
        
        success, timeline_output = run_powershell(ps_cmd_timeline)
        
        if success and timeline_output and timeline_output != "[]":
            try:
                timeline_items = json.loads(timeline_output)
                
                # Handle case of single item
                if isinstance(timeline_items, dict):
                    timeline_items = [timeline_items]
                
                # Process timeline data
                for item in timeline_items:
                    if item and "Message" in item and "TimeCreated" in item:
                        # Extract app info from message
                        message = item["Message"]
                        if "Application Id=" in message:
                            app_id = message.split("Application Id=")[1].split(",")[0].strip()
                            time_created = item["TimeCreated"]
                            
                            # Parse the date if it exists
                            if time_created:
                                try:
                                    last_date = datetime.fromisoformat(time_created.replace('Z', '+00:00'))
                                    days_since_used = (current_date - last_date).days
                                    
                                    # Only update if this is more recent than existing data
                                    if app_id not in usage_data or days_since_used < usage_data[app_id]["days_since_used"]:
                                        usage_data[app_id] = {
                                            "last_used": last_date.strftime("%Y-%m-%d %H:%M:%S"),
                                            "days_since_used": days_since_used,
                                            "launch_count": 1  # We don't have this info from timeline
                                        }
                                except Exception as e:
                                    logging.warning(f"Couldn't parse timeline date for {app_id}: {e}")
            except Exception as e:
                logging.error(f"Error processing timeline data: {str(e)}")
                # Continue with what we have
        
        # Match usage data with installed apps
        unused_apps = []
        
        for app in installed_apps:
            # Skip system apps and framework packages
            if not app.get("Name") or "framework" in app.get("Name", "").lower():
                continue
                
            app_name = app.get("Name", "")
            display_name = app.get("DisplayName", app_name)
            
            # Check if we have usage data for this app
            app_id_to_check = f"App\\{app.get('PackageFamilyName', '')}"
            
            if app_id_to_check in usage_data:
                days_since_used = usage_data[app_id_to_check]["days_since_used"]
                
                # If app hasn't been used in threshold days, add to unused_apps
                if days_since_used >= days_threshold:
                    unused_apps.append({
                        "name": app_name,
                        "display_name": display_name,
                        "days_since_used": days_since_used,
                        "last_used": usage_data[app_id_to_check]["last_used"],
                        "launch_count": usage_data[app_id_to_check].get("launch_count", 0)
                    })
            else:
                # No usage data found, likely never used or usage not tracked
                # We'll consider it unused for our purposes
                unused_apps.append({
                    "name": app_name,
                    "display_name": display_name,
                    "days_since_used": days_threshold,  # Set to threshold as minimum
                    "last_used": "Never or unknown",
                    "launch_count": 0
                })
        
        # Sort by days since used (most unused first)
        unused_apps.sort(key=lambda x: x["days_since_used"], reverse=True)
        
        logging.info(f"Found {len(unused_apps)} apps unused for {days_threshold}+ days")
        return unused_apps
        
    except Exception as e:
        logging.error(f"Error in get_unused_apps: {str(e)}")
        return {"error": f"Error scanning for unused apps: {str(e)}"}