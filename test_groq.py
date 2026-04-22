import os
from dotenv import load_dotenv

# We can use the official groq package if installed, 
# or the openai package pointing to Groq's endpoint.
try:
    from groq import Groq
    USE_GROQ_PKG = True
except ImportError:
    try:
        from openai import OpenAI
        USE_GROQ_PKG = False
    except ImportError:
        print("Please install the groq package: pip install groq")
        exit(1)

def main():
    load_dotenv()
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        print("Error: Please set your GROQ_API_KEY in the .env file.")
        return

    model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    
    print(f"Testing connection to Groq API using model: {model}...")
    
    try:
        if USE_GROQ_PKG:
            print("Using 'groq' Python package.")
            client = Groq(api_key=api_key)
        else:
            print("Using 'openai' Python package with Groq base URL.")
            client = OpenAI(
                api_key=api_key, 
                base_url="https://api.groq.com/openai/v1"
            )

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say 'Connection successful!' and give me a 1 sentence restaurant recommendation for Italian food.",
                }
            ],
            model=model,
        )
        
        print("\n--- Response ---")
        print(chat_completion.choices[0].message.content)
        print("----------------")
        
    except Exception as e:
        print(f"\nConnection failed: {e}")

if __name__ == "__main__":
    main()
