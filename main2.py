import speech_recognition as sr
import pyttsx3
import webbrowser
import datetime
import os
import random
from transformers import pipeline
import torch
import logging
import threading  # For asynchronous tasks
import time
import io

# --- Configuration ---
MODEL_NAME = 'microsoft/DialoGPT-medium'  # Or a smaller, faster model (e.g., distilgpt2)
LANGUAGE = 'en-in'
PAUSE_THRESHOLD = 0.5  # Reduced for faster response
LISTENING_TIMEOUT = 10  # Maximum listening time in seconds
SILENCE_THRESHOLD = 0.5  # Duration of silence to stop listening (seconds)
MAX_GENERATION_LENGTH = 150  # Adjust for speed/quality trade-off
GENERATION_TEMPERATURE_AI = 0.4  # Balance factual/creative
GENERATION_TEMPERATURE_CHAT = 0.7  # More natural chat
TOP_K = 30  # Reduce for speed
TOP_P = 0.7  # Reduce for speed
JARVIS_NAME = "Athena"
MUSIC_PATH = r"C:\Users\gauri\Downloads\Sanam-Teri-Kasam-Ankit-Tiwari-Palak-Muchhal.mp3"  # Replace with a valid path
OPENAI_DIR = "Openai"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Global Variables ---
generator = None
chat_history = []  # Use a list for efficient append/pop
chat_history_max_len = 3  # Keep only the last few turns
engine = pyttsx3.init()  # Initialize TTS engine once
recognizer = sr.Recognizer()  # Initialize recognizer once

# --- Helper Functions ---
def load_model():
    """Loads the text generation model asynchronously."""
    global generator
    try:
        generator = pipeline('conversational', model=MODEL_NAME)  # Use 'conversational' pipeline
        if torch.cuda.is_available():
            generator.model.to('cuda')
        logging.info("Model loaded successfully.")
    except Exception as e:
        logging.error(f"Error loading model: {e}")
        generator = None  # Ensure generator is None in case of error

def speak(text):
    """Speaks the given text using the TTS engine."""
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logging.error(f"Error during speech: {e}")

def listen_extended(silence_threshold=0.5, listening_timeout=10):
    """Listens for user input until a period of silence is detected and returns AudioData."""
    with sr.Microphone() as source:
        logging.info("Listening (extended)...")
        recognizer.adjust_for_ambient_noise(source)  # Calibrate for noise

        audio_buffer = io.BytesIO()
        listening = True
        start_time = time.time()
        last_speech = start_time

        while listening and (time.time() - start_time < listening_timeout):
            try:
                frame = source.stream.read(source.CHUNK)  # Use 'source' directly
                if frame:
                    audio_buffer.write(frame)
                    last_speech = time.time()
                elif (time.time() - last_speech) > silence_threshold:
                    listening = False
                    break
            except Exception as e:
                logging.error(f"Error reading audio stream: {e}")
                return None

        audio_data = sr.AudioData(audio_buffer.getvalue(), source.SAMPLE_RATE, source.SAMPLE_WIDTH)
        if len(audio_data.get_raw_data()) > 0:
            return audio_data
        else:
            logging.warning("No significant audio captured.")
            return None

def recognize_extended_speech(audio_data):
    """Recognizes speech from the extended AudioData."""
    if audio_data is None:
        return ""
    try:
        logging.info("Recognizing speech (extended)...")
        query = recognizer.recognize_google(audio_data, language=LANGUAGE)
        query = query.lower()
        logging.info(f"User said (extended): {query}")
        return query
    except sr.UnknownValueError:
        logging.warning("Could not understand audio (extended)")
        return ""
    except sr.RequestError as e:
        logging.error(f"Could not request results from Google Speech Recognition service; {e}")
        return ""
    except Exception as e:
        logging.error(f"An unexpected error occurred during recognition (extended): {e}")
        return ""

def update_chat_history(role, text):
    """Updates the chat history, keeping it within the maximum length."""
    chat_history.append({"role": role, "text": text})
    if len(chat_history) > chat_history_max_len:
        chat_history.pop(0)

def generate_response(query, max_length=MAX_GENERATION_LENGTH, temperature=0.7, top_k=None, top_p=None):
    """Generates a text response using the conversational model."""
    global generator
    if not generator:
        return "I'm sorry, the AI model is not loaded."
    try:
        conversation = " ".join([f"{msg['role']}: {msg['text']}" for msg in chat_history]) + f" User: {query}"
        response = generator(conversation, max_length=max_length, temperature=temperature, top_k=top_k, top_p=top_p)
        response_text = response.generated_responses[-1]
        return response_text
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return "I encountered an error while processing your request."

def chat(query):
    """Handles natural chat interaction with the user."""
    logging.info(f"User (Chat): {query}")
    update_chat_history("User", query)

    response_text = generate_response(query, temperature=GENERATION_TEMPERATURE_CHAT)

    logging.info(f"{JARVIS_NAME} (Chat): {response_text}")
    update_chat_history(JARVIS_NAME, response_text)
    speak(response_text)
    return response_text

def get_filename_from_prompt(prompt):
    """Generates a filename from the AI prompt."""
    return f"{OPENAI_DIR}/{''.join(prompt.split('intelligence')[1:]).strip()}.txt"

def save_ai_response(prompt, response_text):
    """Saves the AI response to a file."""
    if not os.path.exists(OPENAI_DIR):
        os.makedirs(OPENAI_DIR)
        logging.info(f"{OPENAI_DIR} directory created.")

    filename = get_filename_from_prompt(prompt)
    with open(filename, "w") as f:
        f.write(f"Prompt: {prompt}\nResponse: {response_text}")
    logging.info(f"File '{filename}' created successfully.")

def ai_response(prompt):
    """Handles AI-powered responses (explicitly triggered) with optimized generation."""
    logging.info(f"AI Prompt: {prompt}")

    response_text = generate_response(
        prompt,
        max_length=100,  # Adjust max_length as needed
        temperature=GENERATION_TEMPERATURE_AI,
        top_k=TOP_K,
        top_p=TOP_P
    )

    logging.info(f"AI Response: {response_text}")
    speak(response_text)
    save_ai_response(prompt, response_text)
    return response_text

# --- Command Handlers ---
def handle_how_are_you():
    responses = [
        "I'm doing well, thank you for asking! How about you?",
        "I'm feeling quite alright today.",
        "I'm good, just ready to assist you.",
        "Doing great! What can I do for you?",
        "I'm functioning optimally, thank you. What can I help you with?"
    ]
    response = random.choice(responses)
    logging.info(f"{JARVIS_NAME}: {response}")
    speak(response)

def handle_what_are_you_doing():
    responses = [
        "I'm currently here to help you with your requests.",
        "Just processing your commands and trying my best to assist.",
        "I'm in standby mode, ready for your instructions.",
        "Thinking about how I can be most helpful to you.",
        "Just keeping busy with my digital tasks."
    ]
    response = random.choice(responses)
    logging.info(f"{JARVIS_NAME}: {response}")
    speak(response)

def handle_your_name():
    responses = [
        f"My name is {JARVIS_NAME}.",
        f"You can call me {JARVIS_NAME}.",
        f"I am {JARVIS_NAME}, your virtual assistant.",
        f"It's {JARVIS_NAME} speaking.",
        f"{JARVIS_NAME} is the name I go by."
    ]
    response = random.choice(responses)
    logging.info(f"{JARVIS_NAME}: {response}")
    speak(response)

def handle_thank_you():
    responses = [
        "You're very welcome!",
        "Not a problem at all.",
        "Happy to help!",
        "My pleasure.",
        "Anytime!"
    ]
    response = random.choice(responses)
    logging.info(f"{JARVIS_NAME}: {response}")
    speak(response)

def handle_greeting():
    responses = [
        "Hello!",
        "Hi there!",
        "Hey!",
        "Greetings!",
        "Hello to you too!"
    ]
    response = random.choice(responses)
    logging.info(f"{JARVIS_NAME}: {response}")
    speak(response)

def handle_goodbye():
    responses = [
        "Goodbye!",
        "See you later!",
        "Have a great day!",
        "Farewell!",
        "Until next time!"
    ]
    response = random.choice(responses)
    logging.info(f"{JARVIS_NAME}: {response}")
    speak(response)

def handle_open_website(site_name, url):
    speak(f"Alright, opening {site_name} for you.")
    webbrowser.open(url)

def handle_the_time():
    now = datetime.datetime.now()
    hour = now.strftime("%I")
    minute = now.strftime("%M")
    am_pm = now.strftime("%p")
    speak(f"The current time is {hour}:{minute} {am_pm}.")

def handle_open_music():
    speak("Alright, let's play some tunes.")
    if os.path.exists(MUSIC_PATH):
        os.startfile(MUSIC_PATH)
    else:
        speak("Hmm, I can't seem to find that music file.")

def handle_quit():
    responses = [
        "Okay, shutting down. Goodbye!",
        f"Quitting {JARVIS_NAME}. Have a good one!",
        "Alright, I'm going offline. See you!",
        "Exiting now. Feel free to call on me again.",
        "Understood. Goodbye for now."
    ]
    response = random.choice(responses)
    logging.info(f"{JARVIS_NAME}: {response}")
    speak(response)

# --- Command Mapping ---
COMMAND_MAPPING = {
    "how are you": handle_how_are_you,
    "what are you doing": handle_what_are_you_doing,
    "your name": handle_your_name,
    "thank you": handle_thank_you,
    "thanks": handle_thank_you,
    "hello": handle_greeting,
    "hi": handle_greeting,
    "hey": handle_greeting,
    "goodbye": handle_goodbye,
    "bye": handle_goodbye,
    "see you later": handle_goodbye,
    "open youtube": (handle_open_website, "YouTube", "http://youtube.com"),
    "open wikipedia": (handle_open_website, "Wikipedia", "https://www.wikipedia.org"),
    "open google": (handle_open_website, "Google", "https://www.google.com"),
    "open linkedin": (handle_open_website, "LinkedIn", "https://www.linkedin.com/"),
    "open github": (handle_open_website, "GitHub", "https://github.com/"),
    "open stack overflow": (handle_open_website, "Stack Overflow", "https://stackoverflow.com/"),
    "open coursera": (handle_open_website, "Coursera", "https://www.coursera.org/"),
    "open google maps": (handle_open_website, "Google Maps", "https://www.google.com/maps"),
    "open maps": (handle_open_website, "Google Maps", "https://www.google.com/maps"),
    "open google news": (handle_open_website, "Google News", "https://news.google.com/"),
    "open news": (handle_open_website, "Google News", "https://news.google.com/"),
    "open google calendar": (handle_open_website, "Google Calendar", "https://calendar.google.com/"),
    "open calendar": (handle_open_website, "Google Calendar", "https://calendar.google.com/"),
    "open gmail": (handle_open_website, "Gmail", "https://mail.google.com/"),
    "open email": (handle_open_website, "Gmail", "https://mail.google.com/"),
    "the time": handle_the_time,
    "open music": handle_open_music,
    "jarvis quit": handle_quit,
    "quit jarvis": handle_quit,
    "exit jarvis": handle_quit,
    "athena quit": handle_quit,
    "quit athena": handle_quit,
    "exit athena": handle_quit,
}

# --- Main Loop ---
def main():
    logging.info('Basic Jarvis')
    welcome_messages = [
        f"Hello there! {JARVIS_NAME} at your service. How can I assist you?",
        "Greetings! What can I do for you today?",
        "Hi! I'm ready to help. What's on your mind?",
        f"Hello, it's {JARVIS_NAME} here. How may I be of assistance?",
        "Hi! How are you doing? What can I do for you?"
    ]
    welcome_message = random.choice(welcome_messages)
    logging.info(welcome_message)
    speak(welcome_message)

    while True:
        audio_data = listen_extended()  # Use the extended listening function
        query = recognize_extended_speech(audio_data)  # Recognize from the full audio

        if query:
            logging.info(f"User said: {query}")

            handled = False
            for key, action in COMMAND_MAPPING.items():
                if key in query:
                    logging.info(f"Executing command: {key}")
                    if isinstance(action, tuple):
                        action[0](*action[1:])  # Execute function with arguments
                    else:
                        action()  # Execute function directly
                    handled = True
                    break

            if not handled:
                if "using artificial intelligence" in query or "ai" in query:  # More flexible AI trigger
                    ai_response(prompt=query)
                else:
                    chat(query)  # Default to chat if no command is matched

        else:
            logging.info("Listening...")

if __name__ == '__main__':
    # Load the model in a separate thread to avoid blocking
    model_thread = threading.Thread(target=load_model)
    model_thread.start()

    main()