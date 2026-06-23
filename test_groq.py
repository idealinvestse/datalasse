import os
import sys

# Load our config
sys.path.insert(0, '/root/.openclaw/workspace')
import api_config

# Verify key is set
key = os.environ.get("GROQ_API_KEY")
if key:
    print("✓ GROQ_API_KEY is set")
    # Mask the key for display
    masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
    print(f"Key (masked): {masked}")
else:
    print("✗ GROQ_API_KEY not set")
    sys.exit(1)

try:
    from groq import Groq
    print("✓ Groq client imported successfully")
    client = Groq()
    print("✓ Groq client instantiated (no API call made)")
except ImportError as e:
    print(f"✗ Failed to import Groq: {e}")
    sys.exit(1)

try:
    from langchain_groq import ChatGroq
    print("✓ LangChain Groq imported successfully")
    # Optionally instantiate but might require key; we'll skip
except ImportError as e:
    print(f"✗ Failed to import langchain_groq: {e}")
    sys.exit(1)

print("\n🎉 Groq integration is ready!")
