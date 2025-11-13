
import json
import os
import sys
import threading
import asyncio
from time import sleep
from flask import Flask, render_template, request, jsonify

# --- SETUP AND PATHS ---
# Add Backend to Python Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Backend')))

# Import backend modules
from Model import FirstLayerDMM
from Chatbot import ChatBot
from RealtimeSearchEngine import RealtimeSearchEngine
from Automation import Automation, Content
from SpeechToText import SpeechRecognition
from TextToSpeech import TextToSpeech

# Initialize Flask App
app = Flask(__name__, template_folder='Frontend', static_folder='Frontend/static')

# --- SHARED STATE (IN-MEMORY) ---
app_state = {
    "status": "Idle",
    "chat_history": [{"role": "assistant", "content": "Hello! How can I assist you today?"}],
    "lock": threading.Lock()
}

# --- IMAGE GENERATION COMMUNICATION ---
def trigger_image_generation(prompt):
    """Writes the prompt to the communication file to trigger the image generation script."""
    try:
        with open(os.path.join("Frontend", "Files", "ImageGeneration.data"), "w") as f:
            f.write(f"{prompt},True")
    except Exception as e:
        print(f"Error triggering image generation: {e}")

# --- CORE PROCESSING LOGIC ---
def process_query(query):
    """Processes a user query: classification → execution."""
    try:
        with app_state["lock"]:
            app_state["status"] = "Thinking..."
            app_state["chat_history"].append({"role": "user", "content": query})

        # Classify user intent
        tasks = FirstLayerDMM(query)
        print(f"Tasks classified: {tasks}")

        if not tasks:
            response = "I'm not sure how to handle that. Could you rephrase?"
            with app_state["lock"]:
                app_state["chat_history"].append({"role": "assistant", "content": response})
            threading.Thread(target=TextToSpeech, args=(response,)).start()
            return

        # Execute tasks
        for task in tasks:
            response = ""

            # --- General Chat ---
            if task.startswith("general"):
                prompt = task.replace("general", "").strip()
                response = ChatBot(prompt)

            # --- Realtime Query ---
            elif task.startswith("realtime"):
                prompt = task.replace("realtime", "").strip()
                response = RealtimeSearchEngine(prompt)

            # --- Content Generation ---
            elif task.startswith("content"):
                prompt = task.replace("content", "").strip()
                threading.Thread(target=Content, args=(prompt,)).start()
                response = f"I've generated content on '{prompt}' and opened it in Notepad."

            # --- Image Generation ---
            elif task.startswith("generate image"):
                prompt = task.replace("generate image", "").strip()
                trigger_image_generation(prompt)
                response = "I'm generating your image. It’ll appear soon."

            # --- Automation / System Control / App Opening ---
            else:
                # ✅ FIXED: Properly await async Automation() inside a thread
                threading.Thread(target=lambda: asyncio.run(Automation([task]))).start()
                response = f"Executing your command: {task}"

            # --- Save and Speak Response ---
            if response:
                with app_state["lock"]:
                    app_state["chat_history"].append({"role": "assistant", "content": response})

                # Run Text-to-Speech in background
                threading.Thread(target=TextToSpeech, args=(response,)).start()

    except Exception as e:
        print(f"[ERROR] process_query: {e}")
        with app_state["lock"]:
            app_state["status"] = "Error"
            app_state["chat_history"].append({
                "role": "assistant",
                "content": "Sorry, an unexpected error occurred."
            })

    finally:
        with app_state["lock"]:
            app_state["status"] = "Idle"

# --- FLASK ROUTES ---
@app.route('/')
def index():
    """Serve the main web page."""
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def handle_query():
    """Handle text query from frontend."""
    data = request.json
    query = data.get('query')
    if query:
        threading.Thread(target=process_query, args=(query,)).start()
    return jsonify({"status": "received"})

@app.route('/start_voice', methods=['POST'])
def handle_voice():
    """Handle voice input request."""
    def voice_thread():
        with app_state["lock"]:
            app_state["status"] = "Listening..."

        try:
            voice_query = SpeechRecognition()
            if voice_query:
                process_query(voice_query)
            else:
                with app_state["lock"]:
                    app_state["status"] = "Idle"
        except Exception as e:
            print(f"Error during voice recognition: {e}")
            with app_state["lock"]:
                app_state["status"] = "Error"

    threading.Thread(target=voice_thread).start()
    return jsonify({"status": "listening"})

@app.route('/updates')
def get_updates():
    """Send live status + chat history to frontend."""
    with app_state["lock"]:
        return jsonify({
            "status": app_state["status"],
            "chat_history": app_state["chat_history"]
        })

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("\n--- S.A.R.A. INITIALIZING ---")
    print("IMPORTANT: Run 'Backend/ImageGeneration.py' in another terminal if you use image generation.")
    print("Open your browser and visit: http://127.0.0.1:5000\n")
    app.run(host='127.0.0.1', port=5000, debug=False)