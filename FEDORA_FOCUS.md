# Fedora Focus Documentation

## Overview

GC-Setup is now explicitly documented as a **Fedora-first** application. While it supports other distributions, Fedora users will have the most reliable and tested experience.

## Changes Made

### 1. README Updates

The README now prominently features:
- ⚠️ Warning header stating Fedora is the primary target
- Clear list of supported distributions with status indicators:
  - ✅ **Fedora** (primary, fully tested)
  - ⚠️ Other distros (community supported)
- Contributing section encouraging multi-distro contributions

### 2. First-Run Warning Dialog

**Features:**
- Appears automatically on first application launch
- Warns users that the app is designed for Fedora
- Acknowledges other distribution support with caveats
- Offers two options:
  - **Continue**: Proceeds and marks first-run as complete
  - **Exit**: Closes the application

**Implementation Details:**
- Flag file location: `~/.config/gc-setup/first-run-done`
- Dialog uses Adwaita AlertDialog for native GNOME look
- "Continue" button is styled as suggested action (blue)
- Dialog cannot be closed without making a choice

### 3. User Experience Flow

1. User launches GC-Setup for the first time
2. Main window appears
3. After 100ms, the warning dialog overlays the main window
4. User reads the Fedora-focused message
5. User chooses to continue or exit
6. If continuing, the flag is written and dialog won't show again

## Testing the First-Run Dialog

To test the dialog again after seeing it once:

```bash
# Remove the flag file
rm ~/.config/gc-setup/first-run-done

# Launch the application
# The dialog will appear again
```

## Code Locations

- **First-run dialog**: `src/main.py` (lines 65-113)
- **README documentation**: `README.md` (lines 8-16)

## Future Improvements

Consider:
1. Add distribution detection and show specific warnings for detected non-Fedora systems
2. Show different message text based on detected distribution
3. Add "Don't show again" checkbox for users who understand the limitation
4. Log which distribution users are running on (opt-in analytics)
