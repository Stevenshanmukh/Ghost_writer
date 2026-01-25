# 👻 GhostWriter
![GhostWriter](ghost_icon.png)

**Talk instead of typing.**

GhostWriter is a free, private tool for Windows that types what you say into *any* app—Word, Notepad, Discord, or your web browser. 

It works entirely on your computer. Your voice is **never** sent to the cloud.

---

## 🏃 Getting Started

### 1. Download & Install
You don't need to be a programmer to use this!
1.  **Install Python**: Download Python 3.10 or newer from [python.org](https://www.python.org/downloads/).
    > **IMPORTANT**: When installing, check the box that says **"Add Python to PATH"**.
2.  **Download GhostWriter**: Click the green **Code** button above -> **Download ZIP**. Unzip the folder.
3.  **Install Dependencies**:
    - Double-click the file named `install_requirements.bat` (if it exists) OR
    - Open the folder, right-click blank space -> **Open Terminal Here** -> type: `pip install -r requirements.txt` and hit Enter.

### 2. Run the App
Double-click the **`run.bat`** file.
*(You might see a black window pop up—that's normal!)*

### 3. How to Use
1.  Open the application you want to type into (like Microsoft Word).
2.  **Press F8** on your keyboard. You'll hear a "beep" and see a green ghost icon 🟢.
3.  **Speak clearly.**
4.  **Press F8 again** when done. You'll hear a lower beep.
5.  Wait a moment... your text will magically appear! ✨

---

## ⚙️ Settings

You can change how GhostWriter works using the dropdowns in the app window:

- **Hotkey (Default F8)**: Change the button you press to start/stop listening.
    - *Useful if F8 is already used by another game or app.*
- **Paste Speed**: Controls how fast the text is typed out.
    - *If text appears scrambled or missing letters, change this to "Slow".*
- **Start in Tray**: Checking this hides the app when it starts (look for the ghost icon near your clock).

---

## ❓ Troubleshooting

**"I press F8 but nothing happens!"**
- Make sure GhostWriter is running.
- Try clicking the **"Start Recording"** button in the app manually.
- Check if your microphone is muted in Windows settings.

**"The text is pasting weirdly / characters are missing."**
- Try changing the **Paste Speed** to **Slow** or **Very Slow**. Some apps (like remote desktops) need more time to process keys.

---

**Privacy Note**: GhostWriter runs `whisper` locally on your CPU. No data leaves your machine.
