import os
import google.generativeai as genai

from dotenv import load_dotenv

def google_api_setup() -> str | None:
    '''
    Loads GOOGLE_API_KEY from secrets.env and configures the google-generativeai client.
    Returns the key string, or None if not found.
    '''
    load_dotenv(dotenv_path="secrets.env")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if google_api_key:
        os.environ["GOOGLE_API_KEY"] = google_api_key
        genai.configure(api_key=google_api_key)
        print("Google API Key configured.")
        return google_api_key
    else:
        print("ERROR: No Google API Key found in secrets.env.")
        return None
