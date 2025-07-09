import pyttsx3
import datetime
import speech_recognition as sr
import wikipedia
import webbrowser as wb
import os
import random
import pyautogui
import pyjokes
import json  # For storing conversation history
import subprocess  # For closing applications
import threading  # For potential background tasks
from playsound import playsound
import tkinter as tk
from tkinter import scrolledtext, Entry, Button, Label, PhotoImage, messagebox
from PIL import Image, ImageTk

# ----- Installation Requirements -----
# You need to install the following libraries:
# pip install pyttsx3 SpeechRecognition wikipedia webbrowser os random pyautogui pyjokes json pillow tkinter playsound
# -----------------------------------

engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
engine.setProperty('rate', 150)
engine.setProperty('volume', 1)

CONVERSATION_LOG = "conversation_log.json"
SEARCH_RESULTS_LOG = "search_results.json"
REMINDERS_FILE = "reminders.json"
ASSISTANT_NAME_FILE = "assistant_name.txt"
DEFAULT_ASSISTANT_NAME = "Jarvis"
# Consider making this configurable and using os.path.join
MUSIC_DIRECTORY = r"C:\Users\gauri\Music"

# --- UI Variables ---
root = tk.Tk()
root.title(f"{DEFAULT_ASSISTANT_NAME} AI Assistant")
root.geometry("600x500")
root.resizable(False, False)

# Load background image
try:
    bg_image = Image.open("background.png")  # Replace "background.png" with your image file
    bg_image = bg_image.resize((600, 500))
    bg_photo = ImageTk.PhotoImage(bg_image)
    bg_label = Label(root, image=bg_photo)
    bg_label.place(relwidth=1, relheight=1)
except FileNotFoundError:
    root.config(bg="lightblue")  # Default background color if image not found

chat_area = scrolledtext.ScrolledText(root, width=70, height=20, bg="lightgray", fg="black")
chat_area.config(state=tk.DISABLED)
chat_area.pack(pady=10)

input_entry = Entry(root, width=60, bg="white", fg="black")
input_entry.pack(pady=5)

def send_command():
    """Gets user input from the entry field and processes it."""
    query = input_entry.get().lower()
    input_entry.delete(0, tk.END)
    display_message(f"User (Typed): {query}", "user")
    process_query(query)

send_button = Button(root, text="Send (Type)", command=send_command, bg="skyblue", fg="white")
send_button.pack(pady=5)

# --- Functions ---

def speak(audio, from_assistant=True) -> None:
    """Speaks the given audio output and displays it in the chat area."""
    try:
        engine.say(audio)
        engine.runAndWait()
        display_message(f"{load_name()}: {audio}", "assistant")
        print(f"{load_name()}: {audio}")  # Display on terminal after speaking
    except Exception as e:
        print(f"Error during speech: {e}")
        display_message(f"Error during speech: {e}", "error")

def display_message(message, sender):
    """Displays a message in the chat area with appropriate formatting."""
    chat_area.config(state=tk.NORMAL)
    if sender == "user":
        chat_area.insert(tk.END, f"{message}\n", "user")
        chat_area.tag_config("user", foreground="blue")
    elif sender == "assistant":
        chat_area.insert(tk.END, f"{message}\n", "assistant")
        chat_area.tag_config("assistant", foreground="green")
    elif sender == "error":
        chat_area.insert(tk.END, f"Error: {message}\n", "error")
        chat_area.tag_config("error", foreground="red")
    chat_area.see(tk.END)
    chat_area.config(state=tk.DISABLED)

def speak_wait() -> None:
    """Speaks a short waiting message."""
    wait_messages = ["Just a moment...", "Opening that for you...", "Please wait...", "Working on it..."]
    speak(random.choice(wait_messages))

def time() -> None:
    """Tells the current time."""
    now = datetime.datetime.now()
    current_time = now.strftime("%I:%M:%S %p")
    response = f"The current time is {current_time}"
    speak(response)
    save_conversation("User asked for time", response)

def date() -> None:
    """Tells the current date."""
    now = datetime.datetime.now()
    current_date = now.strftime("%d %B %Y")
    response = f"The current date is {current_date}"
    speak(response)
    save_conversation("User asked for date", response)

def wishme() -> None:
    """Greets the user based on the time of day."""
    speak("Welcome back, sir!")
    print("Welcome back, sir!")

    hour = datetime.datetime.now().hour
    if 4 <= hour < 12:
        speak("Good morning!")
    elif 12 <= hour < 16:
        speak("Good afternoon!")
    elif 16 <= hour < 24:
        speak("Good evening!")
    else:
        speak("Good night, see you tomorrow.")

    assistant_name = load_name()
    initial_greeting = f"{assistant_name} at your service. Please tell me how may I assist you."
    speak(initial_greeting)
    load_reminders()

def screenshot() -> None:
    """Takes a screenshot and saves it."""
    try:
        img = pyautogui.screenshot()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_dir = r"c:\Users\gauri\OneDrive\Pictures\Screenshots"  # Make directory configurable?
        os.makedirs(screenshot_dir, exist_ok=True)  # Ensure directory exists
        img_path = os.path.join(screenshot_dir, f"screenshot_{timestamp}.png")
        img.save(img_path)
        response = f"Screenshot saved as {img_path}."
        speak(response)
        save_conversation("User asked for screenshot", response)
    except Exception as e:
        speak(f"Error taking screenshot: {e}")
        save_conversation("User asked for screenshot", f"Error: {e}")

def takecommand() -> str:
    """Takes microphone input from the user and returns it as text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        display_message("Listening...", "assistant")
        r.pause_threshold = 1.2  # Increased pause threshold
        r.adjust_for_ambient_noise(source, duration=1.5)  # Increased ambient noise adjustment
        audio = None

        try:
            audio = r.listen(source, timeout=5)
        except sr.WaitTimeoutError:
            display_message("Timeout occurred. Please try again.", "assistant")
            return None
        except sr.Error as e:
            display_message(f"Error with microphone: {e}", "error")
            print(f"Microphone error: {e}")
            return None

    if audio:
        try:
            display_message("Recognizing...", "assistant")
            query = r.recognize_google(audio, language="en-in")
            display_message(f"User (Voice): {query}", "user")
            print(f"User said: {query}")
            return query.lower()
        except sr.UnknownValueError:
            display_message("Sorry, I did not understand that.", "assistant")
            return None
        except sr.RequestError as e:
            display_message(f"Speech recognition service is unavailable: {e}", "error")
            print(f"Speech recognition error: {e}")
            return None
        except Exception as e:
            display_message(f"An unexpected error occurred during recognition: {e}", "error")
            print(f"Recognition error: {e}")
            return None
    return None

def play_music(song_name=None) -> None:
    """Plays music from the user's Music directory."""
    try:
        songs = os.listdir(MUSIC_DIRECTORY)
        if song_name:
            matching_songs = [song for song in songs if song_name.lower() in song.lower()]
            if matching_songs:
                song_path = os.path.join(MUSIC_DIRECTORY, random.choice(matching_songs))
                try:
                    playsound(song_path)
                    response = f"Playing {os.path.basename(song_path)}."
                    speak(response)
                    save_conversation(f"User asked to play {song_name}", response)
                except Exception as e:
                    response = f"Error playing '{os.path.basename(song_path)}' with playsound: {e}"
                    speak(response)
                    save_conversation(f"Error playing {song_name}", response)
            else:
                response = f"No song found matching '{song_name}'."
                speak(response)
                save_conversation(f"User asked to play {song_name}", response)
        elif songs:
            song_path = os.path.join(MUSIC_DIRECTORY, random.choice(songs))
            try:
                playsound(song_path)
                response = f"Playing {os.path.basename(song_path)}."
                speak(response)
                save_conversation("User asked to play music", response)
            except Exception as e:
                response = f"Error playing '{os.path.basename(song_path)}' with playsound: {e}"
                speak(response)
                save_conversation("User asked to play music", f"Error: {e}")
        else:
            response = "No songs found in the music directory."
            speak(response)
            save_conversation("User asked to play music", response)
    except FileNotFoundError:
        response = f"Music directory not found at '{MUSIC_DIRECTORY}'."
        speak(response)
        save_conversation("User asked to play music", response)
    except Exception as e:
        response = f"Error accessing music directory: {e}"
        speak(response)
        save_conversation("User asked to play music", f"Error: {e}")

def set_name() -> None:
    """Sets a new name for the assistant."""
    speak("What would you like to name me?")
    new_name = takecommand()
    if new_name:
        try:
            with open(ASSISTANT_NAME_FILE, "w") as f:
                f.write(new_name)
            response = f"Alright, I will be called {new_name} from now on."
            speak(response)
            save_conversation(f"User changed name to {new_name}", response)
            root.title(f"{new_name} AI Assistant")  # Update window title
        except Exception as e:
            speak(f"Error saving new name: {e}")
            save_conversation(f"User tried to change name to {new_name}", f"Error: {e}")
    else:
        response = "Sorry, I couldn't catch that."
        speak(response)
        save_conversation("User tried to change name", response)

def load_name() -> str:
    """Loads the assistant's name from a file, or uses a default name."""
    try:
        with open(ASSISTANT_NAME_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return DEFAULT_ASSISTANT_NAME
    except Exception as e:
        print(f"Error loading assistant name: {e}")
        return DEFAULT_ASSISTANT_NAME

def search_wikipedia(query):
    """Searches Wikipedia and displays the summary in the chat area."""
    speak(f"Searching Wikipedia for '{query}'...")
    try:
        result = wikipedia.summary(query, sentences=2)
        speak(result)
        save_search_result(f"Wikipedia search for: {query}", {"source": "Wikipedia", "summary": result})
        return True
    except wikipedia.exceptions.DisambiguationError:
        response = "Multiple results found. Please be more specific."
        speak(response)
        save_search_result(f"Wikipedia search for: {query}", {"error": "Multiple results found"})
        return False
    except wikipedia.exceptions.PageError:
        response = f"Sorry, the content '{query}' is not available on Wikipedia. Searching Google for '{query}'..."
        speak(response)
        search_on_google(query)
        save_search_result(f"Wikipedia search for: {query}", {"error": "Page not found", "action": "Searched Google"})
        return False
    except Exception as e:
        response = f"I encountered an issue while searching Wikipedia: {e}"
        speak(response)
        save_search_result(f"Wikipedia search for: {query}", {"error": f"Search error: {e}"})
        return False

def search_on_google(query):
    """Opens Google and searches for the given query."""
    speak_wait()
    search_url = f"https://www.google.com/search?q={query}"
    try:
        wb.open(search_url)
        response = f"Searching Google for '{query}' in your browser."
        speak(response)
        save_conversation(f"User asked to search on Google for: {query}", response)
        save_search_result("Google Search (Opened in Browser)", {"query": query, "action": "Opened in browser"})
    except wb.Error as e:
        speak(f"Error opening web browser for Google search: {e}")
        save_conversation(f"User asked to search on Google for: {query}", f"Error: {e}")
    except Exception as e:
        speak(f"An unexpected error occurred while opening Google: {e}")
        save_conversation(f"User asked to search on Google for: {query}", f"Error: {e}")

def respond_to_greeting(query):
    """Provides human-like responses to greetings."""
    greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
    responses = ["Hello!", "Hi there!", "Hey!", "Greetings to you!", "Good to hear from you.",
                 f"Hello, how can I help you today?"]
    for greeting in greetings:
        if greeting in query:
            response = random.choice(responses)
            speak(response)
            save_conversation(query, response)
            return True
    return False

def respond_to_thanks(query):
    """Provides human-like responses to thank you."""
    thanks = ["thank you", "thanks", "appreciate it"]
    responses = ["You're welcome!", "No problem.", "Glad I could help!", "My pleasure.", "Anytime!"]
    for thank in thanks:
        if thank in query:
            response = random.choice(responses)
            speak(response)
            save_conversation(query, response)
            return True
    return False

def have_a_conversation(query):
    """Simulates a basic conversation."""
    if respond_to_greeting(query):
        return True
    if respond_to_thanks(query):
        return True

    if "how are you" in query:
        responses = ["I'm doing well, thank you for asking!", "I'm functioning optimally.",
                     "Feeling good and ready to assist!"]
        response = random.choice(responses)
        speak(response)
        save_conversation(query, response)
        return True

    if "what can you do" in query:
        response = "I can tell you the time and date, search Wikipedia and Google, play music, open websites, take screenshots, tell jokes, remember things for you, and have basic conversations."
        speak(response)
        save_conversation(query, response)
        return True

    if "what is your location" in query:
        location_response = f"My current understanding is that we are in India."
        speak(location_response)
        save_conversation(query, location_response)
        return True

    if "what day is it" in query:
        today = datetime.datetime.now().strftime("%A")
        day_response = f"Today is {today}."
        speak(day_response)
        save_conversation(query, day_response)
        return True

    # --- More interactive responses ---
    if "how is the weather" in query or "what's the weather like" in query:
        # For a real weather report, you'd
        # need to integrate with a weather API
        weather_responses = ["It seems like a pleasant day.",
                             "I don't have real-time weather information right now, but I hope it's nice!",
                             "The weather is probably lovely!"]
        response = random.choice(weather_responses)
        speak(response)
        save_conversation(query, response)
        return True

    if "tell me something interesting" in query:
        interesting_facts = [
            "Honey never spoils.",
            "Bananas are berries, but strawberries aren't.",
            "The Eiffel Tower can be 15 cm taller during the summer due to thermal expansion.",
            "Octopuses have three hearts.",
            "There are more trees on Earth than stars in the Milky Way galaxy."
        ]
        response = random.choice(interesting_facts)
        speak(f"Here's something interesting: {response}")
        save_conversation(query, response)
        return True

    return False

def save_conversation(user_input, assistant_response):
    """Saves the conversation to a JSON file as a list of dictionaries."""
    conversation = []
    try:
        with open(CONVERSATION_LOG, "r") as f:
            try:
                conversation = json.load(f)
            except json.JSONDecodeError:
                # Handle empty or corrupted file
                conversation = []
    except FileNotFoundError:
        pass  # File doesn't exist yet

    conversation.append({"user": user_input, "assistant": assistant_response})

    try:
        with open(CONVERSATION_LOG, "w") as f:
            json.dump(conversation, f, indent=4)  # Use indent for better readability
    except Exception as e:
        print(f"Error saving conversation: {e}")

def load_conversation_history_gui():
    """Loads and displays the recent conversation history in a new window."""
    history_window = tk.Toplevel(root)
    history_window.title("Conversation History")
    history_text = scrolledtext.ScrolledText(history_window, width=70, height=20, bg="lightgray", fg="black")
    history_text.config(state=tk.DISABLED)
    history_text.pack(padx=10, pady=10)

    try:
        with open(CONVERSATION_LOG, "r") as f:
            history_text.config(state=tk.NORMAL)
            try:
                conversation_history = json.load(f)
                for entry in conversation_history:
                    history_text.insert(tk.END, f"User: {entry['user']}\n", "user")
                    history_text.tag_config("user", foreground="blue")
                    history_text.insert(tk.END, f"{load_name()}: {entry['assistant']}\n", "assistant")
                    history_text.tag_config("assistant", foreground="green")
                    history_text.insert(tk.END, "----\n")
            except json.JSONDecodeError:
                history_text.insert(tk.END, "No conversation history found or file is corrupted.\n")
            history_text.config(state=tk.DISABLED)
    except FileNotFoundError:
        history_text.insert(tk.END, "No conversation history found.\n")
    except Exception as e:
        history_text.insert(tk.END, f"Error reading conversation history: {e}\n", "error")
        history_text.tag_config("error", foreground="red")

def remember_thing_gui(query):
    """Remembers a piece of information provided by the user via a dialog."""
    memory_dialog = tk.Toplevel(root)
    memory_dialog.title("Remember Something")
    memory_label = Label(memory_dialog, text="What should I remember?")
    memory_label.pack(pady=5)
    memory_entry = Entry(memory_dialog, width=40)
    memory_entry.pack(pady=5)

    def save_memory():
        memory = memory_entry.get()
        if memory:
            try:
                with open(REMINDERS_FILE, "w") as f:
                    json.dump({"remembered": memory}, f)
                response = f"Okay, I will remember that: {memory}"
                speak(response)
                save_conversation(f"User asked to remember: {query}", response)
                print(f"Remembered: {memory}")
            except Exception as e:
                speak(f"Error saving reminder: {e}")
                save_conversation(f"User asked to remember: {query}", f"Error: {e}")
        else:
            response = "Sorry, I didn't catch what you wanted me to remember."
            speak(response)
            save_conversation(f"User asked to remember: {query}", response)
        memory_dialog.destroy()

    save_button = Button(memory_dialog, text="Remember", command=save_memory)
    save_button.pack(pady=10)

def recall_thing_gui():
    """Recalls the remembered information and displays it in the chat area."""
    try:
        with open(REMINDERS_FILE, "r") as f:
            reminders = json.load(f)
            if "remembered" in reminders and reminders["remembered"]:
                response = f"You asked me to remember: {reminders['remembered']}"
                speak(response)
                save_conversation("User asked to recall memory", response)
                print(f"You asked me to remember: {reminders['remembered']}")
            else:
                response = "There is nothing I currently remember."
                speak(response)
                save_conversation("User asked to recall memory", response)
                print("Nothing remembered.")
    except FileNotFoundError:
        response = "There is nothing I currently remember."
        speak(response)
        save_conversation("User asked to recall memory", response)
        print("Nothing remembered.")
    except json.JSONDecodeError:
        response = "There was an issue reading the remembered information."
        speak(response)
        save_conversation("User asked to recall memory", response)
        print("Error reading remembered data.")
    except Exception as e:
        response = f"An unexpected error occurred while recalling memory: {e}"
        speak(response)
        save_conversation("User asked to recall memory", f"Error: {e}")
        print(f"Error recalling memory: {e}")

def forget_thing_gui():
    """Resets the remembered information and displays a message."""
    try:
        if os.path.exists(REMINDERS_FILE):
            os.remove(REMINDERS_FILE)
            response = "I have forgotten what I remembered."
            speak(response)
            save_conversation("User asked to forget memory", response)
            print("Forgotten reminder.")
        else:
            response = "There was nothing for me to forget."
            speak(response)
            save_conversation("User asked to forget memory", response)
            print("No reminder to forget.")
    except Exception as e:
        speak(f"Error forgetting reminder: {e}")
        save_conversation("User asked to forget memory", f"Error: {e}")

def load_reminders():
    """Loads and stores the current remembered thing in memory."""
    try:
        if os.path.exists(REMINDERS_FILE):
            with open(REMINDERS_FILE, "r") as f:
                reminders = json.load(f)
                if "remembered" in reminders and reminders["remembered"]:
                    global remembered_item
                    remembered_item = reminders["remembered"]
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        print("Error reading remembered data on startup.")
    except Exception as e:
        print(f"Error loading reminders on startup: {e}")

def save_search_result(search_type, result_data):
    """Saves search results to a JSON file as a list of dictionaries."""
    search_results = []
    try:
        with open(SEARCH_RESULTS_LOG, "r") as f:
            try:
                search_results = json.load(f)
            except json.JSONDecodeError:
                search_results = []
    except FileNotFoundError:
        pass

    search_results.append({"timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           "type": search_type, "result": result_data})

    try:
        with open(SEARCH_RESULTS_LOG, "w") as f:
            json.dump(search_results, f, indent=4)
    except Exception as e:
        print(f"Error saving search result: {e}")

def close_application(query):
    """Closes a specific application."""
    query = query.replace("close", "").strip()
    speak(f"Attempting to close {query}...")
    try:
        # Use taskkill to forcefully close the application by its executable name or window title
        # Try closing by executable name first (more reliable)
        os.system(f"taskkill /im {query}.exe /f")
        # If that fails, try closing by window title (less reliable)
        os.system(f"taskkill /fi \"windowtitle eq {query}\" /f")
        speak(f"{query} might have been closed.")
        save_conversation(f"User asked to close {query}", f"Attempted to close {query}.")
        return True
    except Exception as e:
        speak(f"Sorry, I couldn't close {query}. An error occurred: {e}")
        save_conversation(f"User asked to close {query}", f"Failed to close {query}. Error: {e}")
        return False

def shutdown_system_gui():
    """Initiates system shutdown after confirmation."""
    if messagebox.askyesno("Shutdown", "Are you sure you want to shutdown your system?"):
        speak("Initiating shutdown sequence.")
        try:
            os.system("shutdown /s /f /t 1")
        except Exception as e:
            speak(f"Could not initiate shutdown. Please ensure the script is run with administrator privileges.")
            save_conversation("User asked to shutdown", f"Failed to initiate shutdown. Error: {e}")

def restart_system_gui():
    """Initiates system restart after confirmation."""
    if messagebox.askyesno("Restart", "Are you sure you want to restart your system?"):
        speak("Initiating restart sequence.")
        try:
            os.system("shutdown /r /f /t 1")
        except Exception as e:
            speak(f"Could not initiate restart. Please ensure the script is run with administrator privileges.")
            save_conversation("User asked to restart", f"Failed to initiate restart. Error: {e}")

def process_query(query):
    """Processes the user's query and calls the appropriate functions."""
    if not query:
        return

    if have_a_conversation(query):
        return

    if "time" in query:
        time()
    elif "date" in query:
        date()
    elif "wikipedia" in query:
        query = query.replace("wikipedia", "").strip()
        search_wikipedia(query)
    elif "search on google about" in query:
        query = query.replace("search on google about", "").strip()
        search_on_google(query)
    elif "play music" in query:
        song_name = query.replace("play music", "").strip()
        play_music(song_name)
    elif "open youtube" in query:
        speak_wait()
        wb.open("https://www.youtube.com/")
    elif "open google" in query:
        speak_wait()
        wb.open("google.com")
    elif "open wikipedia" in query:
        speak_wait()
        wb.open("https://www.wikipedia.org")
    elif "open linkedin" in query:
        speak_wait()
        wb.open("https://www.linkedin.com/")
    elif "open github" in query:
        speak_wait()
        wb.open("https://github.com/")
    elif "open stack overflow" in query:
        speak_wait()
        wb.open("https://stackoverflow.com/")
    elif "open coursera" in query:
        speak_wait()
        wb.open("https://www.coursera.org/")
    elif "open google maps" in query or "open maps" in query:
        speak_wait()
        wb.open("https://www.google.com/maps")
    elif "open google news" in query or "open news" in query:
        speak_wait()
        wb.open("https://news.google.com/")
    elif "open google calendar" in query or "open calendar" in query:
        speak_wait()
        wb.open("https://calendar.google.com/")
    elif "open gmail" in query or "open email" in query:
        speak_wait()
        wb.open("https://mail.google.com/")
    elif "change your name" in query:
        set_name()
    elif "screenshot" in query:
        screenshot()
    elif "tell me a joke" in query:
        joke = pyjokes.get_joke()
        speak(joke)
        save_conversation(query, joke)
    elif "shutdown" in query:
        shutdown_system_gui()
    elif "restart" in query:
        restart_system_gui()
    elif "offline" in query or "exit" in query or "quit" in query:
        speak("Going offline. Have a good day!")
        root.destroy()
    elif "show history" in query or "read conversation" in query:
        load_conversation_history_gui()
    elif "remember" in query:
        query = query.replace("remember", "").strip()
        remember_thing_gui(query)
    elif "what did i tell you to remember" in query or "what do you remember" in query:
        recall_thing_gui()
    elif "forget" in query or "reset memory" in query:
        forget_thing_gui()
    elif "close" in query:
        close_application(query)
    else:
        speak("Sorry, I'm not sure how to respond to that.")
        save_conversation(query, "Sorry, I'm not sure how to respond to that.")

def background_listen():
    """Continuously listens for voice commands in the background."""
    while True:
        query = takecommand()
        if query:
            process_query(query)
        # Add a small delay to prevent excessive CPU usage
        import time
        time.sleep(0.1)

if __name__ == "__main__":
    remembered_item = None  # Initialize the remembered item
    root.after(100, wishme) # Wishme after a short delay to allow UI to load

    # Start background listening in a separate thread
    threading.Thread(target=background_listen, daemon=True).start()

    root.mainloop()