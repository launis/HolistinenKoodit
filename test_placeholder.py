import sys
import os
sys.path.append(os.path.join(os.getcwd(), "src"))
from orchestrator import Orchestrator

# Mock Context
class MockContext:
    def __init__(self):
        self.files = [
            ("test.pdf", "This is the content of test.pdf with \"quotes\" and \n newlines."),
            ("other.txt", "Simple content")
        ]

# Mock Orchestrator (partial)
class MockOrchestrator(Orchestrator):
    def __init__(self):
        pass

orch = MockOrchestrator()
context = MockContext()

# Test case 1: Simple replacement
json_input = '{"file": "{{FILE: test.pdf}}"}'
expected_content = "This is the content of test.pdf with \\\"quotes\\\" and \\n newlines."
print(f"Input: {json_input}")
result = orch._inject_file_content(json_input, context)
print(f"Result: {result}")

if expected_content in result:
    print("SUCCESS: Content injected and escaped.")
else:
    print("FAILURE: Content mismatch.")

# Test case 2: Multiple files
json_input_2 = '{"f1": "{{FILE: test.pdf}}", "f2": "{{FILE: other.txt}}"}'
result_2 = orch._inject_file_content(json_input_2, context)
print(f"Result 2: {result_2}")

if "Simple content" in result_2 and "quotes" in result_2:
    print("SUCCESS: Multiple files injected.")
else:
    print("FAILURE: Multiple files mismatch.")
