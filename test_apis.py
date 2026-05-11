"""
Test script to verify API keys are working
"""
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

print("=" * 50)
print("API KEY VERIFICATION TEST")
print("=" * 50)

# Check if keys are loaded
openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

print(f"\n✓ OpenAI key loaded: {openai_key[:25]}..." if openai_key else "\n✗ OpenAI key NOT found")
print(f"✓ Anthropic key loaded: {anthropic_key[:25]}..." if anthropic_key else "✗ Anthropic key NOT found")

# Test OpenAI
print("\n" + "-" * 50)
print("Testing OpenAI API...")
print("-" * 50)

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    response = llm.invoke([HumanMessage(content="Say 'Hello from OpenAI!' and nothing else.")])
    print(f"✅ OpenAI Response: {response.content}")
except Exception as e:
    print(f"❌ OpenAI Error: {e}")

# Test Anthropic
print("\n" + "-" * 50)
print("Testing Anthropic API...")
print("-" * 50)

try:
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage
    
    llm = ChatAnthropic(model="claude-haiku-4-5", temperature=0)
    response = llm.invoke([HumanMessage(content="Say 'Hello from Claude!' and nothing else.")])
    print(f"✅ Anthropic Response: {response.content}")
except Exception as e:
    print(f"❌ Anthropic Error: {e}")

print("\n" + "=" * 50)
print("TEST COMPLETE")
print("=" * 50)