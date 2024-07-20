#!/bin/bash

# Function to check if the script is executable and make it executable if not
make_self_executable() {
    if [ ! -x "$0" ]; then
        echo "Script is not executable. Making it executable..."
        chmod +x "$0"
        echo "Script is now executable. Please run it again."
        exit 0
    fi
}

# Make the script executable if it's not already
make_self_executable

# Check if pyinstaller is installed
if ! command -v pyinstaller &> /dev/null
then
    echo "PyInstaller could not be found. Please install it first."
    exit 1
fi

# Check if main.py exists in the current directory
if [ ! -f "main.py" ]; then
    echo "main.py not found in the current directory."
    exit 1
fi

# Check for logos/logo.ico in the current directory
ICON_PATH="logos/logo.ico"
if [ ! -f "$ICON_PATH" ]; then
    echo "logo.ico not found in the logos directory."
    exit 1
fi

# Run pyinstaller to convert main.py to an executable with the icon
pyinstaller --onefile --icon="$ICON_PATH" main.py

# Check if the executable was created successfully
if [ $? -eq 0 ]; then
    echo "Executable created successfully."
    echo "You can find the executable in the 'dist' directory."
else
    echo "Failed to create executable."
fi
