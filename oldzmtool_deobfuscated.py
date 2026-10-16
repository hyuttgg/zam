# ==============================================================================
# Old ZM Tool v9.0.0 - Full Deobfuscated Source Code
# Reverse Engineered by Antigravity from obf-oldzmtool.py
# Original Author: zam2109shop.com
# ==============================================================================

import os
import sys
import gc
import time
import json
import random
import shutil
import sqlite3
import requests
import traceback
import subprocess
import threading
from threading import Lock, Event
from datetime import datetime, timezone
import pytz
import psutil
from psutil import (
    boot_time,
    process_iter,
    cpu_percent,
    virtual_memory,
    Process,
    NoSuchProcess,
    AccessDenied,
    ZombieProcess,
)
from prettytable import PrettyTable
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console

# ------------------------------------------------------------------------------
# Global Variables & Locks
# ------------------------------------------------------------------------------

package_lock = Lock()
status_lock = Lock()
rejoin_lock = Lock()

bot_instance = None
bot_thread = None
socket_server = None

stop_webhook_thread = False
webhook_thread = None
webhook_url = None
device_name = None
webhook_interval = None
reset_tab_interval = None
close_and_rejoin_delay = 5

boot_time_val = boot_time()

auto_android_id_enabled = False
auto_android_id_thread = None
auto_android_id_value = None

package_statuses = {}

SERVER_LINKS_FILE = "zam2109shop.com/server-links.txt"
ACCOUNTS_FILE = "zam2109shop.com/accounts.txt"
CONFIG_FILE = "zam2109shop.com/config.json"
version = "9.0.0 | Created By zam2109shop.com | Bản hoàn chỉnh"

# Executors Mapping
executors = {
    'Trigon': '/storage/emulated/0/Trigon/',
    'FrostWare': '/storage/emulated/0/FrostWare/',
    'Evon': '/storage/emulated/0/Evon/',
    'KRNL': '/storage/emulated/0/PunkX/',
    'Delta': '/storage/emulated/0/Delta/',
    'Cryptic': '/storage/emulated/0/Cryptic/',
}

# Add clones for RonixExploit, RonixExploit VNG, Delta, Cryptic, FrostWare
for i in range(1, 21):
    clone_str = f"{i:03d}"
    executors[f"RonixExploit Clone {clone_str}"] = f"/storage/emulated/0/RobloxClone{clone_str}/RonixExploit/"
    executors[f"RonixExploit VNG Clone {clone_str}"] = f"/storage/emulated/0/RobloxVNGClone{clone_str}/RonixExploit/"
    executors[f"Delta Clone {clone_str}"] = f"/storage/emulated/0/RobloxClone{clone_str}/Delta/"
    executors[f"Cryptic Clone {clone_str}"] = f"/storage/emulated/0/RobloxClone{clone_str}/Cryptic/"
    executors[f"FrostWare Clone {clone_str}"] = f"/storage/emulated/0/RobloxClone{clone_str}/FrostWare/"

# Workspace paths
workspace_paths = [
    os.path.join(path, "Workspace") for path in executors.values()
] + [
    os.path.join(path, "workspace") for path in executors.values()
]

# Ensure directory exists
os.makedirs("zam2109shop.com", exist_ok=True)


# ------------------------------------------------------------------------------
# Class: Utilities
# ------------------------------------------------------------------------------

class Utilities:
    @staticmethod
    def collect_garbage():
        gc.collect()

    @staticmethod
    def log_error(error_message):
        try:
            with open("error_log.txt", "a", encoding="utf-8") as f:
                f.write(str(error_message) + "\n\n")
        except Exception:
            pass

    @staticmethod
    def clear_screen():
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def get_hwid_codex():
        try:
            result = subprocess.run(
                ["settings", "get", "secure", "android_id"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    @staticmethod
    def calculate_time_left(expiry_timestamp):
        current_time = int(time.time())
        time_left = expiry_timestamp - current_time
        return time_left

    @staticmethod
    def format_time_left(time_left):
        hours, remainder = divmod(time_left, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02} hour(s) {int(minutes):02} minute(s) {int(seconds):02} second(s)"

    @staticmethod
    def convert_to_ho_chi_minh_time(expiry_timestamp):
        ho_chi_minh_tz = pytz.timezone("Asia/Ho_Chi_Minh")
        expiry_datetime = datetime.fromtimestamp(expiry_timestamp, pytz.utc)
        expiry_datetime = expiry_datetime.astimezone(ho_chi_minh_tz)
        return expiry_datetime.strftime("%Y-%m-%d %H:%M:%S")


# ------------------------------------------------------------------------------
# Class: SystemMonitor
# ------------------------------------------------------------------------------

class SystemMonitor:
    @staticmethod
    def capture_screenshot():
        try:
            screenshot_path = "/storage/emulated/0/Download/screenshot.png"
            os.system(f"/system/bin/screencap -p {screenshot_path}")
            if not os.path.exists(screenshot_path):
                raise FileNotFoundError("Screenshot file was not created.")
            return screenshot_path
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Error capturing screenshot: {e}\033[0m")
            Utilities.log_error(f"Error capturing screenshot: {e}")
            return None

    @staticmethod
    def get_uptime():
        current_time = time.time()
        uptime_seconds = current_time - psutil.boot_time()
        days = int(uptime_seconds // (24 * 3600))
        hours = int((uptime_seconds % (24 * 3600)) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"

    @staticmethod
    def roblox_processes():
        package_names = []
        for proc in process_iter(["pid", "name", "cmdline", "memory_info"]):
            try:
                name = proc.info.get("name") or ""
                cmdline = " ".join(proc.info.get("cmdline") or [])
                package_name = None
                config = FileManager._load_config()
                prefix = config.get("package_prefix", "com.roblox")

                if prefix in name:
                    package_name = name
                elif prefix in cmdline:
                    for part in proc.info.get("cmdline") or []:
                        if prefix in part:
                            package_name = part
                            break

                if package_name:
                    mem_usage = proc.info["memory_info"].rss / (1024 ** 2)
                    mem_usage_rounded = round(mem_usage, 2)
                    cpu_usage = proc.cpu_percent(interval=0.1) / (psutil.cpu_count(logical=True) or 1)
                    cpu_usage_rounded = round(cpu_usage, 2)
                    full_name = package_name
                    package_names.append(
                        f"{full_name} (PID: {proc.pid}, CPU: {cpu_usage_rounded}%, MEM: {mem_usage_rounded}MB)"
                    )
            except (NoSuchProcess, AccessDenied, ZombieProcess):
                continue
        return package_names

    @staticmethod
    def get_memory_usage():
        try:
            process = Process(os.getpid())
            mem_info = process.memory_info()
            mem_usage_mb = mem_info.rss / (1024 ** 2)
            return round(mem_usage_mb, 2)
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Error getting memory usage: {e}\033[0m")
            Utilities.log_error(f"Error getting memory usage: {e}")
            return None

    @staticmethod
    def get_system_info():
        try:
            cpu_usage = cpu_percent(interval=1)
            memory_info = virtual_memory()
            system_info = {
                "cpu_usage": cpu_usage,
                "memory_total": round(memory_info.total / (1024 ** 3), 2),
                "memory_used": round(memory_info.used / (1024 ** 3), 2),
                "memory_percent": memory_info.percent,
                "uptime": SystemMonitor.get_uptime(),
                "roblox_packages": SystemMonitor.roblox_processes(),
            }
            return system_info
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Error retrieving system information: {e}\033[0m")
            Utilities.log_error(f"Error retrieving system information: {e}")
            return None


# ------------------------------------------------------------------------------
# Class: FileManager
# ------------------------------------------------------------------------------

class FileManager:
    @staticmethod
    def setup_user_ids():
        print("\033[1;32m[ zam2109shop.com ] - Auto-detecting User IDs from app packages...\033[0m")
        packages = RobloxManager.get_roblox_packages()
        if not packages:
            print("\033[1;31m[ zam2109shop.com ] - No Roblox packages detected to set up User IDs.\033[0m")
            return

        accounts = {}
        for package_name in packages:
            file_path = f"/data/data/{package_name}/files/appData/LocalStorage/appStorage.json"
            user_id = FileManager.find_userid_from_file(file_path)
            if user_id and user_id != "-1":
                accounts[package_name] = user_id
                print(f"\033[96m[ zam2109shop.com ] - Found UserID for {package_name}: {user_id}\033[0m")
            else:
                print(f"\033[1;31m[ zam2109shop.com ] - UserID not found for {package_name}.\033[0m")

        if accounts:
            FileManager.save_accounts(accounts)
            print("\033[1;32m[ zam2109shop.com ] - User IDs have been successfully saved.\033[0m")
        else:
            print("\033[1;31m[ zam2109shop.com ] - Could not find any valid User IDs to set up.\033[0m")

    @staticmethod
    def save_server_links(server_links):
        try:
            with open(SERVER_LINKS_FILE, "w", encoding="utf-8") as file:
                for package, link in server_links.items():
                    file.write(f"{package},{link}\n")
            print("\033[1;32m[ zam2109shop.com ] - Server links saved successfully.\033[0m")
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Error saving server links: {e}\033[0m")
            Utilities.log_error(f"Error saving server links: {e}")

    @staticmethod
    def load_server_links():
        server_links = {}
        if not os.path.exists(SERVER_LINKS_FILE):
            return server_links
        try:
            with open(SERVER_LINKS_FILE, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if "," in line:
                        package, link = line.split(",", 1)
                        server_links[package.strip()] = link.strip()
        except Exception:
            pass
        return server_links

    @staticmethod
    def save_accounts(accounts):
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as file:
            for package, user_id in accounts.items():
                file.write(f"{package},{user_id}\n")

    @staticmethod
    def load_accounts():
        accounts = {}
        if not os.path.exists(ACCOUNTS_FILE):
            return accounts
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if "," in line:
                        package, user_id = line.split(",", 1)
                        accounts[package.strip()] = user_id.strip()
                    elif line:
                        print(f"\033[1;31m[ zam2109shop.com ] - Invalid line format: {line}. Expected format 'package,user_id'.\033[0m")
        except Exception:
            pass
        return accounts

    @staticmethod
    def find_userid_from_file(file_path):
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()
                needle = '"UserId":"'
                if needle in content:
                    userid_start = content.index(needle) + len(needle)
                    userid_end = content.find('"', userid_start)
                    if userid_end != -1:
                        return content[userid_start:userid_end]
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Error reading file: {e}\033[0m")
        return None

    @staticmethod
    def get_username(user_id):
        retry_attempts = 3
        for attempt in range(1, retry_attempts + 1):
            try:
                url = f"https://users.roblox.com/v1/users/{user_id}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("name", "Unknown")
            except Exception as e:
                print(f"\033[1;31m[ zam2109shop.com ] - Attempt {attempt} failed for Roblox Users API: {e}\033[0m")

            try:
                url = f"https://users.roproxy.com/v1/users/{user_id}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("name", "Unknown")
            except Exception as e:
                print(f"\033[1;31m[ zam2109shop.com ] - Attempt {attempt} failed for RoProxy API: {e}\033[0m")

        return "Unknown"

    @staticmethod
    def save_username(user_id, username):
        file_path = "usernames.json"
        data = {}
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
            data[str(user_id)] = username
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Error saving username: {e}\033[0m")

    @staticmethod
    def load_saved_username(user_id):
        file_path = "usernames.json"
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    return data.get(str(user_id))
            except Exception as e:
                print(f"\033[1;31m[ zam2109shop.com ] - Error loading username: {e}\033[0m")
        return None

    @staticmethod
    def download_file(url, destination, binary=False):
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                mode = "wb" if binary else "w"
                with open(destination, mode) as file:
                    if binary:
                        file.write(response.content)
                    else:
                        file.write(response.text)
                print(f"\033[1;32m[ zam2109shop.com ] - {destination} downloaded successfully.\033[0m")
                return True
            else:
                error_message = f"Failed to download {destination}. Status code: {response.status_code}"
                print(f"\033[1;31m[ zam2109shop.com ] - {error_message}\033[0m")
                return False
        except requests.RequestException as e:
            error_message = f"Request exception while downloading {destination}: {e}"
            print(f"\033[1;31m[ zam2109shop.com ] - {error_message}\033[0m")
            return False
        except Exception as e:
            error_message = f"Unexpected error while downloading {destination}: {e}"
            print(f"\033[1;31m[ zam2109shop.com ] - {error_message}\033[0m")
            return False

    @staticmethod
    def _load_config():
        config = {
            "webhook_url": "",
            "device_name": "",
            "interval": "inf",
            "disable_ui": "0",
            "check_executor": "1",
            "command_8_configured": False,
            "lua_script_template": 'task.spawn(function()local a=tostring(game.Players.LocalPlayer.UserId)..".main"while true do pcall(function()if isfile(a)then delfile(a)end writefile(a,"https://discord.gg/3f6SUbGneC")end)task.wait(1)end end)',
            "package_prefix": "com.roblox",
            "close_and_rejoin_delay": 5,
            "reset_tab_interval": "inf",
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                    loaded = json.load(file)
                    config.update(loaded)
            except Exception as e:
                print(f"\033[1;31m[ zam2109shop.com ] - Error loading configuration: {e}\033[0m")
                Utilities.log_error(f"Error loading configuration: {e}")
        return config

    @staticmethod
    def save_config(config_data=None):
        try:
            current_config = FileManager._load_config()
            if config_data:
                current_config.update(config_data)
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                json.dump(current_config, file, indent=4)
            print("\033[1;32m[ zam2109shop.com ] - Configuration saved successfully.\033[0m")
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Error saving configuration: {e}\033[0m")
            Utilities.log_error(f"Error saving configuration: {e}")

    @staticmethod
    def check_and_create_cookie_file():
        cookie_file_path = "cookie.txt"
        if not os.path.exists(cookie_file_path):
            with open(cookie_file_path, "w", encoding="utf-8") as f:
                pass


# ------------------------------------------------------------------------------
# Class: RobloxManager
# ------------------------------------------------------------------------------

class RobloxManager:
    @staticmethod
    def get_cookie():
        cookie_txt_path = "cookie.txt"
        new_dir_path = "zam2109shop.com/Shoụko.dev - Data"
        new_cookie_path = os.path.join(new_dir_path, "cookie.txt")

        if not os.path.exists(cookie_txt_path):
            if os.path.exists(new_cookie_path):
                shutil.copy(new_cookie_path, cookie_txt_path)
            else:
                print("\033[1;31m[ zam2109shop.com ] - cookie.txt not found in the current directory!\033[0m")
                Utilities.log_error("cookie.txt not found in the current directory.")
                return []

        cookies = []
        try:
            with open(cookie_txt_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            valid_lines = []
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue
                if "_|WARNING:" in line_str:
                    parts = line_str.split(":")
                    ck = parts[-1] if len(parts) > 1 else line_str
                    cookies.append(ck)
                    valid_lines.append(line_str)
                elif ":" in line_str:
                    parts = line_str.split(":")
                    if len(parts) >= 3:
                        cookies.append(parts[2])
                    valid_lines.append(line_str)

            if not cookies:
                print("\033[1;31m[ zam2109shop.com ] - No valid cookies found in cookie.txt. Please add cookies.\033[0m")
                Utilities.log_error("No valid cookies found in cookie.txt.")
                return []

            return cookies
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Error: {e}\033[0m")
            Utilities.log_error(f"Error in get_cookie: {e}")
            return []

    @staticmethod
    def verify_cookie(cookie_value):
        headers = {
            "Cookie": f".ROBLOSECURITY={cookie_value}",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
            "Referer": "https://www.roblox.com/",
            "Origin": "https://www.roblox.com",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        try:
            response = requests.get(
                "https://users.roblox.com/v1/users/authenticated",
                headers=headers,
                timeout=10,
            )
            if response.status_code == 200:
                print("\033[1;32m[ zam2109shop.com ] - Cookie is valid! User is authenticated.\033[0m")
                return response.json().get("id")
            else:
                print("\033[1;31m[ zam2109shop.com ] - Invalid cookie. The user is not authenticated.\033[0m")
                return None
        except requests.RequestException as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Request exception occurred while verifying cookie: {e}\033[0m")
            return None
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Unexpected exception occurred while verifying cookie: {e}\033[0m")
            return None

    @staticmethod
    def check_user_online(user_id, cookie):
        max_retries = 3
        delay = 2
        body = {"userIds": [int(user_id)]}
        headers = {
            "Content-Type": "application/json",
            "Cookie": f".ROBLOSECURITY={cookie}",
        }

        for attempt in range(1, max_retries + 1):
            try:
                session = requests.Session()
                primary_response = session.post(
                    "https://presence.roblox.com/v1/presence/users",
                    json=body,
                    headers=headers,
                    timeout=5,
                )
                if primary_response.status_code == 200:
                    primary_data = primary_response.json()
                    presences = primary_data.get("userPresences", [])
                    if presences:
                        return presences[0].get("userPresenceType", 0)
            except Exception as e:
                pass

            try:
                roproxy_response = requests.post(
                    "https://presence.roproxy.com/v1/presence/users",
                    json=body,
                    headers={"Content-Type": "application/json"},
                    timeout=5,
                )
                if roproxy_response.status_code == 200:
                    data = roproxy_response.json()
                    presences = data.get("userPresences", [])
                    if presences:
                        return presences[0].get("userPresenceType", 0)
            except Exception as e:
                pass

            time.sleep(delay)

        return 0

    @staticmethod
    def get_roblox_packages():
        packages = []
        config = FileManager._load_config()
        package_prefix = config.get("package_prefix", "com.roblox")
        try:
            cmd = f"pm list packages {package_prefix} | sed 's/package://'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    name = line.strip()
                    if name:
                        packages.append(name)
            else:
                print(f"\033[1;31m[ zam2109shop.com ] - Failed to retrieve packages with prefix {package_prefix}.\033[0m")
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Error retrieving packages: {e}\033[0m")
            Utilities.log_error(f"Error retrieving packages: {e}")
        return packages

    @staticmethod
    def kill_roblox_processes():
        packages = RobloxManager.get_roblox_packages()
        if not packages:
            print("\033[1;32m[ zam2109shop.com ] - No Roblox processes to kill.\033[0m")
            return
        for pkg in packages:
            subprocess.run(
                f"nohup /system/bin/am force-stop {pkg} > /dev/null 2>&1 &",
                shell=True,
            )

    @staticmethod
    def kill_roblox_process(package_name):
        try:
            print(f"\033[1;96m[ zam2109shop.com ] - Killing Roblox process for {package_name}...\033[0m")
            subprocess.run(["/system/bin/am", "force-stop", package_name], check=True)
            print(f"\033[1;32m[ zam2109shop.com ] - Killed process for {package_name}\033[0m")
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Error killing process for {package_name}: {e}\033[0m")
            Utilities.log_error(f"Error killing process for {package_name}: {e}")

    @staticmethod
    def delete_cache_for_package(package_name):
        cache_path = f"/data/data/{package_name}/cache/"
        if os.path.exists(cache_path):
            os.system(f"rm -rf {cache_path}")
            print(f"\033[1;32m[ zam2109shop.com ] - Cache cleared for {package_name}\033[0m")
        else:
            print(f"\033[1;93m[ zam2109shop.com ] - No cache found for {package_name}\033[0m")

    @staticmethod
    def launch_roblox(package_name, server_link):
        try:
            print(f"\033[1;36mOpening Roblox for {package_name}...\033[0m")
            with status_lock:
                package_statuses.setdefault(package_name, {})["Status"] = "Opening..."
            subprocess.run(
                [
                    "am", "start", "-a", "android.intent.action.MAIN",
                    "-n", f"{package_name}/com.roblox.client.startup.ActivitySplash",
                ],
                check=True,
            )
            time.sleep(2)
            print(f"\033[1;36mJoining Roblox for {package_name}...\033[0m")
            with status_lock:
                package_statuses.setdefault(package_name, {})["Status"] = "Joining..."
            subprocess.run(
                [
                    "am", "start", "-a", "android.intent.action.VIEW",
                    "-n", f"{package_name}/com.roblox.client.ActivityProtocolLaunch",
                    "-d", server_link,
                ],
                check=True,
            )
            print("\033[1;32mJoined Roblox\033[0m")
            with status_lock:
                package_statuses.setdefault(package_name, {})["Status"] = "\033[1;32mJoined Roblox\033[0m"
        except Exception as e:
            error_message = f"Error launching Roblox for {package_name}: {e}"
            print(f"\033[1;31m[ zam2109shop.com ] - {error_message}\033[0m")
            with status_lock:
                package_statuses.setdefault(package_name, {})["Status"] = "\033[1;31mLaunch Failed\033[0m"
            Utilities.log_error(error_message)

    @staticmethod
    def inject_cookies_and_appstorage():
        db_url = "https://raw.githubusercontent.com/nghvit/module/refs/heads/main/import/Cookies"
        appstorage_url = "https://raw.githubusercontent.com/nghvit/module/refs/heads/main/import/appStorage.json"
        downloaded_db_path = "Cookies.db"
        downloaded_appstorage_path = "appStorage.json"

        if not FileManager.download_file(db_url, downloaded_db_path, binary=True) or \
           not FileManager.download_file(appstorage_url, downloaded_appstorage_path, binary=False):
            print("\033[1;31m[ zam2109shop.com ] - Failed to download necessary files. Exiting.\033[0m")
            Utilities.log_error("Failed to download necessary files for cookie and appStorage injection.")
            return

        packages = RobloxManager.get_roblox_packages()
        if not packages:
            print("\033[1;31m[ zam2109shop.com ] - No Roblox packages detected.\033[0m")
            return

        cookies = RobloxManager.get_cookie()
        if not cookies:
            return

        failed_packages = []
        for i, package_name in enumerate(packages):
            if i >= len(cookies):
                print(f"\033[1;31m[ zam2109shop.com ] - Failed to retrieve a cookie for {package_name}. Skipping...\033[0m")
                continue

            cookie = cookies[i]
            user_id = RobloxManager.verify_cookie(cookie)
            if not user_id:
                print(f"\033[1;31m[ zam2109shop.com ] - Cookie for {package_name} is invalid. Skipping injection...\033[0m")
                continue

            print(f"\033[1;32m[ zam2109shop.com ] - Cookie for {package_name} is valid! User ID: {user_id}\033[0m")
            print(f"\033[1;32m[ zam2109shop.com ] - Injecting cookie for {package_name}: {cookie[:20]}...\033[0m")

            destination_db_dir = f"/data/data/{package_name}/app_webview/Default/"
            destination_appstorage_dir = f"/data/data/{package_name}/files/appData/LocalStorage/"
            os.makedirs(destination_db_dir, exist_ok=True)
            os.makedirs(destination_appstorage_dir, exist_ok=True)

            destination_db_path = os.path.join(destination_db_dir, "Cookies")
            destination_appstorage_path = os.path.join(destination_appstorage_dir, "appStorage.json")

            try:
                shutil.copy(downloaded_db_path, destination_db_path)
                RobloxManager.replace_cookie_value_in_db(destination_db_path, cookie)
                print(f"\033[1;32m[ zam2109shop.com ] - Copied Cookies.db to {destination_db_path}\033[0m")

                shutil.copy(downloaded_appstorage_path, destination_appstorage_path)
                print(f"\033[1;32m[ zam2109shop.com ] - Copied appStorage.json to {destination_appstorage_path}\033[0m")
            except Exception as e:
                error_message = f"Error injecting cookie for {package_name}: {e}"
                print(f"\033[1;31m[ zam2109shop.com ] - {error_message}\033[0m")
                Utilities.log_error(error_message)

        print("\033[1;32m[ zam2109shop.com ] - Opening all Roblox tabs...\033[0m")
        for package_name in packages:
            try:
                print(f"\033[1;36m[ zam2109shop.com ] - Launching {package_name}...\033[0m")
                subprocess.run(
                    [
                        "am", "start", "-a", "android.intent.action.MAIN",
                        "-n", f"{package_name}/com.roblox.client.startup.ActivitySplash",
                    ],
                    check=True,
                )
                print(f"\033[1;32m[ zam2109shop.com ] - Successfully launched {package_name}\033[0m")
            except Exception as e:
                failed_packages.append(package_name)
                print(f"\033[1;31m[ zam2109shop.com ] - Error launching {package_name}: {e}\033[0m")

        if failed_packages:
            print(f"\033[1;31m[ zam2109shop.com ] - Failed to launch packages: {', '.join(failed_packages)}\033[0m")
        else:
            print("\033[1;32m[ zam2109shop.com ] - Successfully launched all packages.\033[0m")

        print("\033[1;33m[ zam2109shop.com ] - Waiting for all tabs to load (1 minute)...\033[0m")
        time.sleep(60)

        debug_mode = input("\033[1;93m[ zam2109shop.com ] - Keep Roblox tabs open for debugging? (y/n): \033[0m").strip().lower()
        if debug_mode != "y":
            print("\033[1;33m[ zam2109shop.com ] - Closing all Roblox tabs after loading...\033[0m")
            RobloxManager.kill_roblox_processes()
        else:
            print("\033[1;33m[ zam2109shop.com ] - Keeping Roblox tabs open for debugging.\033[0m")

        print("\033[1;32m[ zam2109shop.com ] - Cookie and appStorage injection, followed by app launch, completed for all packages.\033[0m")

    @staticmethod
    def replace_cookie_value_in_db(db_path, new_cookie_value):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            now = int(time.time() * 1000000)
            cursor.execute(
                "UPDATE cookies SET value = ?, last_access_utc = ?, expires_utc = ? WHERE host_key = '.roblox.com' AND name = '.ROBLOSECURITY'",
                (new_cookie_value, now, now + 31536000000000),
            )
            conn.commit()
            conn.close()
            print("\033[1;32mCookie value replaced successfully in the database!\033[0m")
        except sqlite3.Error as e:
            print(f"\033[1;31mDatabase error during cookie replacement: {e}\033[0m")
        except Exception as e:
            print(f"\033[1;31mError replacing cookie value in database: {e}\033[0m")

    @staticmethod
    def format_server_link(input_link):
        input_link = input_link.strip()
        if "roblox.com" in input_link or input_link.startswith("roblox://"):
            return input_link
        elif input_link.isdigit():
            return f"roblox://placeID={input_link}"
        else:
            print("\033[1;31m[ zam2109shop.com ] - Invalid input! Please enter a valid game ID or private server link.\033[0m")
            return None


# ------------------------------------------------------------------------------
# Class: WebhookManager
# ------------------------------------------------------------------------------

class WebhookManager:
    @staticmethod
    def start_webhook_thread():
        global webhook_thread, stop_webhook_thread
        stop_webhook_thread = False

        def worker():
            config = FileManager._load_config()
            interval_str = config.get("interval", "inf")
            if interval_str == "inf" or not interval_str:
                return
            try:
                interval_min = float(interval_str)
            except ValueError:
                return

            while not stop_webhook_thread:
                WebhookManager.send_webhook()
                time.sleep(interval_min * 60)

        webhook_thread = threading.Thread(target=worker, daemon=True)
        webhook_thread.start()

    @staticmethod
    def send_webhook():
        config = FileManager._load_config()
        url = config.get("webhook_url")
        device = config.get("device_name", "Android Device")

        if not url:
            return

        try:
            screenshot_path = SystemMonitor.capture_screenshot()
            info = SystemMonitor.get_system_info()
            if not info:
                return

            cpu = f"{info['cpu_usage']:.1f}%"
            mem_used = f"{info['memory_used']:.2f} GB"
            mem_total = f"{info['memory_total']:.2f} GB"
            mem_percent = f"{info['memory_percent']:.1f}%"
            uptime = info["uptime"]

            roblox_count = len(info["roblox_packages"])
            roblox_status = f"Running: {roblox_count} instance{'s' if roblox_count != 1 else ''}"
            roblox_details = "\n".join(info["roblox_packages"]) if info["roblox_packages"] else "None"

            tool_mem = SystemMonitor.get_memory_usage()
            tool_mem_display = f"{tool_mem} MB" if tool_mem is not None else "Unavailable"
            status_text = "🟢 Online" if roblox_count > 0 else "🔴 Offline"

            random_color = random.randint(0, 0xFFFFFF)

            embed = {
                "color": random_color,
                "title": "📈 System Status Monitor",
                "description": f"Real-time report for **{device}**",
                "fields": [
                    {"name": "🏷️ Device", "value": f"```{device}```", "inline": True},
                    {"name": "💾 Total Memory", "value": f"```{mem_total}```", "inline": True},
                    {"name": "⏰ Uptime", "value": f"```{uptime}```", "inline": True},
                    {"name": "⚡ CPU Usage", "value": f"```{cpu}```", "inline": True},
                    {"name": "📊 Memory Usage", "value": f"```{mem_used} ({mem_percent})```", "inline": True},
                    {"name": "🛠️ Tool Memory Usage", "value": f"```{tool_mem_display}```", "inline": True},
                    {"name": "🎮 Total Roblox Processes", "value": f"```{roblox_status}```", "inline": True},
                    {"name": "🔍 Roblox Details", "value": f"```{roblox_details}```", "inline": False},
                    {"name": "✅ Status", "value": f"```{status_text}```", "inline": True},
                ],
                "thumbnail": {
                    "url": "https://media.discordapp.net/attachments/1261275201723957268/1473302832777138258/icon.png"
                },
                "image": {"url": "attachment://screenshot.png"},
                "footer": {
                    "text": "Made with 💖 by zam2109shop.com | Join us at discord.gg/3f6SUbGneC",
                    "icon_url": "https://media.discordapp.net/attachments/1261275201723957268/1473302832777138258/icon.png",
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "author": {
                    "name": "zam2109shop.com",
                    "url": "https://discord.gg/3f6SUbGneC",
                    "icon_url": "https://media.discordapp.net/attachments/1261275201723957268/1473302832777138258/icon.png",
                },
            }

            payload = {
                "username": "zam2109shop.com",
                "avatar_url": "https://i.imgur.com/5yXNxU4.png",
                "embeds": [embed],
            }

            files = {}
            if screenshot_path and os.path.exists(screenshot_path):
                files["file"] = ("screenshot.png", open(screenshot_path, "rb"), "image/png")

            response = requests.post(url, data={"payload_json": json.dumps(payload)}, files=files)
            if response.status_code not in (200, 204):
                print(f"\033[1;31m[ zam2109shop.com ] - Webhook error: Status code {response.status_code}\033[0m")
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Error sending device info: {e}\033[0m")
            Utilities.log_error(f"Error in webhook thread: {e}")

    @staticmethod
    def stop_webhook():
        global stop_webhook_thread
        stop_webhook_thread = True

    @staticmethod
    def setup_webhook():
        try:
            url = input("\033[1;35m[ zam2109shop.com ] - Enter your Webhook URL: \033[0m").strip()
            name = input("\033[1;35m[ zam2109shop.com ] - Enter your device name: \033[0m").strip()
            interval = input("\033[1;35m[ zam2109shop.com ] - Enter the interval to send Webhook (minutes): \033[0m").strip()

            FileManager.save_config({
                "webhook_url": url,
                "device_name": name,
                "interval": interval,
            })
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Error during webhook setup: {e}\033[0m")
            Utilities.log_error(f"Error during webhook setup: {e}")


# ------------------------------------------------------------------------------
# Class: UIManager
# ------------------------------------------------------------------------------

class UIManager:
    @staticmethod
    def print_header(version_str):
        console = Console()
        banner = (
            "\n\n███████╗███╗░░░███╗\u2003\u2003░█████╗░██╗░░░░░██████╗░\n"
            "╚════██║████╗░████║\u2003\u2003██╔══██╗██║░░░░░██╔══██╗\n"
            "░░███╔═╝██╔████╔██║\u2003\u2003██║░░██║██║░░░░░██║░░██║\n"
            "██╔══╝░░██║╚██╔╝██║\u2003\u2003██║░░██║██║░░░░░██║░░██║\n"
            "███████╗██║░╚═╝░██║\u2003\u2003╚█████╔╝███████╗██████╔╝\n"
            "╚══════╝╚═╝░░░░░╚═╝\u2003\u2003░╚════╝░╚══════╝╚═════╝░\n"
            "=> ⭐ VIET NAM VERSION ⭐ <= "
        )
        console.print(Align.center(Text(banner, style="bold white")))

        config = FileManager._load_config()
        check_executor = config.get("check_executor", "1")
        method_str = "Check Executor" if check_executor == "1" else "Check Online"

        info_text = (
            f"[bold yellow]- Version: [/bold yellow][bold white]{version_str}[/bold white]\n"
            f"[bold yellow]- Last Update: [/bold yellow][bold white]17/2/2026[/bold white]\n"
            f"[bold yellow]- Credit: [/bold yellow][bold white]zam2109shop.com[/bold white]\n"
            f"[bold yellow]- Method: [/bold yellow][bold white]{method_str}[/bold white]\n"
        )
        console.print(Panel(Align.center(info_text), box=ROUNDED, border_style="bold cyan"))

    @staticmethod
    def create_dynamic_menu(options):
        console = Console()
        table = Table(box=ROUNDED, border_style="bold magenta")
        table.add_column("LỆNH", justify="center", style="bold cyan")
        table.add_column("MÔ TẢ LỆNH", justify="left", style="bold white")

        for i, service in enumerate(options, start=1):
            table.add_row(f"[bold yellow][ {i} ][/bold yellow]", f"[bold blue]{service}[/bold blue]")

        panel = Panel(
            table,
            title="[bold yellow]https://discord.gg/3f6SUbGneC - Bảng Vip[/bold yellow]",
            box=ROUNDED,
            border_style="yellow",
        )
        console.print(panel)

    @staticmethod
    def create_dynamic_table(headers, rows):
        table = PrettyTable()
        table.field_names = headers
        for h in headers:
            table.align[h] = "l"
        for row in rows:
            table.add_row(row)
        return table

    @staticmethod
    def update_status_table():
        Utilities.clear_screen()
        UIManager.print_header(version)
        cpu_usage = cpu_percent()
        ram = virtual_memory().percent

        title = f"CPU: {cpu_usage}% | RAM: {ram}%"
        table = PrettyTable()
        table.title = title
        table.field_names = ["Package", "Tên đăng nhập", "Trạng thái Acc"]
        table.align["Package"] = "l"
        table.align["Tên đăng nhập"] = "l"
        table.align["Trạng thái Acc"] = "l"

        with status_lock:
            for package, info in package_statuses.items():
                username = info.get("Username", "Unknown")
                if username != "Unknown" and len(username) > 4:
                    obfuscated_username = username[:2] + "******" + username[-2:]
                else:
                    obfuscated_username = username
                status = info.get("Status", "Unknown")
                table.add_row([package, obfuscated_username, status])

        print(table)


# ------------------------------------------------------------------------------
# Class: ExecutorManager
# ------------------------------------------------------------------------------

class ExecutorManager:
    @staticmethod
    def detect_executors():
        detected = []
        for name, base_path in executors.items():
            if os.path.exists(base_path):
                for sub in ["Autoexec", "Autoexecute", "autoexec"]:
                    p = os.path.join(base_path, sub)
                    if os.path.exists(p):
                        detected.append((name, p))
                        print(f"\033[1;32m[ zam2109shop.com ] - Detected executor: {name}\033[0m")
                        break
        return detected

    @staticmethod
    def write_lua_script(detected_executors):
        config = FileManager._load_config()
        lua_script_content = config.get(
            "lua_script_template",
            'task.spawn(function()local a=tostring(game.Players.LocalPlayer.UserId)..".main"while true do pcall(function()if isfile(a)then delfile(a)end writefile(a,"https://discord.gg/3f6SUbGneC")end)task.wait(1)end end)',
        )

        for name, autoexec_path in detected_executors:
            try:
                if name == "KRNL":
                    autoruns_path = "/storage/emulated/0/krnl/workspace/.storage/autoruns.json"
                    tabs_path = "/storage/emulated/0/krnl/workspace/.storage/tabs"
                    os.makedirs(tabs_path, exist_ok=True)
                    target_file = os.path.join(tabs_path, "check_executor.luau")
                    with open(target_file, "w", encoding="utf-8") as f:
                        f.write(lua_script_content)

                    autoruns = []
                    if os.path.exists(autoruns_path):
                        try:
                            with open(autoruns_path, "r", encoding="utf-8") as f:
                                autoruns = json.load(f)
                        except Exception:
                            pass
                    if "check_executor" not in autoruns:
                        autoruns.append("check_executor")
                        with open(autoruns_path, "w", encoding="utf-8") as f:
                            json.dump(autoruns, f)
                    print("\033[1;32m[ zam2109shop.com ] - Added script into KRNL autoexec!\033[0m")
                else:
                    target_file = os.path.join(autoexec_path, "executor_check.lua")
                    with open(target_file, "w", encoding="utf-8") as f:
                        f.write(lua_script_content)
                    print(f"\033[1;32m[ zam2109shop.com ] - Lua script written to: {target_file}\033[0m")
            except Exception as e:
                print(f"\033[1;31m[ zam2109shop.com ] - Error writing Lua script to {name}: {e}\033[0m")
                Utilities.log_error(f"Error writing Lua script to {name}: {e}")

    @staticmethod
    def check_executor_status(package_name, continuous=False, max_wait_time=60):
        accounts = FileManager.load_accounts()
        user_id = accounts.get(package_name)
        if not user_id:
            return False

        filename = f"{user_id}.main"
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            for wsp in workspace_paths:
                file_path = os.path.join(wsp, filename)
                if os.path.exists(file_path):
                    return True
            if not continuous:
                break
            time.sleep(2)
        return False

    @staticmethod
    def check_executor_and_rejoin(package_name, server_link, next_package_event):
        try:
            with status_lock:
                package_statuses.setdefault(package_name, {})["Status"] = "\033[1;33mChecking executor...\033[0m"

            loaded = ExecutorManager.check_executor_status(package_name, continuous=True, max_wait_time=90)
            if loaded:
                with status_lock:
                    package_statuses.setdefault(package_name, {})["Status"] = "\033[1;32mExecutor has loaded successfully\033[0m"
                if next_package_event:
                    next_package_event.set()
            else:
                with status_lock:
                    package_statuses.setdefault(package_name, {})["Status"] = "\033[1;31mExecutor didn't load. Rejoining...\033[0m"
                print(f"\033[1;33m[ zam2109shop.com ] - Rejoining {package_name}...\033[0m")
                RobloxManager.kill_roblox_process(package_name)
                RobloxManager.delete_cache_for_package(package_name)
                time.sleep(2)
                RobloxManager.launch_roblox(package_name, server_link)
                ExecutorManager.check_executor_and_rejoin(package_name, server_link, next_package_event)
        except Exception as e:
            print(f"\033[1;31mError checking executor for {package_name}: {e}\033[0m")
            if next_package_event:
                next_package_event.set()

    @staticmethod
    def reset_executor_file(package_name):
        accounts = FileManager.load_accounts()
        user_id = accounts.get(package_name)
        if not user_id:
            return
        filename = f"{user_id}.main"
        for wsp in workspace_paths:
            fp = os.path.join(wsp, filename)
            if os.path.exists(fp):
                try:
                    os.remove(fp)
                except Exception:
                    pass


# ------------------------------------------------------------------------------
# Class: Runner
# ------------------------------------------------------------------------------

class Runner:
    @staticmethod
    def launch_package_sequentially(server_links):
        accounts = FileManager.load_accounts()
        config = FileManager._load_config()
        check_exec_enable = config.get("check_executor", "1")
        delay = int(config.get("close_and_rejoin_delay", 5))

        detected_executors = ExecutorManager.detect_executors()
        if check_exec_enable == "1":
            ExecutorManager.write_lua_script(detected_executors)

        total_packages = len(server_links)
        for index, (package_name, server_link) in enumerate(server_links.items(), start=1):
            user_id = accounts.get(package_name)
            if not user_id:
                print(f"\033[1;31m[ zam2109shop.com ] - No UserID found for {package_name}, skipping...\033[0m")
                continue

            username = FileManager.load_saved_username(user_id)
            if not username:
                username = FileManager.get_username(user_id)
                FileManager.save_username(user_id, username)

            with status_lock:
                package_statuses[package_name] = {
                    "Username": username,
                    "Status": "\033[1;33mWaiting to Join\033[0m",
                }

            print(f"\033[1;32m[ zam2109shop.com ] - Launching package {index}/{total_packages}: {package_name}\033[0m")

            if check_exec_enable == "1":
                ExecutorManager.reset_executor_file(package_name)

            next_package_event = Event()
            RobloxManager.launch_roblox(package_name, server_link)

            if check_exec_enable == "1":
                t = threading.Thread(
                    target=ExecutorManager.check_executor_and_rejoin,
                    args=(package_name, server_link, next_package_event),
                    daemon=True,
                )
                t.start()
                next_package_event.wait(timeout=90)
            else:
                time.sleep(delay)

    @staticmethod
    def monitor_presence(server_links, stop_event):
        accounts = FileManager.load_accounts()
        while not stop_event.is_set():
            for package_name, server_link in server_links.items():
                if stop_event.is_set():
                    break
                user_id = accounts.get(package_name)
                if not user_id:
                    continue

                db_path = f"/data/data/{package_name}/app_webview/Default/Cookies"
                cookie = ""
                if os.path.exists(db_path):
                    try:
                        conn = sqlite3.connect(db_path)
                        cur = conn.cursor()
                        cur.execute("SELECT value FROM cookies WHERE name = '.ROBLOSECURITY'")
                        row = cur.fetchone()
                        if row:
                            cookie = row[0]
                        conn.close()
                    except Exception:
                        pass

                presence = RobloxManager.check_user_online(user_id, cookie)
                if presence == 2:
                    with status_lock:
                        package_statuses.setdefault(package_name, {})["Status"] = "\033[1;32mIn-Game\033[0m"
                else:
                    with status_lock:
                        package_statuses.setdefault(package_name, {})["Status"] = "\033[1;31mNot In-Game, Rejoining!\033[0m"
                    print(f"\033[1;31m[ zam2109shop.com ] - {package_name} confirmed offline, rejoining...\033[0m")
                    RobloxManager.kill_roblox_process(package_name)
                    RobloxManager.delete_cache_for_package(package_name)
                    time.sleep(2)
                    RobloxManager.launch_roblox(package_name, server_link)

            time.sleep(15)

    @staticmethod
    def force_rejoin(server_links, interval, stop_event):
        if str(interval).lower() == "inf":
            return
        try:
            interval_sec = float(interval)
        except ValueError:
            return

        while not stop_event.is_set():
            time.sleep(interval_sec)
            if stop_event.is_set():
                break
            print("\033[1;31m[ zam2109shop.com ] - Force killing Roblox processes due to time limit.\033[0m")
            RobloxManager.kill_roblox_processes()
            print("\033[1;33m[ zam2109shop.com ] - Waiting for 5 seconds before starting the rejoin process...\033[0m")
            time.sleep(5)
            Runner.launch_package_sequentially(server_links)

    @staticmethod
    def update_status_table_periodically():
        while True:
            with status_lock:
                UIManager.update_status_table()
            time.sleep(2)


# ------------------------------------------------------------------------------
# Standalone Helper Functions
# ------------------------------------------------------------------------------

def check_activation_status():
    try:
        response = requests.get(
            "https://raw.githubusercontent.com/zam2109/Toolrejoin/refs/heads/main/oldtool",
            timeout=10,
        )
        content = response.text.strip().lower()
        if content == "true":
            print("\033[1;32m[ zam2109shop.com ] - Activation status: Enabled. Proceeding with tool execution.\033[0m")
            return True
        elif content == "false":
            print("\033[1;31m[ zam2109shop.com ] - Activation status: Disabled. Tool execution halted. ( VN: Tool đã lỗi thời vui lòng sài lại lệnh số 2 để setub lại nhé )\033[0m")
            sys.exit(0)
        else:
            print(f"\033[1;31m[ zam2109shop.com ] - Invalid activation status received: {content}. Halting execution.\033[0m")
            sys.exit(0)
    except Exception as e:
        print(f"\033[1;31m[ zam2109shop.com ] - Error checking activation status: {e}\033[0m")
        Utilities.log_error(f"Error checking activation status: {e}")
        return True


def set_android_id(android_id):
    try:
        subprocess.run(
            ["settings", "put", "secure", "android_id", str(android_id)],
            check=True,
            capture_output=True,
        )
    except Exception as e:
        Utilities.log_error(f"Failed to set Android ID: {e}")


def auto_change_android_id():
    while auto_android_id_enabled:
        if auto_android_id_value:
            set_android_id(auto_android_id_value)
        time.sleep(2)


# ------------------------------------------------------------------------------
# Main Application Flow
# ------------------------------------------------------------------------------

def main():
    global auto_android_id_enabled, auto_android_id_thread, auto_android_id_value

    Utilities.clear_screen()
    check_activation_status()

    config = FileManager._load_config()

    # Save default lua script if not exists
    default_script = config.get(
        "lua_script_template",
        'task.spawn(function()local a=tostring(game.Players.LocalPlayer.UserId)..".main"while true do pcall(function()if isfile(a)then delfile(a)end writefile(a,"https://discord.gg/FcEGmkNDDe")end)task.wait(1)end end)',
    )
    checkui_path = "zam2109shop.com/checkui.lua"
    if not os.path.exists(checkui_path):
        try:
            with open(checkui_path, "w", encoding="utf-8") as f:
                f.write(default_script)
            print("\033[1;32m[ zam2109shop.com ] - Default script saved to checkui.lua\033[0m")
        except Exception as e:
            print(f"\033[1;31m[ zam2109shop.com ] - Error saving default script to {checkui_path}: {e}\033[0m")

    # Start webhook thread if configured
    if config.get("webhook_url") and config.get("interval") != "inf":
        WebhookManager.start_webhook_thread()
    else:
        print("\033[1;33m[ zam2109shop.com ] - Webhook not configured or disabled.\033[0m")

    options = [
        "Start Auto Rejoin (Auto setup User ID)",
        "Setup Game ID for Packages",
        "Auto Login with Cookie",
        "Enable Discord Webhook",
        "Auto Check User Setup",
        "Configure Package Prefix",
        "Auto Change Android ID",
    ]

    while True:
        Utilities.clear_screen()
        UIManager.print_header(version)
        UIManager.create_dynamic_menu(options)

        choice = input("\033[1;93m[ zam2109shop.com ] - Enter command: \033[0m").strip()

        # ----------------------------------------------------------------------
        # Option 1: Start Auto Rejoin
        # ----------------------------------------------------------------------
        if choice == "1":
            try:
                FileManager.setup_user_ids()
                accounts = FileManager.load_accounts()
                if not accounts:
                    print("\033[1;31m[ zam2109shop.com ] - Setup ran, but no User IDs were found. Cannot start Auto Rejoin.\033[0m")
                    input("\033[1;32mPress Enter to return...\033[0m")
                    continue

                server_links = FileManager.load_server_links()
                if not server_links:
                    print("\033[1;31m[ zam2109shop.com ] - No game ID or server link set up. Please run option 2 first.\033[0m")
                    input("\033[1;32mPress Enter to return...\033[0m")
                    continue

                rejoin_in = input("\033[1;93m[ zam2109shop.com ] - Force rejoin interval (minutes, 'q' to skip): \033[0m").strip()
                if rejoin_in.lower() == "q":
                    interval = float("inf")
                else:
                    try:
                        interval = int(rejoin_in) * 60
                        if interval <= 0:
                            print("\033[1;31m[ zam2109shop.com ] - Interval must be positive.\033[0m")
                            input("\033[1;32mPress Enter to return...\033[0m")
                            continue
                    except ValueError:
                        interval = float("inf")

                RobloxManager.kill_roblox_processes()
                time.sleep(2)
                Runner.launch_package_sequentially(server_links)

                stop_event = Event()
                cfg = FileManager._load_config()
                if cfg.get("check_executor", "1") == "0":
                    t_mon = threading.Thread(
                        target=Runner.monitor_presence,
                        args=(server_links, stop_event),
                        daemon=True,
                    )
                    t_mon.start()

                if interval != float("inf"):
                    t_rejoin = threading.Thread(
                        target=Runner.force_rejoin,
                        args=(server_links, interval, stop_event),
                        daemon=True,
                    )
                    t_rejoin.start()

                while not stop_event.is_set():
                    time.sleep(2)
                    with status_lock:
                        UIManager.update_status_table()
                    Utilities.collect_garbage()
            except Exception as e:
                print(f"\033[1;31m[ zam2109shop.com ] - Error: {e}\033[0m")
                Utilities.log_error(f"Setup error: {e}")
                input("\033[1;32mPress Enter to return...\033[0m")

        # ----------------------------------------------------------------------
        # Option 2: Setup Game ID for Packages
        # ----------------------------------------------------------------------
        elif choice == "2":
            try:
                print("\033[1;32m[ zam2109shop.com ] - Auto Setup User IDs from appStorage.json...\033[0m")
                FileManager.setup_user_ids()

                games = [
                    "1. Blox Fruits",
                    "2. Grow A Garden",
                    "3. King Legacy",
                    "4. Fisch",
                    "5. Bee Swarm Simulator",
                    "6. Anime Last Stand",
                    "7. Dead Rails Alpha",
                    "8. All Star Tower Defense X",
                    "9. 99 Nights In The Forest",
                    "10. Murder Mystery 2",
                    "11. Steal A Brainrot",
                    "12. Blue Lock Rivals",
                    "13. Arise Crossover",
                    "14. Other game or Private Server Link",
                ]

                print("\033[93m[ zam2109shop.com ] - Select game:\033[0m")
                for g in games:
                    print(f"\033[96m{g}\033[0m")

                game_ids = {
                    "1": "2753915549",
                    "2": "126884695634066",
                    "3": "4520749081",
                    "4": "16732694052",
                    "5": "1537690962",
                    "6": "12886143095",
                    "7": "116495829188952",
                    "8": "17687504411",
                    "9": "79546208627805",
                    "10": "142823291",
                    "11": "109983668079237",
                    "12": "18668065416",
                    "13": "87039211657390",
                }

                g_choice = input("\033[93m[ zam2109shop.com ] - Enter choice: \033[0m").strip()
                if g_choice in game_ids:
                    server_link = f"roblox://placeID={game_ids[g_choice]}"
                elif g_choice == "14":
                    raw_link = input("\033[93m[ zam2109shop.com ] - Enter game ID or private server link: \033[0m").strip()
                    server_link = RobloxManager.format_server_link(raw_link)
                else:
                    print("\033[1;31m[ zam2109shop.com ] - Invalid choice.\033[0m")
                    input("\033[1;32mPress Enter to return...\033[0m")
                    continue

                if server_link:
                    packages = RobloxManager.get_roblox_packages()
                    links = {pkg: server_link for pkg in packages}
                    FileManager.save_server_links(links)
                else:
                    print("\033[1;31m[ zam2109shop.com ] - Invalid server link.\033[0m")
            except Exception as e:
                print(f"\033[1;31m[ zam2109shop.com ] - Error: {e}\033[0m")
                Utilities.log_error(f"Setup error: {e}")
            input("\033[1;32mPress Enter to return...\033[0m")

        # ----------------------------------------------------------------------
        # Option 3: Auto Login with Cookie
        # ----------------------------------------------------------------------
        elif choice == "3":
            RobloxManager.inject_cookies_and_appstorage()
            input("\033[1;32m\nPress Enter to exit...\033[0m")

        # ----------------------------------------------------------------------
        # Option 4: Enable Discord Webhook
        # ----------------------------------------------------------------------
        elif choice == "4":
            WebhookManager.setup_webhook()
            input("\033[1;32m\nPress Enter to exit...\033[0m")

        # ----------------------------------------------------------------------
        # Option 5: Auto Check User Setup
        # ----------------------------------------------------------------------
        elif choice == "5":
            try:
                print("\033[1;35m[1]\033[1;32m Executor Check\033[0m \033[1;35m[2]\033[1;36m Online Check\033[0m")
                m_choice = input("\033[1;93m[ zam2109shop.com ] - Select check method (1-2, 'q' to keep default): \033[0m").strip()
                if m_choice == "1":
                    template = 'task.spawn(function()local a=tostring(game.Players.LocalPlayer.UserId)..".main"while true do pcall(function()if isfile(a)then delfile(a)end writefile(a,"https://discord.gg/3f6SUbGneC")end)task.wait(1)end end)'
                    FileManager.save_config({
                        "check_executor": "1",
                        "lua_script_template": template,
                    })
                    with open(checkui_path, "w", encoding="utf-8") as f:
                        f.write(template)
                    print("\033[1;32m[ zam2109shop.com ] - Set to Executor + ZM Rejoin Check\033[0m")
                elif m_choice == "2":
                    FileManager.save_config({"check_executor": "0"})
                    if os.path.exists(checkui_path):
                        try:
                            os.remove(checkui_path)
                            print(f"\033[1;36m[ zam2109shop.com ] - Removed {checkui_path} for Online Check.\033[0m")
                        except Exception:
                            pass
                    print("\033[1;36m[ zam2109shop.com ] - Set to Online Check.\033[0m")
                elif m_choice.lower() != "q":
                    print("\033[1;31m[ zam2109shop.com ] - Invalid choice. Keeping default.\033[0m")
            except Exception as e:
                print(f"\033[1;31m[ zam2109shop.com ] - Error setting up check method: {e}\033[0m")
                Utilities.log_error(f"Check method setup error: {e}")
            input("\033[1;32mPress Enter to return...\033[0m")

        # ----------------------------------------------------------------------
        # Option 6: Configure Package Prefix
        # ----------------------------------------------------------------------
        elif choice == "6":
            try:
                cfg = FileManager._load_config()
                curr_prefix = cfg.get("package_prefix", "com.roblox")
                print(f"\033[1;32m[ zam2109shop.com ] - Current package prefix: {curr_prefix}\033[0m")
                new_prefix = input("\033[1;93m[ zam2109shop.com ] - Enter new package prefix (or press Enter to keep current): \033[0m").strip()
                if new_prefix:
                    FileManager.save_config({"package_prefix": new_prefix})
                    print(f"\033[1;32m[ zam2109shop.com ] - Package prefix updated to: {new_prefix}\033[0m")
                else:
                    print(f"\033[1;33m[ zam2109shop.com ] - Package prefix unchanged: {curr_prefix}\033[0m")
            except Exception as e:
                print(f"\033[1;31m[ zam2109shop.com ] - Error setting package prefix: {e}\033[0m")
                Utilities.log_error(f"Error setting package prefix: {e}")
            input("\033[1;32mPress Enter to return...\033[0m")

        # ----------------------------------------------------------------------
        # Option 7: Auto Change Android ID
        # ----------------------------------------------------------------------
        elif choice == "7":
            try:
                if not auto_android_id_enabled:
                    android_id_in = input("\033[1;93m[ zam2109shop.com ] - Enter Android ID to spam set: \033[0m").strip()
                    if android_id_in:
                        auto_android_id_value = android_id_in
                        auto_android_id_enabled = True
                        auto_android_id_thread = threading.Thread(target=auto_change_android_id, daemon=True)
                        auto_android_id_thread.start()
                        print("\033[1;32m[ zam2109shop.com ] - Auto change Android ID enabled.\033[0m")
                    else:
                        print("\033[1;31m[ zam2109shop.com ] - Android ID cannot be empty.\033[0m")
                else:
                    auto_android_id_enabled = False
                    print("\033[1;31m[ zam2109shop.com ] - Auto change Android ID disabled.\033[0m")
            except Exception as e:
                print(f"\033[1;31m[ zam2109shop.com ] - Error: {e}\033[0m")
            input("\033[1;32mPress Enter to return...\033[0m")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\033[1;31m[ zam2109shop.com ] - Tool terminated by user.\033[0m")
        sys.exit(0)
    except Exception as e:
        print(f"\033[1;31m[ zam2109shop.com ] - Initialization error: {e}\033[0m")
        Utilities.log_error(f"Initialization error: {e}")
        sys.exit(1)
