import os
import time

from dotenv import load_dotenv
from google import genai


load_dotenv()


class LLMService:
    """
    Gemini LLM service with retry and fallback support.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing in .env file."
            )

        self.client = genai.Client(
            api_key=self.api_key
        )

        self.primary_model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash"
        )

        self.fallback_model = os.getenv(
            "GEMINI_FALLBACK_MODEL",
            "gemini-2.5-flash-lite"
        )

    def _generate(self, prompt, model):
        """
        Make one Gemini API request.
        """

        response = self.client.models.generate_content(
            model=model,
            contents=prompt
        )

        if response and response.text:
            return response.text.strip()

        raise RuntimeError(
            "Gemini returned an empty response."
        )

    def generate_response(self, prompt):
        """
        Generate response using primary model.
        If temporary 503/high-demand error occurs,
        retry and then use fallback model.
        """

        if not prompt or not prompt.strip():
            return "Please enter a valid question."

        # --------------------------------------------------
        # PRIMARY MODEL
        # --------------------------------------------------

        for attempt in range(3):

            try:

                print(
                    f"Gemini primary attempt "
                    f"{attempt + 1}/3: {self.primary_model}"
                )

                return self._generate(
                    prompt,
                    self.primary_model
                )

            except Exception as error:

                error_text = str(error)

                print(
                    f"Primary Gemini error: {error_text}"
                )

                # Retry only temporary availability errors
                temporary_error = (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "high demand" in error_text
                    or "temporarily" in error_text.lower()
                )

                if not temporary_error:
                    break

                # Exponential backoff:
                # 2 sec → 4 sec → 8 sec
                if attempt < 2:
                    wait_time = 2 ** (attempt + 1)

                    print(
                        f"Retrying in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

        # --------------------------------------------------
        # FALLBACK MODEL
        # --------------------------------------------------

        print(
            f"Trying fallback model: "
            f"{self.fallback_model}"
        )

        try:

            return self._generate(
                prompt,
                self.fallback_model
            )

        except Exception as fallback_error:

            print(
                f"Fallback Gemini error: "
                f"{fallback_error}"
            )

            raise RuntimeError(
                "Gemini is temporarily unavailable. "
                "Please try again in a few moments."
            )


# ------------------------------------------------------
# SINGLE SERVICE INSTANCE
# ------------------------------------------------------

llm_service = LLMService()