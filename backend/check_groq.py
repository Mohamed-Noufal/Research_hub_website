import os
import sys
from dotenv import load_dotenv

# Explicitly load .env
load_dotenv()

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

def check_groq():
    print("🔍 Checking Groq Configuration...")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY is NOT set in environment variables.")
        return
        
    print(f"✅ GROQ_API_KEY found: {api_key[:8]}...{api_key[-4:]}")
    
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        print("✅ Client initialized")
        
        print("🧪 Testing simple completion...")
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print(f"✅ Response received: {completion.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Groq API Error: {e}")

if __name__ == "__main__":
    check_groq()
