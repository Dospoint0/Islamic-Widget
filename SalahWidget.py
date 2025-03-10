#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Islamic Widget for Fedora
Features:
- Daily Quranic verse with translation
- Prayer time countdown
- Daily hadith display
- Configurable settings
"""

import os
import sys
import json
import random
import requests
import datetime
import subprocess
from pathlib import Path
import tzlocal  # Add this import for timezone detection
from PyQt5.QtCore import Qt, QTimer, QTime, QDate, QDateTime, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QMenu, QAction, QSystemTrayIcon,
                            QDialog, QFormLayout, QComboBox, QLineEdit, QSpinBox,
                            QGridLayout, QFrame)
from geopy.geocoders import Nominatim

# Configuration file paths
CONFIG_DIR = Path(os.path.expanduser("~/.config/islamic-widget"))
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = CONFIG_DIR / "cache"

# Get local timezone
def get_local_timezone():
    try:
        return str(tzlocal.get_localzone())
    except:
        return "America/New_York"  # Default fallback
    
def get_user_location(cityname, countryname):
    try:
        city = cityname.capitalize()
        country = countryname.capitalize()
        geolocator = Nominatim(user_agent="geoapiExercises")
        location = geolocator.geocode(f"{city}, {country}")
        return location.latitude, location.longitude
    except:
        return 40.7128, -74.0060

# Default configuration
DEFAULT_CONFIG = {
    "location": {
        "city": "New York",
        "country": "United States",
        "latitude": get_user_location("city", "country")[0],
        "longitude": get_user_location("city", "country")[1],
        "timezone": get_local_timezone(),
    },
    "appearance": {
        "theme": "light",
        "font_size": 12,
        "show_arabic": True,
        "show_translation": True,
        "show_hadith": True,
    },
    "api": {
        "prayer_api": "https://api.aladhan.com/v1/timingsByCity",
        "quran_api": "https://api.alquran.cloud/v1/ayah/random",
        "hadith_api": "https://random-hadith-generator.vercel.app/bukhari",
    },
    "update_interval": {
        "quran_verse": "daily",  # daily, hourly
        "hadith": "daily",      # daily, hourly
    }
}

class IslamicWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.load_config()
        
        # Initialize UI
        self.init_ui()
        
        # Setup timers
        self.setup_timers()
        
        # Initialize data
        self.update_data()

    def load_config(self):
        """Load configuration from file or create default if not exists"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        if not CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            self.config = DEFAULT_CONFIG
        else:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Update timezone if it's not already set
            if 'timezone' not in self.config['location'] or not self.config['location']['timezone']:
                self.config['location']['timezone'] = get_local_timezone()
                self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
    
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("Islamic Widget")
        self.setWindowIcon(QIcon.fromTheme("preferences-desktop"))
        self.setMinimumSize(350, 500)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Create header
        header = QLabel("Islamic Widget")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(header)
        
        # Prayer times section
        prayer_frame = QWidget()
        prayer_layout = QVBoxLayout(prayer_frame)
        
        prayer_header = QLabel("Prayer Times")
        prayer_header.setStyleSheet("font-size: 14px; font-weight: bold;")
        prayer_layout.addWidget(prayer_header)
        
        # Create labels for all prayer times
        self.prayer_labels = {}
        prayer_names = ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha', 'Midnight']
        
        # Create a grid layout for prayer times
        prayer_grid = QGridLayout()
        for i, prayer in enumerate(prayer_names):
            name_label = QLabel(f"{prayer}:")
            name_label.setStyleSheet("font-weight: bold;")
            time_label = QLabel("--:--")
            self.prayer_labels[prayer] = time_label
            
            prayer_grid.addWidget(name_label, i, 0)
            prayer_grid.addWidget(time_label, i, 1)
        
        prayer_layout.addLayout(prayer_grid)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        prayer_layout.addWidget(separator)
        
        # Next prayer and countdown
        self.next_prayer_label = QLabel("Next Prayer: Calculating...")
        self.next_prayer_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        self.countdown_label = QLabel("Time Remaining: --:--:--")
        self.countdown_label.setStyleSheet("font-weight: bold;")
        
        prayer_layout.addWidget(self.next_prayer_label)
        prayer_layout.addWidget(self.countdown_label)
        
        main_layout.addWidget(prayer_frame)
        
        # Quran verse section
        quran_frame = QWidget()
        quran_layout = QVBoxLayout(quran_frame)
        
        quran_header = QLabel("Daily Verse")
        quran_header.setStyleSheet("font-size: 14px; font-weight: bold;")
        quran_layout.addWidget(quran_header)
        
        self.quran_arabic = QLabel("Loading verse...")
        self.quran_arabic.setAlignment(Qt.AlignRight)
        self.quran_arabic.setStyleSheet(f"font-size: {self.config['appearance']['font_size'] + 4}px; font-weight: bold;")
        self.quran_arabic.setWordWrap(True)
        
        self.quran_translation = QLabel("Loading translation...")
        self.quran_translation.setWordWrap(True)
        
        self.verse_reference = QLabel("Surah --:--")
        self.verse_reference.setAlignment(Qt.AlignRight)
        self.verse_reference.setStyleSheet("font-style: italic;")
        
        if self.config['appearance']['show_arabic']:
            quran_layout.addWidget(self.quran_arabic)
        
        if self.config['appearance']['show_translation']:
            quran_layout.addWidget(self.quran_translation)
        
        quran_layout.addWidget(self.verse_reference)
        main_layout.addWidget(quran_frame)
        
        # Hadith section
        if self.config['appearance']['show_hadith']:
            hadith_frame = QWidget()
            hadith_layout = QVBoxLayout(hadith_frame)
            
            hadith_header = QLabel("Daily Hadith")
            hadith_header.setStyleSheet("font-size: 14px; font-weight: bold;")
            hadith_layout.addWidget(hadith_header)
            
            self.hadith_text = QLabel("Loading hadith...")
            self.hadith_text.setWordWrap(True)
            
            self.hadith_source = QLabel("Source: --")
            self.hadith_source.setStyleSheet("font-style: italic;")
            
            hadith_layout.addWidget(self.hadith_text)
            hadith_layout.addWidget(self.hadith_source)
            main_layout.addWidget(hadith_frame)
        
        # Bottom buttons
        buttons_layout = QHBoxLayout()
        
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.update_data)
        
        buttons_layout.addWidget(self.settings_btn)
        buttons_layout.addWidget(self.refresh_btn)
        main_layout.addLayout(buttons_layout)
        
        # Set the main layout
        self.setLayout(main_layout)
        
        # Create system tray icon
        self.create_tray_icon()
        
        # Apply theme
        self.apply_theme()
    
    def setup_timers(self):
        """Setup timers for updating data and countdown"""
        # Timer for updating countdown
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)  # Update every second
        
        # Timer for daily updates
        current_time = QTime.currentTime()
        target_time = QTime(0, 0, 0)  # Midnight
        
        # Calculate time until next midnight
        secs_until_midnight = current_time.secsTo(target_time)
        if secs_until_midnight < 0:
            secs_until_midnight += 24 * 60 * 60  # Add a day if past midnight
        
        # Start the daily timer
        self.daily_timer = QTimer(self)
        self.daily_timer.timeout.connect(self.daily_update)
        self.daily_timer.start(secs_until_midnight * 1000)
    
    def create_tray_icon(self):
        """Create system tray icon with menu"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("preferences-desktop"))
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show Widget", self)
        show_action.triggered.connect(self.show)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        
        refresh_action = QAction("Refresh Data", self)
        refresh_action.triggered.connect(self.update_data)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(settings_action)
        tray_menu.addAction(refresh_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Connect signals
        self.tray_icon.activated.connect(self.tray_icon_activated)
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
    
    def update_data(self):
        """Update all data (prayer times, Quran verse, hadith)"""
        self.update_prayer_times()
        self.update_quran_verse()
        
        if self.config['appearance']['show_hadith']:
            self.update_hadith()
    
    def daily_update(self):
        """Handle daily updates"""
        self.update_data()
        
        # Reset timer for next day
        self.daily_timer.start(24 * 60 * 60 * 1000)  # 24 hours
    
    def update_prayer_times(self):
        """Update prayer times from API"""
        try:
            # Get today's date
            today = QDate.currentDate()
            date_str = today.toString("dd-MM-yyyy")
            
            # Fetch prayer times
            params = {
                'city': self.config['location']['city'],
                'country': self.config['location']['country'],
                'method': 2,  # ISNA method
                'date': date_str,
                'timezone': self.config['location']['timezone']  # Add timezone parameter
            }
            
            response = requests.get(self.config['api']['prayer_api'], params=params)
            data = response.json()
            
            if data['code'] == 200:
                timings = data['data']['timings']
                
                # Extract prayer times
                self.prayer_times = {
                    'Fajr': self.time_to_datetime(timings['Fajr']),
                    'Sunrise': self.time_to_datetime(timings['Sunrise']),
                    'Dhuhr': self.time_to_datetime(timings['Dhuhr']),
                    'Asr': self.time_to_datetime(timings['Asr']),
                    'Maghrib': self.time_to_datetime(timings['Maghrib']),
                    'Isha': self.time_to_datetime(timings['Isha']),
                    'Midnight': self.time_to_datetime(timings['Midnight'])
                }
                
                isha_time = self.prayer_times['Isha']
                tomorrow = QDate.currentDate().addDays(1)
                
                # Fetch tomorrow's Fajr time
                tomorrow_params = params.copy()
                tomorrow_params['date'] = tomorrow.toString("dd-MM-yyyy")
                tomorrow_response = requests.get(self.config['api']['prayer_api'], params=tomorrow_params)
                tomorrow_data = tomorrow_response.json()
                
                if tomorrow_data['code'] == 200:
                    tomorrow_fajr = self.time_to_datetime(tomorrow_data['data']['timings']['Fajr'])
                    tomorrow_fajr = QDateTime(tomorrow, tomorrow_fajr.time())
                    
                    # Calculate midnight as the midpoint
                    seconds_between = isha_time.secsTo(tomorrow_fajr)
                    midnight_seconds = seconds_between // 2
                    self.prayer_times['Midnight'] = isha_time.addSecs(midnight_seconds)
                
                # Update next prayer time
                self.update_next_prayer()
                # Add this line to update the prayer time displays
                self.update_prayer_displays()
            else:
                self.next_prayer_label.setText("Prayer API Error: Try again later")
                self.countdown_label.setText("--:--:--")
                
        except Exception as e:
            self.next_prayer_label.setText(f"Error: Could not update prayer times")
            self.countdown_label.setText("--:--:--")
            print(f"Error updating prayer times: {e}")
    
    def time_to_datetime(self, time_str):
        """Convert time string to QDateTime"""
        today = QDate.currentDate()
        time = QTime.fromString(time_str, "HH:mm")
        return QDateTime(today, time)
    
    def update_next_prayer(self):
        """Determine the next prayer time"""
        now = QDateTime.currentDateTime()
        
        # Find the next prayer
        next_prayer = None
        next_prayer_time = None
        
        for prayer, time in self.prayer_times.items():
            if time > now:
                if next_prayer_time is None or time < next_prayer_time:
                    next_prayer = prayer
                    next_prayer_time = time
        
        # If no next prayer found, it means all prayers for today are done
        # Use tomorrow's Fajr
        if next_prayer is None:
            tomorrow = QDate.currentDate().addDays(1)
            next_prayer = "Fajr (Tomorrow)"
            
            # Fetch tomorrow's prayer times
            date_str = tomorrow.toString("dd-MM-yyyy")
            
            params = {
                'city': self.config['location']['city'],
                'country': self.config['location']['country'],
                'method': 2,  # ISNA method
                'date': date_str
            }
            
            try:
                response = requests.get(self.config['api']['prayer_api'], params=params)
                data = response.json()
                
                if data['code'] == 200:
                    fajr_time = data['data']['timings']['Fajr']
                    time = QTime.fromString(fajr_time, "HH:mm")
                    next_prayer_time = QDateTime(tomorrow, time)
                else:
                    self.next_prayer_label.setText("Could not fetch tomorrow's prayer times")
                    return
            except Exception as e:
                self.next_prayer_label.setText("Error fetching tomorrow's prayer times")
                print(f"Error: {e}")
                return
        
        # Store next prayer information
        self.next_prayer = next_prayer
        self.next_prayer_time = next_prayer_time
        
        # Update labels
        self.next_prayer_label.setText(f"Next: {self.next_prayer}")
        self.update_countdown()
    
    def update_countdown(self):
        """Update the countdown timer to next prayer"""
        if hasattr(self, 'next_prayer_time'):
            now = QDateTime.currentDateTime()
            seconds_remaining = now.secsTo(self.next_prayer_time)
            
            if seconds_remaining > 0:
                hours = seconds_remaining // 3600
                minutes = (seconds_remaining % 3600) // 60
                seconds = seconds_remaining % 60
                
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.countdown_label.setText(f"Time Remaining: {time_str}")
            else:
                # Time has passed, update next prayer
                self.update_prayer_times()
    
    def update_quran_verse(self):
        """Update the daily Quran verse"""
        try:
            # Fetch random verse
            response = requests.get(self.config['api']['quran_api'])
            data = response.json()
            
            if data['code'] == 200:
                verse = data['data']
                
                arabic_text = verse['text']
                surah_name = verse['surah']['englishName']
                verse_number = verse['numberInSurah']
                
                # Get translation
                translation_response = requests.get(f"https://api.alquran.cloud/v1/ayah/{verse['number']}/en.sahih")
                translation_data = translation_response.json()
                
                if translation_data['code'] == 200:
                    translation_text = translation_data['data']['text']
                    
                    # Update UI
                    if self.config['appearance']['show_arabic']:
                        self.quran_arabic.setText(arabic_text)
                    
                    if self.config['appearance']['show_translation']:
                        self.quran_translation.setText(translation_text)
                    
                    self.verse_reference.setText(f"Surah {surah_name} ({verse_number})")
                else:
                    self.quran_translation.setText("Could not load translation")
            else:
                self.quran_arabic.setText("Could not load verse")
                self.quran_translation.setText("API error")
                
        except Exception as e:
            self.quran_arabic.setText("Error loading verse")
            self.quran_translation.setText(f"Please check your internet connection")
            print(f"Error updating Quran verse: {e}")
    
    def update_hadith(self):
        """Update the daily hadith"""
        try:
            # Fetch random hadith
            response = requests.get(self.config['api']['hadith_api'])
            data = response.json()
            
            if 'data' in data and data['data']:
                hadith = data['data']
                
                hadith_text = hadith.get('hadith_english', "")
                hadith_source = f"Sahih al-Bukhari {hadith.get('hadith_number', '')}"
                
                # Update UI
                self.hadith_text.setText(hadith_text)
                self.hadith_source.setText(f"Source: {hadith_source}")
            else:
                self.hadith_text.setText("Could not load hadith")
                self.hadith_source.setText("API error")
                
        except Exception as e:
            self.hadith_text.setText("Error loading hadith")
            self.hadith_source.setText("Please check your internet connection")
            print(f"Error updating hadith: {e}")
    
    def open_settings(self):
        """Open settings dialog"""
        settings_dialog = SettingsDialog(self.config, self)
        if settings_dialog.exec_() == QDialog.Accepted:
            self.config = settings_dialog.get_config()
            self.save_config()
            self.apply_theme()
            self.update_data()
    
    def apply_theme(self):
        """Apply the selected theme"""
        if self.config['appearance']['theme'] == 'dark':
            self.setStyleSheet("""
                QWidget {
                    background-color: #2D2D30;
                    color: #EEEEEE;
                }
                QLabel {
                    color: #EEEEEE;
                }
                QPushButton {
                    background-color: #3E3E42;
                    color: #EEEEEE;
                    border: 1px solid #555555;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #4E4E52;
                }
            """)
        else:  # Light theme
            self.setStyleSheet("""
                QWidget {
                    background-color: #F0F0F0;
                    color: #333333;
                }
                QLabel {
                    color: #333333;
                }
                QPushButton {
                    background-color: #E0E0E0;
                    color: #333333;
                    border: 1px solid #AAAAAA;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #D0D0D0;
                }
            """)
        
        # Update font size for Arabic text
        self.quran_arabic.setStyleSheet(f"font-size: {self.config['appearance']['font_size'] + 4}px; font-weight: bold;")
    
    def quit_application(self):
        """Quit the application"""
        QApplication.quit()
    
    def closeEvent(self, event):
        """Handle close event"""
        event.ignore()
        self.hide()
    
    def update_prayer_displays(self):
        """Update all prayer time displays"""
        if hasattr(self, 'prayer_times'):
            for prayer, time in self.prayer_times.items():
                if prayer in self.prayer_labels:
                    time_str = time.toString('hh:mm')
                    self.prayer_labels[prayer].setText(time_str)
                    
                    # Highlight the next prayer
                    if prayer == self.next_prayer:
                        self.prayer_labels[prayer].setStyleSheet("font-weight: bold; color: #2196F3;")
                    else:
                        self.prayer_labels[prayer].setStyleSheet("")


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.init_ui()
    
    def init_ui(self):
        """Initialize settings dialog UI"""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Location settings
        location_form = QFormLayout()
        
        self.city_input = QLineEdit(self.config['location']['city'])
        self.country_input = QLineEdit(self.config['location']['country'])
        self.timezone_input = QLineEdit(self.config['location']['timezone'])
        
        location_form.addRow("City:", self.city_input)
        location_form.addRow("Country:", self.country_input)
        location_form.addRow("Timezone:", self.timezone_input)
        
        # Appearance settings
        appearance_form = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(self.config['appearance']['theme'])
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.config['appearance']['font_size'])
        
        appearance_form.addRow("Theme:", self.theme_combo)
        appearance_form.addRow("Font Size:", self.font_size_spin)
        
        # Button layout
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        # Add all layouts to main layout
        layout.addLayout(location_form)
        layout.addLayout(appearance_form)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def get_config(self):
        """Get the updated configuration"""
        self.config['location']['city'] = self.city_input.text()
        self.config['location']['country'] = self.country_input.text()
        self.config['location']['timezone'] = self.timezone_input.text()
        self.config['appearance']['theme'] = self.theme_combo.currentText()
        self.config['appearance']['font_size'] = self.font_size_spin.value()
        
        return self.config


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Islamic Widget")
    
    widget = IslamicWidget()
    widget.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()