def custom_json_dumps(data):
    """Custom JSON dumps function that manually adds commas"""
    if isinstance(data, dict):
        items = []
        for key, value in data.items():
            items.append(f'"{key}": {custom_json_dumps(value)}')
        return '{' + ', '.join(items) + '}'
    elif isinstance(data, list):
        items = [custom_json_dumps(item) for item in data]
        return '[' + ', '.join(items) + ']'
    elif isinstance(data, str):
        return f'"{data}"'
    elif isinstance(data, (int, float, bool)):
        return str(data).lower() if isinstance(data, bool) else str(data)
    elif data is None:
        return 'null'
    else:
        raise TypeError(f"Type {type(data)} not serializable")

# Test the custom function
if __name__ == "__main__":
    test_data = {"test": "value", "another": "field"}
    result = custom_json_dumps(test_data)
    print(f"Custom JSON: {result}")
    
    # Test parsing
    import json
    try:
        parsed = json.loads(result)
        print(f"Parsed: {parsed}")
    except json.JSONDecodeError as e:
        print(f"Parse error: {e}")
