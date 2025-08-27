import json
import orjson
import sys
import platform

print(f"Python version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"JSON module version: {json.__version__ if hasattr(json, '__version__') else 'unknown'}")

# Test with different JSON libraries
print("\n=== Testing json.dumps ===")
test_data = {"test": "value", "another": "field"}
result_json = json.dumps(test_data)
print(f"json.dumps result: {repr(result_json)}")

print("\n=== Testing orjson.dumps ===")
result_orjson = orjson.dumps(test_data)
print(f"orjson.dumps result: {repr(result_orjson)}")

# Test parsing
print("\n=== Testing JSON parsing ===")
try:
    parsed_json = json.loads(result_json)
    print(f"json.loads result: {parsed_json}")
except json.JSONDecodeError as e:
    print(f"json.loads error: {e}")

try:
    parsed_orjson = orjson.loads(result_orjson)
    print(f"orjson.loads result: {parsed_orjson}")
except Exception as e:
    print(f"orjson.loads error: {e}")

# Test with different data structures
print("\n=== Testing with different data ===")
test_data2 = {"a": 1, "b": 2, "c": 3}
result2 = json.dumps(test_data2)
print(f"json.dumps numbers: {repr(result2)}")

test_data3 = {"list": [1, 2, 3], "dict": {"nested": "value"}}
result3 = json.dumps(test_data3)
print(f"json.dumps nested: {repr(result3)}")
