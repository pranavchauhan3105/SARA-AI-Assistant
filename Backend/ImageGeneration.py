import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import get_key
import os
from time import sleep

# --- SETUP AND CONFIGURATION ---

# Ensure the main data directory exists
os.makedirs("Data", exist_ok=True)

# Define the path for the communication file
IMAGE_GEN_FILE = os.path.join("Frontend", "Files", "ImageGeneration.data")

# IMPROVEMENT 1: Robust Configuration and Startup
# Load API key and configure headers within a try-except block to handle errors early.
try:
    HUGGINGFACE_API_KEY = get_key('.env', 'HuggingFaceAPIKey')
    if not HUGGINGFACE_API_KEY:
        raise ValueError("HuggingFaceAPIKey not found or is empty in .env file.")
    
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
except (ValueError, FileNotFoundError) as e:
    print(f"Error: Configuration failed - {e}")
    exit() # Exit if the API key isn't configured properly

# --- CORE FUNCTIONS ---

def open_images(prompt: str):
    """Opens and displays the four generated images for a given prompt."""
    folder_path = "Data"
    # Sanitize prompt for use in filenames
    safe_prompt = prompt.replace(" ", "_")
    files = [f"{safe_prompt}{i}.jpg" for i in range(1, 5)]

    print("Displaying generated images...")
    for jpg_file in files:
        image_path = os.path.join(folder_path, jpg_file)
        try:
            img = Image.open(image_path)
            img.show()
            sleep(1)  # Stagger the opening of images slightly
        except IOError:
            print(f"Error: Unable to open {image_path}. It may not exist or is corrupted.")

# IMPROVEMENT 2: Enhanced API Error Handling
async def query(payload: dict):
    """Sends a single asynchronous request to the Hugging Face API with better error logging."""
    try:
        response = await asyncio.to_thread(requests.post, API_URL, headers=HEADERS, json=payload)
        response.raise_for_status() # Raises an exception for bad status codes (4xx or 5xx)
        return response.content
    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during API query: {e}")
        return None

async def generate_images_async(prompt: str):
    """Creates and runs four concurrent image generation tasks."""
    print("Sending 4 concurrent requests to the API...")
    tasks = []
    for i in range(4):
        # Create a unique, enhanced payload for each image
        payload = {
            "inputs": f"{prompt}, 4k, high-resolution, photorealistic, seed={randint(0, 1000000)}",
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    # Wait for all API calls to complete
    image_bytes_list = await asyncio.gather(*tasks)

    # Save the successfully generated images to files
    saved_count = 0
    safe_prompt = prompt.replace(' ', '_')
    for i, image_bytes in enumerate(image_bytes_list):
        if image_bytes:
            file_path = os.path.join("Data", f"{safe_prompt}{i + 1}.jpg")
            try:
                with open(file_path, "wb") as f:
                    f.write(image_bytes)
                saved_count += 1
            except IOError as e:
                print(f"Error saving image {i+1}: {e}")
    print(f"Successfully saved {saved_count} of 4 images.")

def run_image_generation(prompt: str):
    """Synchronous wrapper to generate and then open images."""
    asyncio.run(generate_images_async(prompt))
    open_images(prompt)

# --- MAIN SERVICE LOOP ---

# IMPROVEMENT 3 & 4: Refined Main Loop and Clearer Feedback
def main():
    """Monitors for image generation requests and processes them."""
    print("--- Image Generation Service Started ---")
    print("Waiting for a request from the frontend...")
    
    while True:
        try:
            with open(IMAGE_GEN_FILE, "r") as f:
                data = f.read().strip()

            # Split data only if it's not empty
            if data:
                prompt, status = data.split(",", 1)

                if status == "True":
                    print(f"\nReceived request to generate images for prompt: '{prompt}'")
                    run_image_generation(prompt=prompt)

                    # Reset the status in the file after generating images
                    with open(IMAGE_GEN_FILE, "w") as f:
                        f.write("False,False")
                    
                    print("\nTask complete. Waiting for new request...")
            
            sleep(2) # Wait 2 seconds before polling again

        except FileNotFoundError:
            print("Communication file not found. Waiting for frontend to create it...")
            sleep(5)
        except ValueError:
            # Handles cases where the file is empty or being written to.
            sleep(1)
        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")
            sleep(5)

if __name__ == "__main__":
    main()