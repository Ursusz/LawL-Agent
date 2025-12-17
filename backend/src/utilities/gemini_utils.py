import random
import time
import re

GEMINI_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
]

def get_random_gemini_model():
    """
    Returns a random Gemini model from the list, with weighted probabilities.
    Gemini 2.0 models are 3 times more likely to be picked.
    """
    weights = []
    for model in GEMINI_MODELS:
        if 'gemini-2.0' in model:
            weights.append(3)
        else:
            weights.append(1)
    
    return random.choices(GEMINI_MODELS, weights=weights, k=1)[0]


def call_gemini_with_retry(func, max_retries=3, default_delay=65):
    """
    Calls a Gemini API function with retry logic for rate limits and temporary unavailability.
    
    Args:
        func: A callable that executes the Gemini API request.
        max_retries: Maximum number of retry attempts.
        default_delay: Default wait time in seconds if retry delay can't be parsed from error.
        
    Returns:
        The result of func() if successful, or None if max retries reached or non-retriable error occurs.
    """
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_str = str(e)
            print(f"[GEMINI] Error on attempt {attempt + 1}: {error_str}")
            
            # Check if it's a rate limit or availability error
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "UNAVAILABLE" in error_str or "try again" in error_str:
                # Try to parse retry delay from error
                retry_delay = default_delay
                
                # Try to extract retryDelay from error message
                delay_match = re.search(r'Please retry in (\d+(?:\.\d+)?)s', error_str)
                if delay_match:
                    retry_delay = float(delay_match.group(1)) + 1  # Add 1 second buffer
                
                if attempt < max_retries - 1:
                    print(f"[GEMINI] Rate limit hit, waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                else:
                    print(f"[GEMINI] Max retries reached, giving up")
                    return None
            else:
                # For other errors, return None immediately
                print(f"[GEMINI] Non-retriable error, giving up")
                return None
    return None
