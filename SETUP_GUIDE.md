# 🚀 9P Social Analytics - Setup Guide

**Welcome!** This guide will help you get the 9P Social Analytics app running on your computer in just a few simple steps.

**No coding experience needed!** Just follow along step-by-step.

---

## 📋 What You'll Need

- A computer (Windows or Mac)
- Internet connection
- About 10-15 minutes

**That's it!** The app comes with everything pre-configured.

---

## 🪟 Setup Instructions for Windows

### Step 1: Install Docker Desktop

Docker is a tool that lets you run the app in a container (think of it like a portable environment).

1. **Download Docker Desktop:**
   - Go to: https://www.docker.com/products/docker-desktop/
   - Click the big **"Download for Windows"** button
   - Wait for the download to complete (~500MB file)

2. **Install Docker Desktop:**
   - Find the downloaded file (usually in your Downloads folder)
   - Double-click `Docker Desktop Installer.exe`
   - Click **"OK"** when asked about WSL 2
   - Click **"Install"**
   - Wait for installation to complete (5-10 minutes)
   - Click **"Close and restart"** when finished
   - Your computer will restart

3. **Start Docker Desktop:**
   - After restart, Docker Desktop should start automatically
   - If not, find "Docker Desktop" in your Start Menu and click it
   - Wait for Docker to fully start (you'll see a whale icon in your system tray)
   - **IMPORTANT:** Docker must be running every time you use the app

4. **Accept Terms (First Time Only):**
   - When Docker opens, it may ask you to accept terms
   - Click **"Accept"**
   - You can skip the tutorial/survey

### Step 2: Download the 9P Analytics App

1. **Download the app files:**
   - If you received a ZIP file:
     - Right-click the ZIP file → **"Extract All"**
     - Choose where to extract (e.g., Desktop or Documents)
     - Click **"Extract"**

   - If you have a GitHub link:
     - Click the green **"Code"** button
     - Click **"Download ZIP"**
     - Follow the extraction steps above

2. **Remember where you extracted it!**
   - For example: `C:\Users\YourName\Desktop\9P`

### Step 3: Run the App

1. **Open Command Prompt in the app folder:**
   - Open the folder where you extracted the app
   - Click in the **address bar** at the top (where it shows the folder path)
   - Type: `cmd` and press **Enter**
   - A black window (Command Prompt) will open

2. **Start the app:**
   - In the Command Prompt window, type:
     ```
     docker-compose up
     ```
   - Press **Enter**

3. **Wait for it to start (first time only):**
   - **First time:** This takes 5-10 minutes (downloading and building)
   - You'll see lots of text scrolling by - this is normal!
   - **Look for this message:**
     ```
     ✓ Ready in 2000ms
     ```
   - **Next times:** Starts in 10-20 seconds

4. **Open the app in your browser:**
   - Open your web browser (Chrome, Edge, Firefox, etc.)
   - Go to: **http://localhost:3000**
   - You should see the 9P Social Analytics home page! 🎉

### Step 4: Configure Your API Keys (One-Time Setup)

The app needs API keys to fetch data and analyze posts.

1. **Get Your API Keys:**

   **Reddit API (for fetching posts):**
   - Go to: https://www.reddit.com/prefs/apps
   - Log in to Reddit
   - Scroll down and click **"Create App"** or **"Create Another App"**
   - Fill in:
     - Name: `9P Analytics` (or anything)
     - Type: Select **"script"**
     - Description: Leave blank
     - About URL: Leave blank
     - Redirect URI: `http://localhost:3000`
   - Click **"Create app"**
   - **Copy these values:**
     - **Client ID**: Under the app name (looks like: `abc123xyz`)
     - **Client Secret**: Next to "secret" (looks like: `abc123xyz-ABC123XYZ`)

   **Anthropic API (for AI analysis):**
   - Go to: https://console.anthropic.com/
   - Sign up or log in
   - Click **"Get API Keys"** or go to: https://console.anthropic.com/settings/keys
   - Click **"Create Key"**
   - Give it a name: `9P Analytics`
   - Click **"Create Key"**
   - **Copy the API key** (starts with `sk-ant-`)
   - **IMPORTANT:** Copy it now! You won't see it again

2. **Add Keys to the App:**
   - In the app (http://localhost:3000), click **"Settings"** in the top navigation
   - Paste your keys:
     - **Anthropic API Key:** Paste your `sk-ant-...` key
     - **Reddit Client ID:** Paste your Reddit client ID
     - **Reddit Client Secret:** Paste your Reddit client secret
   - Click **"Save API Keys"**
   - You should see a success message! ✅

### Step 5: Start Analyzing!

1. Go back to the home page (click "9P Social Analytics" at the top)
2. Enter a brand name (e.g., "Nike", "Apple", "Tesla")
3. Choose a time range (e.g., "Last 7 days")
4. Click **"Analyze Brand"**
5. Wait for the analysis to complete (1-3 minutes depending on # of posts)
6. View your results! 📊

---

## 🍎 Setup Instructions for Mac

### Step 1: Install Docker Desktop

1. **Download Docker Desktop:**
   - Go to: https://www.docker.com/products/docker-desktop/
   - Click **"Download for Mac"**
   - Choose:
     - **"Mac with Intel chip"** if you have an older Mac
     - **"Mac with Apple chip"** if you have an M1/M2/M3 Mac
   - Wait for download (~500MB)

2. **Install Docker Desktop:**
   - Open your Downloads folder
   - Double-click `Docker.dmg`
   - Drag the Docker icon to the Applications folder
   - Open Applications folder
   - Double-click **Docker**

3. **Grant Permissions:**
   - macOS will ask for your password - enter it
   - Click **"Install"** or **"OK"** when asked about helper tools
   - Accept the service agreement

4. **Start Docker:**
   - Docker Desktop should now be running
   - You'll see a whale icon in your menu bar (top right)
   - Wait until it says "Docker Desktop is running"
   - **IMPORTANT:** Docker must be running every time you use the app

### Step 2: Download the 9P Analytics App

1. **Download the app files:**
   - If you received a ZIP file:
     - Double-click the ZIP to extract
     - Move the extracted folder to somewhere convenient (e.g., Desktop or Documents)

   - If you have a GitHub link:
     - Click the green **"Code"** button
     - Click **"Download ZIP"**
     - Double-click the ZIP to extract

2. **Remember where you put it!**
   - For example: `/Users/YourName/Desktop/9P`

### Step 3: Run the App

1. **Open Terminal:**
   - Press `Command + Space` (opens Spotlight)
   - Type: `Terminal`
   - Press **Enter**

2. **Navigate to the app folder:**
   - In Terminal, type: `cd ` (note the space after cd)
   - Drag the app folder from Finder into the Terminal window
   - Press **Enter**
   - (Alternative: type the full path, e.g., `cd ~/Desktop/9P`)

3. **Start the app:**
   - Type:
     ```bash
     docker-compose up
     ```
   - Press **Enter**

4. **Wait for it to start:**
   - **First time:** Takes 5-10 minutes (downloading and building)
   - You'll see lots of text - this is normal!
   - **Look for:**
     ```
     ✓ Ready in 2000ms
     ```
   - **Next times:** Starts in 10-20 seconds

5. **Open the app:**
   - Open your browser (Safari, Chrome, Firefox, etc.)
   - Go to: **http://localhost:3000**
   - You should see the 9P Social Analytics home page! 🎉

### Step 4: Configure Your API Keys (One-Time Setup)

Follow the same instructions as Windows Step 4 above (they're identical).

### Step 5: Start Analyzing!

Follow the same instructions as Windows Step 5 above.

---

## 🛠️ Common Issues & Solutions

### "Docker is not running"

**Problem:** You see an error like "Cannot connect to Docker daemon"

**Solution:**
- Open Docker Desktop application
- Wait for it to fully start (whale icon in taskbar/menu bar)
- Try the `docker-compose up` command again

---

### "Port 3000 is already in use"

**Problem:** Error says port 3000 is already being used

**Solution:**

**Windows:**
```cmd
netstat -ano | findstr :3000
taskkill /PID [NUMBER] /F
```
(Replace [NUMBER] with the number shown in the last column)

**Mac:**
```bash
lsof -ti:3000 | xargs kill -9
```

---

### "Classification failed" or "API error"

**Problem:** Analysis fails with API errors

**Solution:**
1. Check your API keys in Settings
2. Make sure you have:
   - Valid Anthropic API key (starts with `sk-ant-`)
   - Valid Reddit credentials
3. Make sure you have API credits:
   - Anthropic: Check https://console.anthropic.com/
   - Reddit: API is free

---

### App is slow or freezing

**Problem:** App feels slow

**Solution:**
1. Close other Docker containers: `docker ps` then `docker stop [container-name]`
2. Restart Docker Desktop
3. Allocate more resources to Docker:
   - Docker Desktop → Settings → Resources
   - Increase CPU and Memory

---

### Can't access localhost:3000

**Problem:** Browser says "This site can't be reached"

**Solution:**
1. Make sure Docker is running
2. Make sure you ran `docker-compose up` and it finished starting
3. Try: `http://127.0.0.1:3000` instead
4. Check no firewall is blocking port 3000

---

## 📝 Daily Usage

### Starting the App

**Every time you want to use the app:**

1. **Make sure Docker Desktop is running** (check for whale icon)
2. **Open Terminal/Command Prompt** in the app folder
3. **Run:** `docker-compose up`
4. **Wait for:** `✓ Ready in...` message
5. **Open browser to:** http://localhost:3000

### Stopping the App

When you're done using the app:

1. Go to the Terminal/Command Prompt window
2. Press `Ctrl + C` (Windows) or `Control + C` (Mac)
3. Wait for it to shut down gracefully
4. You can now close Docker Desktop if you want

**Or keep it running!** The app uses minimal resources when idle.

---

## 🔄 Updating the App

When a new version is released:

1. **Download the new files** (same as Step 2 in setup)
2. **Stop the old app:** Press `Ctrl+C` in Terminal
3. **Remove old container:**
   ```bash
   docker-compose down
   ```
4. **Rebuild with new code:**
   ```bash
   docker-compose up --build
   ```

---

## ❓ Need Help?

If you're stuck:

1. **Check the error message** in the Terminal/Command Prompt
2. **Make sure:**
   - Docker Desktop is running
   - You're in the correct folder
   - You have internet connection
   - Your API keys are configured
3. **Try restarting everything:**
   - Stop the app (`Ctrl+C`)
   - Close Docker Desktop
   - Restart Docker Desktop
   - Try `docker-compose up` again

---

## 🎯 Quick Command Reference

**Start app:**
```bash
docker-compose up
```

**Start app in background (doesn't take over terminal):**
```bash
docker-compose up -d
```

**Stop app:**
```bash
Ctrl+C (in terminal)
# OR
docker-compose down
```

**Rebuild app (after updates):**
```bash
docker-compose up --build
```

**View logs (if running in background):**
```bash
docker-compose logs -f
```

**Remove everything and start fresh:**
```bash
docker-compose down
docker-compose up --build
```

---

## 💡 Tips & Tricks

1. **Keep Docker Desktop running** - The app won't work without it
2. **Bookmark http://localhost:3000** for quick access
3. **Your API keys are saved locally** - You only configure them once
4. **Analyses are saved in the shared database** - Everyone using this app can see all analyses
5. **Reddit API is rate-limited** - Don't analyze too many brands in quick succession

---

## 🎉 You're All Set!

Enjoy using 9P Social Analytics! Start analyzing brands and gaining insights from social media data.

**Quick Start Checklist:**
- ✅ Docker Desktop installed and running
- ✅ App files downloaded and extracted
- ✅ `docker-compose up` running successfully
- ✅ Browser open to http://localhost:3000
- ✅ API keys configured in Settings
- ✅ Ready to analyze brands!

Happy analyzing! 📊✨
