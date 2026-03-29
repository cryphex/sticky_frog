# 🐸 Sticky Frog

**Sticky Frog 🐸** is a simple, powerful Discord bot designed to keep important messages "stuck" at the bottom of a channel. Whenever new messages are sent, the bot automatically deletes its previous post and resends the sticky message so it remains visible to everyone.

## ✨ Features

- 📌 **Sticky Messages:** Pin any text to the bottom of a specific channel.
- 🔄 **Auto-Relocation:** The message "travels" downward as users chat.
- 💾 **Persistent Storage:** Uses SQLite to ensure stickies stay active even after a bot restart.
- ⏱️ **Cooldown Protection:** Built-in 3-second delay to prevent spam and API rate limiting.
- 🔒 **Permission Based:** Only users with `Manage Messages` permissions can set or stop stickies.

## 🛠️ Installation

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your system.

### 2. Install Dependencies
Clone this repository or copy the code, then install the required libraries by using the **requirements.txt** file:
```bash
pip install -r requirements.txt
```

### 3. Configuration
Create a .env file in the root directory and add your bot token:
```bash
DISCORD_BOT_TOKEN=YOUR_TOKEN_HERE
```

## 🚀 Commands (Slash Commands)
|Command|Description|
|---|---|
|/stick [message]|Creates a new sticky message in the current channel.|
|/stickstop|Stops the stickying process and removes the active sticky message.|
