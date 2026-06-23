import sys
import os
sys.path.insert(0, '/root/.openclaw/workspace')
import api_config  # sets GROQ_API_KEY

from groq import Groq

client = Groq()

try:
    # Try with reasoning effort medium
    response = client.chat.completions.create(
        model="gpt-oss-120b",
        messages=[{"role": "user", "content": "Hello! Confirm you are using GPT-OSS 120b with medium reasoning."}],
        # reasoning_effort may be supported; try as extra body
        extra_body={"reasoning_effort": "medium"}
    )
    content = response.choices[0].message.content if response.choices else "(no content)"
    print("✅ GPT-OSS 120b (medium) response:")
    print(content)
except Exception as e:
    print("❌ First attempt failed:", e)
    # Try without extra_body
    try:
        response2 = client.chat.completions.create(
            model="gpt-oss-120b",
            messages=[{"role": "user", "content": "Hello! Confirm you are using GPT-OSS 120b."}]
        )
        content2 = response2.choices[0].message.content if response2.choices else "(no content)"
        print("✅ GPT-OSS 120b (default) response:")
        print(content2)
    except Exception as e2:
        print("❌ Second attempt failed:", e2)