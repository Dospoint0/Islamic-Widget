#!/bin/bash

# Islamic Widget for Fedora - Installation Script

echo "Installing Islamic Widget for Fedora..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
  echo "Please run this script as a normal user, not as root."
  exit 1
fi

# Install dependencies
echo "Installing dependencies..."
sudo dnf install -y python3-qt5 python3-pip

# Create directories
echo "Creating application directories..."
mkdir -p ~/.local/share/islamic-widget
mkdir -p ~/.local/share/applications
mkdir -p ~/.config/islamic-widget

# Download the application
echo "Downloading application..."
curl -o ~/.local/share/islamic-widget/islamic-widget.py https://github.com/Dospoint0/Islamic-Widget/SalahWidget.py
chmod +x ~/.local/share/islamic-widget/islamic-widget.py

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --user requests

# Create desktop entry
echo "Creating desktop entry..."
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
X-GNOME-Autostart-enabled=true
EOF

# Create autostart entry
echo "Setting up autostart..."
mkdir -p ~/.config/autostart
cp ~/.local/share/applications/islamic-widget.desktop ~/.config/autostart/

echo "Installation complete!"
echo "You can find the Islamic Widget in your application menu."
echo "The widget will start automatically when you log in."
echo "To start it now, run: python3 ~/.local/share/islamic-widget/islamic-widget.py"