import sys
import os
sys.path.insert(0, '/root/.openclaw/workspace')
import api_config  # sets GROQ_API_KEY

from groq import Groq

client = Groq()

try:
    # Try with reasoning effort medium
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Hello! Confirm you are using GPT-OSS 120b with medium reasoning."}],
        reasoning_effort="medium"
    )
    content = response.choices[0].message.content if response.choices else "(no content)"
    print("✅ GPT-OSS 120b (medium) response:")
    print(content)
except Exception as e:
    print("❌ First attempt with reasoning_effort failed:", e)
    # Try without reasoning_effort (some versions ignore)
    try:
        response2 = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Hello! Confirm you are using GPT-OSS 120b."}]
        )
        content2 = response2.choices[0].message.content if response2.choices else "(no content)"
        print("✅ GPT-OSS 120b (default) response:")
        print(content2)
    except Exception as e2:
        print("❌ Second attempt failed:", e2)
        # Try a different model to ensure connectivity
        try:
            response3 = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Confirm Groq API is working with llama-3.3-70b-versatile."}]
            )
            content3 = response3.choices[0].message.content if response3.choices else "(no content)"
            print("✅ Fallback test with llama-3.3-70b-vertible:")
            print(content3)
        except Exception as e3:
            print("❌ Even fallback failed:", e3)