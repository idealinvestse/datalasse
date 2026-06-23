# Quick verification that Groq API is reachable and the model works.
import sys
import os

# Ensure workspace path is in import path for api_config.
sys.path.insert(0, '/root/.openclaw/workspace')

# Load the API key configuration (sets GROQ_API_KEY env var).
import api_config  # noqa: F401

from groq import Groq

client = Groq()

try:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Hello! Please respond with a short confirmation that you are using Groq."}],
    )
    # Extract content safely.
    content = response.choices[0].message.content if response.choices else "(no content)"
    print("✅ Groq API response:")
    print(content)
except Exception as e:
    print("❌ Groq API request failed:")
    print(e)
