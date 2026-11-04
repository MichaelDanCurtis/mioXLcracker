import sys

try:
    with open('output_unlock.txt', 'rb') as f:
        data = f.read()
        print(data.decode('utf-8', errors='replace'))
except Exception as e:
    print(f"Error: {e}")
