# my_openai.py
import os
import openai
from config import apikey

openai.api_key = apikey

def create_completion(model, prompt, temperature=0.7, max_tokens=256, top_p=1, frequency_penalty=0, presence_penalty=0):
    """
    Creates an OpenAI completion.
    """
    try:
        response = openai.Completion.create(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )
        return response
    except Exception as e:
        print(f"Error in create_completion: {e}")
        return None

if __name__ == '__main__':
    response = create_completion(
        model="gpt-3.5-turbo-instruct",
        prompt="write an email to my boss for resignation?"
    )
    if response and response.choices:
        print(response.choices[0].text)
    else:
        print("Failed to get a response from OpenAI.")