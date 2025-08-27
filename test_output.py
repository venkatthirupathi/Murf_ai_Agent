import json

# Test with different approaches
test_data = {"test": "value", "another": "field"}

# Method 1: Direct print
print("Method 1 - Direct print:")
print(json.dumps(test_data))

# Method 2: repr
print("\nMethod 2 - repr:")
print(repr(json.dumps(test_data)))

# Method 3: Write to file
print("\nMethod 3 - Write to file:")
with open("test_output.json", "w") as f:
    json.dump(test_data, f)

# Read back from file
with open("test_output.json", "r") as f:
    content = f.read()
    print(f"File content: {repr(content)}")

# Method 4: Manual string construction
print("\nMethod 4 - Manual string:")
manual_json = '{"test": "value", "another": "field"}'
print(f"Manual: {repr(manual_json)}")
