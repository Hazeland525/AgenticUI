from maps_service import MapsService # Replace 'your_filename' with the name of your python file
import logging

# This lets you see the actual errors if it fails
logging.basicConfig(level=logging.INFO)

def run_test():
    service = MapsService()
    print("Searching for coffee...")
    results = service.search_places("Best coffee in San Francisco")

    if results:
        print(f"\nSuccess! Found {len(results)} places.")
        for p in results[:3]:
            print(f"- {p['name']} ({p['address']})")
    else:
        print("\nStill no results. Look at the logs above for the error body.")

if __name__ == "__main__":
    run_test()