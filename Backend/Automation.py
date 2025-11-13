# --- Imports ---
import os
import asyncio
import subprocess
import webbrowser
import psutil
import keyboard
import requests
import re  # Added for filename sanitization
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from pywhatkit import search, playonyt
from AppOpener import open as appopen
from groq import Groq
from rich import print

# --- Load .env ---
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")
Username = env_vars.get("Username", "User")

# --- Validate Key ---
if not GroqAPIKey:
    print("[bold red]❌ Missing GroqAPIKey in .env file![/]")
    exit()

# --- Setup Groq ---
client = Groq(api_key=GroqAPIKey)

# --- Constants ---
classes = ["zCubwf", "hgKElc", "LTKOO sY7ric", "Z0LcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta",
           "IZ6rdc", "O5uR6d LTKOO", "vlzY6d", "webanswers-webanswers_table_webanswers-table", "dDoN ikb4Bb gsrt", "sXLaOe", 
           "LWkfKe", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"]
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/110 Safari/537.36"
SystemChatBot = [{
    "role": "system",
    "content": f"Hello, I am {Username}. You're a content writer. You write letters, articles, and blogs professionally."
}]

# --- Ensure Data folder exists ---
os.makedirs("Data", exist_ok=True)

# --- Core Functions ---

def GoogleSearch(topic):
    search(topic)
    return True

def Content(topic):
    def open_file(file_path):
        subprocess.Popen(['notepad.exe', file_path])

    def content_ai(prompt):
        # SUGGESTION 1: Manage Chat History State
        # The 'messages' list is now local to this function to prevent history from carrying over.
        messages = []
        messages.append({"role": "user", "content": prompt})
        
        completion = client.chat.completions.create(
            # SUGGESTION 4: Update the AI Model Name
            # Replaced the invalid model with a valid one from Groq.
            model="llama-3.1-70b-versatile",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True
        )
        response = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                response += chunk.choices[0].delta.content
        response = response.strip().replace("</s>", "")
        messages.append({"role": "assistant", "content": response})
        return response

    cleaned = topic.replace("content ", "").strip()
    ai_text = content_ai(cleaned)

    # SUGGESTION 3: Sanitize Filenames
    # Remove characters that are invalid for filenames to prevent errors.
    safe_filename = re.sub(r'[\\/*?:"<>|]', "", cleaned).lower().replace(' ', '')
    filename = f"Data/{safe_filename}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(ai_text)

    open_file(filename)
    return True

def YouTubeSearch(topic):
    url = f"https://www.youtube.com/results?search_query={topic}"
    webbrowser.open(url)
    return True

def PlayYoutube(query):
    playonyt(query)
    return True

# SUGGESTION 2: Avoid Mutable Default Arguments
# Changed the default value of 'sess' to None.
def OpenApp(app, sess=None):
    # The session is now created inside the function if one isn't provided.
    if sess is None:
        sess = requests.session()
        
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        predefined = {
            "facebook": "https://www.facebook.com",
            "youtube": "https://www.youtube.com",
            "instagram": "https://www.instagram.com",
            "twitter": "https://www.twitter.com",
            "whatsapp": "https://web.whatsapp.com",
            "gmail": "https://mail.google.com",
        }
        if app.lower() in predefined:
            webbrowser.open(predefined[app.lower()])
            return True

        def extract_links(html):
            soup = BeautifulSoup(html, 'html.parser')
            return [g.find('a')['href'] for g in soup.find_all('div', class_='tF2Cxc') if g.find('a')]

        def search_google(query):
            url = f"https://www.google.com/search?q={query}"
            headers = {"User-Agent": useragent}
            r = sess.get(url, headers=headers)
            return r.text if r.status_code == 200 else None

        html = search_google(f"{app} site")
        if html:
            links = extract_links(html)
            if links:
                webbrowser.open(links[0])
            else:
                print(f"No valid links found for '{app}'")
        return True

def CloseApp(app):
    if "chrome" in app.lower():
        return False
    try:
        for process in psutil.process_iter(['pid', 'name']):
            if app.lower() in process.info['name'].lower():
                psutil.Process(process.info['pid']).terminate()
                return True
    except Exception as e:
        print(f"[red]Error closing app:[/] {e}")
    return False

def System(command):
    cmd_map = {
        "mute": lambda: keyboard.press_and_release("volume mute"),
        "unmute": lambda: keyboard.press_and_release("volume unmute"),
        "volume up": lambda: keyboard.press_and_release("volume up"),
        "volume down": lambda: keyboard.press_and_release("volume down"),
    }
    action = cmd_map.get(command.lower())
    if action:
        action()
        return True
    return False

# --- Async Controller ---

async def TranslateAndExecute(commands: list[str]):
    tasks = []

    for command in commands:
        if command.startswith("open "):
            tasks.append(asyncio.to_thread(OpenApp, command.removeprefix("open ")))
        elif command.startswith("close "):
            tasks.append(asyncio.to_thread(CloseApp, command.removeprefix("close ")))
        elif command.startswith("play "):
            tasks.append(asyncio.to_thread(PlayYoutube, command.removeprefix("play ")))
        elif command.startswith("content "):
            tasks.append(asyncio.to_thread(Content, command.removeprefix("content ")))
        elif command.startswith("google search "):
            tasks.append(asyncio.to_thread(GoogleSearch, command.removeprefix("google search ")))
        elif command.startswith("youtube search "):
            tasks.append(asyncio.to_thread(YouTubeSearch, command.removeprefix("youtube search ")))
        elif command.startswith("system "):
            tasks.append(asyncio.to_thread(System, command.removeprefix("system ")))
        else:
            print(f"[yellow]⚠️ Unknown command:[/] {command}")

    results = await asyncio.gather(*tasks)
    return results

async def Automation(commands: list[str]):
    await TranslateAndExecute(commands)
    return True

# --- Run Test Commands ---

if __name__ == "__main__":
    test_commands = [
        "system volume up",
        "open instagram",
        "open Spotify",
        "google search Nightwing comics",
        "youtube search Joji",
    ]
    asyncio.run(Automation(test_commands))