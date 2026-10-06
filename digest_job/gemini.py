import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

GEMINI_MODEL = "gemini-3.5-flash-lite"
MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 30


def ask_gemini(prompt, schema=None):
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    config = None
    if schema is not None:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=config,
            )
            return response.text
        except (errors.ServerError, errors.ClientError) as error:
            # 503 = model overloaded, 429 = rate limit: wait and try again
            if error.code not in (429, 503) or attempt == MAX_ATTEMPTS:
                raise
            print(f"Gemini error {error.code}, attempt {attempt}/{MAX_ATTEMPTS}, waiting {RETRY_DELAY_SECONDS}s...")
            time.sleep(RETRY_DELAY_SECONDS)