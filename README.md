# Archero 2 Autoclicker

Automates Archero 2 daily energy runs. Detects game screens via image matching and injects taps directly into the iPhone — no cursor movement, works in the background while you use your computer normally.

---

## Requirements

- Mac with Apple Silicon (M1 or later)
- Xcode (full app — **not** just Command Line Tools)
- Node.js
- Python 3.11+
- iPhone with Developer Mode enabled

---

## First-Time Setup (new machine)

### 1. Enable Developer Mode on your iPhone
`Settings → Privacy & Security → Developer Mode → on`
The phone will restart. Approve it.

### 2. Install Xcode
Download from the Mac App Store. After installing, open it once and accept the license agreement.

### 3. Install Node.js
```bash
brew install node
```

### 4. Install WebDriverAgent (WDA)
```bash
npm install -g appium-webdriveragent
```

### 5. Sign WDA with your Apple ID
```bash
open "$(npm root -g)/appium-webdriveragent/WebDriverAgent.xcodeproj"
```

In Xcode:
- Select the **WebDriverAgentLib** target → **Signing & Capabilities** tab
  - Enable **Automatically manage signing**
  - Set **Team** to your personal Apple ID (add it under Xcode → Settings → Accounts if needed)
- Repeat for the **WebDriverAgentRunner** target

### 6. Set up Python environment
```bash
cd /path/to/archero
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 7. Trust your Mac on the iPhone
Connect the iPhone via USB. Tap **Trust** on the phone when prompted.

### 8. Run
```bash
./archero.sh          # WiFi mode — no cable needed
./archero.sh --usb    # USB mode — cable plugged in
```

Open Archero 2 on your phone before or after running — the bot will detect wherever you are in the game and resume from there.

---

## Daily Usage

```bash
./archero.sh
```

That's it. The script:
1. Finds your iPhone automatically
2. Starts WDA on the phone
3. Detects the phone IP (WiFi) or starts iproxy (USB)
4. Launches the bot

Stop with **Ctrl+C**.

---

## Recurring Maintenance

### Every 7 days — re-sign WDA (free Apple Developer account)
The provisioning profile expires weekly. When `./archero.sh` fails with a signing error:

```bash
open "$(npm root -g)/appium-webdriveragent/WebDriverAgent.xcodeproj"
```

In Xcode, select **WebDriverAgentRunner** → **Signing & Capabilities** → click **Try Again** (or toggle the team off and back on). Do the same for **WebDriverAgentLib**. Close Xcode and run `./archero.sh` again.

---

## Troubleshooting

### `❌ No iPhone found`
- Make sure the phone is unlocked
- If using USB: tap **Trust** on the phone
- If using WiFi: phone and Mac must be on the same network
- Try running `xcrun devicectl list devices` to see if the phone shows up

### `❌ WDA crashed — check /tmp/wda.log`
Run `tail -30 /tmp/wda.log` to see the error.

**Signing expired (most common):**
```
No profiles for 'com.*.WebDriverAgentRunner.xctrunner' were found
```
→ Re-sign WDA in Xcode (see *Every 7 days* above)

**Build failed:**
```
error: SDK not found
```
→ Open Xcode, go to Settings → Platforms, and make sure the iOS platform is downloaded

### `❌ WDA did not start in time`
WDA started but the bot couldn't reach it.
- WiFi mode: make sure phone and Mac are on the same WiFi network (not a guest network)
- USB mode: make sure `iproxy` is installed — `brew install libimobiledevice`
- Try `--usb` mode if WiFi keeps failing

### `Password:` prompt appearing in terminal
Harmless — xcodebuild runs `devicectl diagnose` in the background when interrupted. Press Enter to dismiss, or open a new terminal tab and run `killall devicectl`.

### Bot stuck scanning and not clicking
The template images may not be matching. Take a native iOS screenshot, crop the relevant banner tightly in Photos, drop it in `images_native/`, and update `IMAGE_PATHS` in `config.py`.

### WDA connection drops mid-run
The bot will automatically stop after ~20 seconds of failed screenshots. Just run `./archero.sh` again.

---

## Adding New Game Screens

1. Take a screenshot on your iPhone (side button + volume up)
2. Crop to just the unique banner/text in Photos
3. AirDrop to Mac → save into `images_native/`
4. Add to `IMAGE_PATHS` in `config.py`:
   ```python
   "my_screen": _n("my_screenshot.png"),
   ```
5. Add detection logic in `state_machine.py`

The scaling from native resolution (1206×2622) down to matching resolution is automatic.

---

## File Structure

```
archero/
├── archero.sh          # Entry point — run this
├── bot.py              # Main loop
├── state_machine.py    # Game flow logic
├── clicker_wda.py      # Touch injection via WebDriverAgent
├── vision.py           # OpenCV template matching
├── config.py           # Timings, thresholds, image paths
├── images/             # Legacy Mac-captured templates (kept for reference)
└── images_native/      # Native iOS screenshot crops (active templates)
```
