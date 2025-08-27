# Test different ways of outputting strings
test_string = '{"message": "test", "value": 123}'

print("Method 1 - Direct print:")
print(test_string)

print("\nMethod 2 - repr:")
print(repr(test_string))

print("\nMethod 3 - Bytes conversion:")
print(test_string.encode('utf-8'))

print("\nMethod 4 - Manual construction:")
manual_string = '{"message": "test"' + ', ' + '"value": 123}'
print(manual_string)
print(repr(manual_string))

print("\nMethod 5 - String replacement:")
replaced_string = test_string.replace('", "', '", "')
print(replaced_string)
print(repr(replaced_string))
