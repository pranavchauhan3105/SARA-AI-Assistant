import os
import datetime
from json import load, dump
from dotenv import dotenv_values
from groq import Groq
from googlesearch import search  # Make sure to install: pip install googlesearch-python

# --- SETUP ---

# Ensure 'Data' folder exists
os.makedirs("Data", exist_ok=True)

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "SARA")
GroqAPIKey = env_vars.get("GroqAPIKey")

if not GroqAPIKey:
    print("Error: GroqAPIKey not found in .env file.")
    exit()

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# --- SYSTEM PROMPT ---

System = f"""Hello, I am {Username}. You are a very accurate and advanced AI chatbot named {Assistantname}, with real-time access to up-to-date information from the internet.

*** Provide answers in a professional way using full stops, commas, question marks, and correct grammar. ***
*** Answer as directly as possible. If asked about time, just state the time, nothing more. ***
"""

SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"}
]

# --- HELPERS ---

def load_chat_log():
    try:
        with open("Data/ChatLog.json", "r") as f:
            return load(f)
    except (FileNotFoundError, ValueError):
        return []

def save_chat_log(messages):
    with open("Data/ChatLog.json", "w") as f:
        dump(messages, f, indent=4)

def GoogleSearch(query):
    try:
        results = list(search(query, advanced=True, num_results=5))
        output = f"The search results for '{query}' are:\n[start]\n"
        for result in results:
            title = getattr(result, "title", "No title available")
            description = getattr(result, "description", "No description available")
            output += f"Title: {title}\nDescription: {description}\n\n"
        output += "[end]"
        return output
    except Exception as e:
        return f"Google search failed: {e}"

def AnswerModifier(Answer):
    return '\n'.join(line for line in Answer.split('\n') if line.strip())

def RealtimeInformation():
    now = datetime.datetime.now()
    return f"""Use this real-time information if needed:
Day: {now.strftime("%A")}
Date: {now.strftime("%d")}
Month: {now.strftime("%B")}
Year: {now.strftime("%Y")}
Time: {now.strftime("%H")} hours, {now.strftime("%M")} minutes, {now.strftime("%S")} seconds.
"""

# --- MAIN FUNCTION ---

def RealtimeSearchEngine(prompt):
    global SystemChatBot

    messages = load_chat_log()

    # Do the search only once
    search_result = GoogleSearch(prompt)

    # Add search result to system prompt context, not to chat history
    full_prompt = (
        SystemChatBot
        + [{"role": "system", "content": search_result}]
        + [{"role": "system", "content": RealtimeInformation()}]
        + messages
        + [{"role": "user", "content": prompt}]
    )

    # Generate response using Groq
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # ✅ Updated model
            messages=full_prompt,
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=True
        )

        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.strip().replace("</s>", "")
        messages.append({"role": "user", "content": prompt})
        messages.append({"role": "assistant", "content": Answer})
        save_chat_log(messages)
        return AnswerModifier(Answer)

    except Exception as e:
        print("\n--- An Error Occurred ---")
        print(f"Error details: {e}")
        print("-------------------------\n")
        return "Sorry, an error occurred. Please try again later."

# --- MAIN LOOP ---

if __name__ == "__main__":
    print(f"Starting {Assistantname}. Type 'exit' to quit.\n")
    while True:
        prompt = input(f"{Username}: ").strip()
        if prompt.lower() == "exit":
            print(f"Goodbye from {Assistantname}!")
            break
        elif prompt:
            print(f"{Assistantname}: {RealtimeSearchEngine(prompt)}\n")
