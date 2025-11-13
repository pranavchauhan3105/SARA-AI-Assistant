from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import mtranslate as mt

# --- SETUP ---
# Get the absolute path of the project's root directory
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables from the root .env file
env_vars = dotenv_values(os.path.join(ROOT_DIR, ".env"))
InputLanguage = env_vars.get("InputLanguage")

# --- HTML CODE ---
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;
        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;
            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };
            recognition.onend = function() { recognition.start(); };
            recognition.start();
        }
        function stopRecognition() {
            recognition.stop();
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''

HtmlCode = str(HtmlCode).replace("recognition.lang = '';", f"recognition.lang = '{InputLanguage}';")

# Define paths relative to the ROOT_DIR
VOICE_HTML_PATH = os.path.join(ROOT_DIR, "Data", "Voice.html")
TEMP_DIR_PATH = os.path.join(ROOT_DIR, "Frontend", "Files")

# Write the modified HTML code to a file
with open(VOICE_HTML_PATH, "w") as f:
    f.write(HtmlCode)

# --- WEBDRIVER SETUP ---
chrome_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# --- FUNCTIONS ---
def SetAssistantStatus(Status):
    """Sets the assistant's status by writing it to a file."""
    with open(os.path.join(TEMP_DIR_PATH, 'Status.data'), "w", encoding='utf-8') as file:
        file.write(Status)

def QueryModifier(Query):
    """Modifies a query to ensure proper punctuation and formatting."""
    new_query = Query.lower().strip()
    # ... (rest of the function remains the same)
    return new_query.capitalize()

def UniversalTranslator(Text):
    """Translates text into English."""
    return mt.translate(Text, "en", "auto").capitalize()

def SpeechRecognition():
    """Performs speech recognition using the webdriver."""
    driver.get("file:///" + VOICE_HTML_PATH)
    driver.find_element(by=By.ID, value="start").click()
    while True:
        try:
            Text = driver.find_element(by=By.ID, value="output").text
            if Text:
                driver.find_element(by=By.ID, value="end").click()
                if InputLanguage and "en" in InputLanguage.lower():
                    return QueryModifier(Text)
                else:
                    SetAssistantStatus("Translating...")
                    return QueryModifier(UniversalTranslator(Text))
        except Exception:
            pass

if __name__ == "__main__":
    while True:
        Text = SpeechRecognition()
        print(Text)