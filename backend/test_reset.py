#!/usr/bin/env python3
"""
Quick test to verify script can run and produce output
"""
import sys
import os

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

print("=" * 80, flush=True)
print("TEST SCRIPT STARTING", flush=True)
print("=" * 80, flush=True)

try:
    print("Step 1: Checking uploads directory...", flush=True)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(base_dir, "uploads", "pdfs")
    
    if os.path.exists(uploads_dir):
        files = [f for f in os.listdir(uploads_dir) if f.endswith(".pdf")]
        print(f"✓ Found {len(files)} PDF files", flush=True)
        for f in files:
            print(f"  - {f}", flush=True)
    else:
        print(f"✗ Directory not found: {uploads_dir}", flush=True)
    
    print("\nStep 2: Loading settings...", flush=True)
    sys.path.append(base_dir)
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(base_dir), '.env'))
    
    from app.core.config import settings
    print(f"✓ DATABASE_URL loaded: {settings.DATABASE_URL[:30]}...", flush=True)
    
    print("\nStep 3: Test complete!", flush=True)
    print("=" * 80, flush=True)
    
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
