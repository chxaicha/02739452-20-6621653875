import requests

url = "https://www.googleapis.com/books/v1/volumes"

params = {
    "q": "computer",
    "maxResults": 10
}

response = requests.get(url, params=params)

print("Status:", response.status_code)

data = response.json()

for book in data.get("items", []):
    info = book.get("volumeInfo", {})
    print(info.get("title"))
