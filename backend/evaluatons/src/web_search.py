import requests
import os

SERPER_API_KEY = os.getenv("SERPER_KEY")

def duckduckgo_search(query, max_results=5):
    url = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }

    payload = { "q": query, "num": max_results }

    try:
        r = requests.post(url, json=payload, headers=headers)
        data = r.json()

        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title"),
                "body": item.get("snippet"),
                "href": item.get("link")
            })
            if len(results) >= max_results:
                break
        return results

    except Exception as e:
        print("Web Search Error:", e)
        return []
