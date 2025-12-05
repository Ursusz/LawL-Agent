import unittest
import sys
import os
from collections import Counter

# Add src to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utilities.gemini_utils import get_random_gemini_model, GEMINI_MODELS

class TestGeminiUtils(unittest.TestCase):
    def test_get_random_gemini_model_returns_valid_model(self):
        """Test that the function returns a model from the defined list."""
        model = get_random_gemini_model()
        self.assertIn(model, GEMINI_MODELS)

    def test_distribution(self):
        """Test that the distribution of models roughly matches the expected weights."""
        iterations = 10000
        counts = Counter()
        
        for _ in range(iterations):
            model = get_random_gemini_model()
            counts[model] += 1
            
        # Calculate percentages
        percentages = {model: (count / iterations) * 100 for model, count in counts.items()}
        
        # 2.0 models should be around 33.33%
        # Others should be around 11.11%
        # We allow a margin of error (e.g., +/- 2%)
        
        margin = 2.0
        
        for model in GEMINI_MODELS:
            if 'gemini-2.0' in model:
                expected = 33.33
            else:
                expected = 11.11
                
            self.assertTrue(
                expected - margin <= percentages[model] <= expected + margin,
                f"Model {model} percentage {percentages[model]:.2f}% is not within margin of {expected}%"
            )

if __name__ == '__main__':
    unittest.main()
