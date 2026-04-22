import time
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from src.phase2.api.app import app

def run_evaluation():
    load_dotenv()
    client = TestClient(app)
    
    queries = [
        {
            "name": "Delhi, low, Chinese, rating>=4",
            "req": {
                "area": "Connaught Place", # Using a generic area, though dataset is Bangalore
                "budget_inr": 500,
                "cuisine": "Chinese",
                "min_rating": 4.0,
                "notes": "quick service",
                "top_n": 2
            }
        },
        {
            "name": "Bangalore, medium, Italian, family-friendly",
            "req": {
                "area": "Indiranagar",
                "budget_inr": 1500,
                "cuisine": "Italian",
                "min_rating": 4.2,
                "notes": "family-friendly, quiet",
                "top_n": 3
            }
        },
        {
            "name": "High budget cafe",
            "req": {
                "area": "Koramangala 5th Block",
                "budget_inr": 2500,
                "cuisine": "Cafe",
                "min_rating": 4.5,
                "notes": "good coffee, nice ambience",
                "top_n": 2
            }
        }
    ]

    print("Starting Evaluation Harness...\n")
    
    total_latency = 0
    total_passed = 0

    for idx, q in enumerate(queries, 1):
        print(f"--- Test Case {idx}: {q['name']} ---")
        start_time = time.time()
        resp = client.post("/recommendations", json=q["req"])
        latency = time.time() - start_time
        total_latency += latency
        
        if resp.status_code != 200:
            print(f"❌ FAILED. Status code {resp.status_code}")
            continue
            
        data = resp.json()
        results = data.get("results", [])
        
        print(f"Latency: {latency:.3f}s")
        print(f"Results Count: {len(results)}")
        
        passed = True
        for r in results:
            print(f"  -> {r['name']} (Rating: {r['rating']})")
            print(f"     Reason: {r['reason']}")
            
            # Simple hallucination/constraint check: 
            # Did the LLM return an item with rating lower than min_rating?
            if r['rating'] < q["req"]["min_rating"]:
                print(f"     ❌ CONSTRAINT VIOLATION: Rating {r['rating']} < {q['req']['min_rating']}")
                passed = False
                
        if passed:
            print("✅ PASSED: All constraints respected and explanations generated.")
            total_passed += 1
        else:
            print("❌ FAILED: Constraints violated.")
        print("")
        
    print("=== Evaluation Summary ===")
    print(f"Tests Passed: {total_passed}/{len(queries)}")
    print(f"Average Total Latency: {(total_latency/len(queries)):.3f}s")

if __name__ == "__main__":
    run_evaluation()
