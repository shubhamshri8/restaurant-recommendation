import os
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from src.phase2.api.app import app

def test_api():
    # Load .env to ensure Groq config is available
    load_dotenv()
    
    print(f"Using LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
    print(f"Using GROQ_MODEL: {os.getenv('GROQ_MODEL')}")
    print("-" * 50)
    
    client = TestClient(app)
    
    # Test 1: Italian food in Indiranagar
    req1 = {
        "area": "Indiranagar",
        "budget_inr": 1500,
        "cuisine": "Italian",
        "min_rating": 4.0,
        "notes": "Looking for a cozy romantic dinner",
        "top_n": 3
    }
    
    print("\nTest 1: Italian in Indiranagar")
    resp1 = client.post("/recommendations", json=req1)
    data1 = resp1.json()
    assert resp1.status_code == 200
    print(f"Status Code: {resp1.status_code}")
    print(f"Results Found: {len(data1.get('results', []))}")
    if data1.get('results'):
        print(f"Top Pick: {data1['results'][0]['name']}")
        print(f"Reason: {data1['results'][0].get('reason')}")
        print(f"Match Signals: {data1['results'][0].get('match_signals')}")


    # Test 2: Chinese food in Koramangala
    req2 = {
        "area": "Koramangala 5th Block",
        "budget_inr": 800,
        "cuisine": "Chinese",
        "min_rating": 3.8,
        "notes": "Spicy food, good for groups",
        "top_n": 2
    }
    
    print("\nTest 2: Chinese in Koramangala")
    resp2 = client.post("/recommendations", json=req2)
    data2 = resp2.json()
    assert resp2.status_code == 200
    print(f"Status Code: {resp2.status_code}")
    print(f"Results Found: {len(data2.get('results', []))}")
    if data2.get('results'):
        print(f"Top Pick: {data2['results'][0]['name']}")
        print(f"Reason: {data2['results'][0].get('reason')}")
        
    # Test 3: North Indian in Whitefield
    req3 = {
        "area": "Whitefield",
        "budget_inr": 1200,
        "cuisine": "North Indian",
        "min_rating": 4.1,
        "notes": "Butter chicken craving",
        "top_n": 1
    }
    
    print("\nTest 3: North Indian in Whitefield")
    resp3 = client.post("/recommendations", json=req3)
    data3 = resp3.json()
    assert resp3.status_code == 200
    print(f"Status Code: {resp3.status_code}")
    print(f"Results Found: {len(data3.get('results', []))}")
    if data3.get('results'):
        print(f"Top Pick: {data3['results'][0]['name']}")
        print(f"Reason: {data3['results'][0].get('reason')}")

if __name__ == "__main__":
    test_api()
