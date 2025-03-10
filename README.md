# Islamic-Widget
A widget that displays prayer times, daily verses and ahadith for linux Fedora.

# Islamic Widget for Fedora

A desktop widget for Fedora Linux that provides:

- Daily Quranic verse with Arabic text and English translation
- Prayer time countdown for the next prayer
- Daily hadith display
- Configurable settings

## Features

### Daily Quranic Verse
- Displays a random verse from the Quran each day
- Shows both Arabic text and English translation
- Includes reference to surah and verse number

### Prayer Time Countdown
- Shows the next prayer time (or sunrise if that comes first)
- Displays a countdown timer to the next prayer
- Automatically updates when the time for a prayer passes

### Daily Hadith
- Displays a random hadith each day
- Shows source reference

### Configuration Options
- Set your location for accurate prayer times
- Choose between light and dark themes
- Adjust font size
- Customize which components are displayed

## Installation

### Automatic Installation

1. Download the installation script:
```bash
curl -O https://github.com/Dospoint0/Islamic-Widget/install.sh
```

2. Make it executable:
```bash
chmod +x install.sh
```

3. Run the installation script:
```bash
./install.sh
```

### Manual Installation

1. Install the required dependencies:
```bash
sudo dnf install python3-qt5 python3-pip
pip install --user requests
```

2. Download the widget script:
```bash
mkdir -p ~/.local/share/islamic-widget
curl -o ~/.local/share/islamic-widget/islamic-widget.py https://raw.githubusercontent.com/yourusername/islamic-widget/main/islamic-widget.py
chmod +x ~/.local/share/islamic-widget/islamic-widget.py
```

3. Create desktop entry:
```bash
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/islamic-widget.desktop << EOF
[Desktop Entry]
Name=Islamic Widget
Comment=Display Quranic verses, prayer times, and hadiths
Exec=python3 $HOME/.local/share/islamic-widget/islamic-widget.py
Icon=preferences-desktop
Terminal=false
Type=Application
Categories=Utility;Education;
StartupNotify=true
EOF
```

4. (Optional) Add to autostart:
```bash
mkdir -p ~/.config/autostart
cp ~/.local/share/applications/islamic-widget.desktop ~/.config/autostart/
```

## Usage

### Starting the Widget
You can start the widget in several ways:
- From the application menu
- By running `python3 ~/.local/share/islamic-widget/islamic-widget.py`
- Automatically at login (if you set up autostart)

### System Tray
The widget adds an icon to your system tray that provides quick access to:
- Show/hide the widget
- Access settings
- Refresh data
- Quit the application

### Configuring the Widget
Click the "Settings" button in the widget or right-click the system tray icon and select "Settings" to:
- Set your city and country for accurate prayer times
- Change theme (light/dark)
- Adjust font size

## API Sources

This widget uses the following APIs:
- Prayer times: Aladhan API (https://aladhan.com/prayer-times-api)
- Quran verses: Alquran Cloud API (https://alquran.cloud/api)
- Hadiths: Random Hadith Generator API

## Troubleshooting

### Widget doesn't show prayer times correctly
- Make sure your city and country are entered correctly
- Check that your system time and timezone are set correctly
- Ensure you have an active internet connection

### Widget doesn't start
- Verify that all dependencies are installed
- Check the application log for errors
- Make sure the script has executable permissions

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.