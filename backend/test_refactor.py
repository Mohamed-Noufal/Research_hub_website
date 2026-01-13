import requests
import time

def check_endpoint(url):
    try:
        response = requests.get(url)
        print(f"✅ {url}: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ {url}: {e}")
        return False

# Wait for reload
print("Waiting for API reload...")
time.sleep(5)

# 1. Check Root Health
check_endpoint("http://localhost:8001/health")

# 2. Check Papers Health (core module)
check_endpoint("http://localhost:8001/api/v1/papers/health")

# 3. Check Categories (core module)
check_endpoint("http://localhost:8001/api/v1/papers/categories")

# 4. Check Embeddings Stats (embeddings module)
check_endpoint("http://localhost:8001/api/v1/papers/embeddings/stats")
