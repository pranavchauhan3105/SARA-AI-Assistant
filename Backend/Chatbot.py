from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import os

# --- SETUP ---

# Ensure 'Data' directory exists
if not os.path.exists("Data"):
    os.makedirs("Data")

# Load environment variables
if not os.path.exists(".env"):
    print("Warning: .env file not found. Default values will be used.")
env_vars = dotenv_values(".env")

# Load credentials and names
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "SARA")
GroqAPIKey = env_vars.get("GroqAPIKey")

if not GroqAPIKey:
    print("Error: GroqAPIKey not found in .env file. Please add it.")
    exit()

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# Chat log file path
CHAT_LOG_FILE = "Data/ChatLog.json"

# --- SYSTEM MESSAGES ---

SystemPrompt = f"""You are a helpful and advanced AI assistant named {Assistantname}, speaking with {Username}.
- You have access to real-time information.
- Provide concise and direct answers in English only.
- Do not mention your training data or add extra notes.
"""

SystemChatBot = [
    {"role": "system", "content": SystemPrompt}
]

# --- HELPER FUNCTIONS ---

def RealtimeInformation():
    """Returns current real-time info as string."""
    now = datetime.datetime.now()
    return f"Current real-time information: {now.strftime('%A, %d %B %Y, %H:%M:%S')}."

def AnswerModifier(Answer):
    """Removes unnecessary blank lines from answer."""
    return '\n'.join(line for line in Answer.split('\n') if line.strip())

# --- MAIN CHAT FUNCTION ---

def ChatBot(Query):
    try:
        # Load existing chat log or initialize
        try:
            with open(CHAT_LOG_FILE, "r") as f:
                messages = load(f)
        except (FileNotFoundError, ValueError):
            messages = []

        # Add user's message
        messages.append({"role": "user", "content": Query})

        # Compose full prompt
        full_prompt = SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages

        # Call Groq API with a **supported model**
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # ✅ Updated to current model
            messages=full_prompt,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})

        # Trim history to avoid large prompts
        MAX_HISTORY = 20
        if len(messages) > MAX_HISTORY * 2:
            messages = messages[-MAX_HISTORY * 2:]

        # Save updated log
        with open(CHAT_LOG_FILE, "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer)
    
    except Exception as e:
        print("\n--- An Error Occurred ---")
        print(f"Error details: {e}")
        print("-------------------------\n")
        with open(CHAT_LOG_FILE, "w") as f:
            dump([], f)
        return "Sorry, I encountered an error. The chat history has been reset. Please try your query again."

# --- RUN CHAT LOOP ---

if __name__ == "__main__":
    print(f"Starting chat with {Assistantname}. Type 'exit' to quit.\n")
    while True:
        user_input = input(f"{Username}: ").strip()
        if user_input.lower() == 'exit':
            print(f"Goodbye from {Assistantname}!")
            break
        if not user_input:
            continue
        response = ChatBot(user_input)
        print(f"{Assistantname}: {response}\n")
