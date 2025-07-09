import speech_recognition as sr
import win32com.client
from pygame.transform import threshold

speaker=win32com.client.Dispatch("SAPI.SpVoice")

def takeCommand():
    r=sr.Recognizer()
    with sr.Microphone()as source:
        r.pause_threshold= 1
        audio=r.listen(source)
        query=r.recognize_google(audio,language="en-in")
        print(f"user said:{query}")
        return



if __name__=='__main__':
    while 1:
     print("enter the words")
     s=input()
     speaker.Speak(s)
     text=takeCommand()
     speaker(s)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
