import requests
import json

def test_sse_endpoint():
    print("Testing SSE endpoint...")

    try:
        # Make request to SSE endpoint
        response = requests.get('http://localhost:8000/api/scan/stream/8', stream=True)

        print(f"Response status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        # Read a few lines to see if we get any data
        line_count = 0
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                print(f"Line {line_count}: {decoded_line}")
                line_count += 1

                # Stop after 10 lines to avoid overwhelming output
                if line_count >= 10:
                    break

    except Exception as e:
        print(f"Error testing SSE endpoint: {e}")

if __name__ == "__main__":
    test_sse_endpoint()