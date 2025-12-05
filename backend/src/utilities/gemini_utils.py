import random

GEMINI_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-2.5-flash-lite-preview'
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
