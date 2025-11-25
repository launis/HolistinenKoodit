
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.orchestrator import Orchestrator

class MockLLM:
    def generate_response(self, prompt, model):
        return ""

class MockDataHandler:
    pass

def test_cleaner():
    orch = Orchestrator(MockLLM(), MockDataHandler())
    
    test_cases = [
        (
            '✅ Vaihe 1 (Valmis)\n```json\n{"key": "value"}\n```',
            '{"key": "value"}'
        ),
        (
            'Here is the JSON: {"foo": "bar"} Hope this helps!',
            '{"foo": "bar"}'
        ),
        (
            '{"pure": "json"}',
            '{"pure": "json"}'
        ),
        (
            'No json here',
            'No json here'
        )
    ]
    
    print("Running JSON Cleaner Tests...")
    for i, (input_text, expected) in enumerate(test_cases):
        result = orch._clean_json_response(input_text)
        if result == expected:
            print(f"✅ Test {i+1} Passed")
        else:
            print(f"❌ Test {i+1} Failed")
            print(f"   Input: {repr(input_text)}")
            print(f"   Expected: {repr(expected)}")
            print(f"   Got: {repr(result)}")

if __name__ == "__main__":
    test_cleaner()
