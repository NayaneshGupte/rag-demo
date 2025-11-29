# LLM Provider Quick Start Guide

## Installation & Setup

### 1. Clone/Update Repository
```bash
cd /Users/nayaneshgupte/AI\ Projects/RAG\ Demo
git fetch origin
git checkout feature-reafactor  # or merge into your branch
```

### 2. Configure Environment
```bash
# Copy the example configuration
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

### 3. Set Your LLM Providers
```bash
# Option A: Gemini as primary (recommended for cost)
LLM_PRIMARY_PROVIDER=gemini
LLM_FALLBACK_PROVIDERS=claude
GOOGLE_API_KEY=your-key
ANTHROPIC_API_KEY=your-key

# Option B: Claude as primary (recommended for quality)
LLM_PRIMARY_PROVIDER=claude
LLM_FALLBACK_PROVIDERS=gemini
ANTHROPIC_API_KEY=your-key
GOOGLE_API_KEY=your-key
```

## Usage Examples

### Example 1: Basic Usage (No Code Changes Needed!)

```python
from app.services.agent_service import AgentService

# Automatic fallback happens behind the scenes
agent = AgentService()
agent.process_emails()

# Check which provider is currently active
status = agent.llm_factory.get_provider_status()
print(f"Using: {status['current_provider']}")
```

### Example 2: Check Provider Status

```python
from app.services.agent_service import AgentService

agent = AgentService()
status = agent.llm_factory.get_provider_status()

print("Provider Status:")
print(f"  Current: {status['current_provider']}")
print(f"  Primary: {status['primary']['name']} "
      f"({'available' if status['primary']['available'] else 'unavailable'})")

for fallback in status['fallbacks']:
    available = 'available' if fallback['available'] else 'unavailable'
    print(f"  Fallback: {fallback['name']} ({available})")
```

### Example 3: Direct Factory Usage

```python
from app.services.llm_providers import LLMFactory
from app.config import Config

# Create factory with configured providers
factory = LLMFactory(
    primary_provider=Config.LLM_PRIMARY_PROVIDER,
    fallback_providers=Config.LLM_FALLBACK_PROVIDERS
)

# Generate content with automatic retry and fallback
response = factory.generate_content(
    prompt="Classify this email as urgent or not: Hello there!",
    temperature=0.0,
    max_tokens=100,
    max_retries=5,
    retry_delay=5
)

print(response.text)
print(f"Used model: {response.model_name}")
```

### Example 4: Using a Specific Provider

```python
from app.services.llm_providers import GeminiProvider, ClaudeProvider

# Use Gemini directly
gemini = GeminiProvider(model_name="models/gemini-2.0-flash")
if gemini.is_available():
    response = gemini.generate_content("Hello!")
    print(response.text)

# Use Claude directly
claude = ClaudeProvider(model_name="claude-3-sonnet-20240229")
if claude.is_available():
    response = claude.generate_content("Hello!")
    print(response.text)
```

### Example 5: Custom Provider

```python
from app.services.llm_providers.base import LLMProvider, LLMResponse
import os

class MyLLMProvider(LLMProvider):
    """Custom LLM provider using your own API."""
    
    def __init__(self, model_name: str = "my-model", api_key: str = None):
        super().__init__(model_name)
        self.api_key = api_key or os.getenv("MY_LLM_API_KEY")
        self.client = None
        
        if self.validate_credentials():
            self._initialize_client()
    
    def validate_credentials(self) -> bool:
        return bool(self.api_key)
    
    def _initialize_client(self):
        # Initialize your API client
        from my_api import Client  # Your custom API client
        self.client = Client(api_key=self.api_key)
    
    def is_available(self) -> bool:
        if not self.validate_credentials():
            return False
        if self.client is None:
            try:
                self._initialize_client()
            except Exception:
                return False
        return self.client is not None
    
    def generate_content(self, prompt: str, temperature: float = 0.0, 
                         max_tokens: int = 1024) -> LLMResponse:
        if not self.is_available():
            raise Exception("MyLLMProvider not available")
        
        # Call your API
        response_text = self.client.generate(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return LLMResponse(text=response_text, model_name=self.model_name)


# Register your provider
from app.services.llm_providers.factory import LLMFactory
LLMFactory.PROVIDER_REGISTRY["my_llm"] = MyLLMProvider

# Use in .env
# LLM_PRIMARY_PROVIDER=my_llm
# MY_LLM_API_KEY=your-key
```

### Example 6: Monitor Provider Switching

```python
from app.services.llm_providers import LLMFactory
from app.config import Config
import logging

# Enable debug logging to see provider switches
logging.basicConfig(level=logging.DEBUG)

factory = LLMFactory(
    primary_provider="gemini",
    fallback_providers=["claude"]
)

# This will show logs when switching providers
try:
    response = factory.generate_content(
        prompt="Hello",
        max_retries=10,  # More retries to see backoff behavior
        retry_delay=1
    )
    print(response.text)
except Exception as e:
    print(f"All providers failed: {e}")
```

### Example 7: Handle Provider Errors

```python
from app.services.llm_providers import LLMFactory

factory = LLMFactory(
    primary_provider="gemini",
    fallback_providers=["claude"]
)

try:
    response = factory.generate_content(
        prompt="Your prompt here",
        temperature=0.0,
        max_tokens=1024
    )
    print("Success:", response.text)
except Exception as e:
    print(f"Error: {e}")
    
    # Get status to understand what happened
    status = factory.get_provider_status()
    print(f"Current provider: {status['current_provider']}")
    print(f"Available providers: {status}")
```

### Example 8: Configuration Variations

```bash
# High Cost / High Quality
LLM_PRIMARY_PROVIDER=claude
LLM_FALLBACK_PROVIDERS=gemini
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=2048

# Low Cost / Fast
LLM_PRIMARY_PROVIDER=gemini
LLM_FALLBACK_PROVIDERS=claude
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=512

# High Availability (Many Retries)
LLM_PRIMARY_PROVIDER=gemini
LLM_FALLBACK_PROVIDERS=claude
LLM_RETRY_MAX_ATTEMPTS=10
LLM_RETRY_DELAY_SECONDS=10

# Creative Responses
LLM_PRIMARY_PROVIDER=claude
LLM_FALLBACK_PROVIDERS=gemini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024
```

## Common Tasks

### Task: Switch Primary Provider

**Before (Old Code - Not Possible):**
- Had to modify code and redeploy

**After (New Code - Just Change .env):**
```bash
# Edit .env
LLM_PRIMARY_PROVIDER=claude  # Was: gemini
LLM_FALLBACK_PROVIDERS=gemini  # Was: claude

# Restart application - no code changes needed!
python run.py
```

### Task: Add a Fallback Provider

```bash
# Edit .env
LLM_FALLBACK_PROVIDERS=claude,openai_provider,custom_llm

# If you're using OpenAI or custom provider, add their API key:
OPENAI_API_KEY=...
CUSTOM_LLM_KEY=...
```

### Task: Increase Retry Attempts

```bash
# Edit .env
LLM_RETRY_MAX_ATTEMPTS=10  # Was: 5
LLM_RETRY_DELAY_SECONDS=10  # Was: 5
```

### Task: Test Provider Availability

```python
from app.services.llm_providers import GeminiProvider, ClaudeProvider

providers = {
    "Gemini": GeminiProvider(),
    "Claude": ClaudeProvider()
}

for name, provider in providers.items():
    available = "✓ Available" if provider.is_available() else "✗ Not Available"
    print(f"{name}: {available}")
```

### Task: Get Real-Time Provider Status

```python
from app.services.agent_service import AgentService
import json

agent = AgentService()
status = agent.llm_factory.get_provider_status()
print(json.dumps(status, indent=2))
```

## Troubleshooting

### Issue: "No LLM provider available"

**Cause:** All providers failed to initialize

**Solution:**
```python
from app.services.llm_providers import GeminiProvider, ClaudeProvider

# Check which providers are available
gemini = GeminiProvider()
claude = ClaudeProvider()

print(f"Gemini available: {gemini.is_available()}")
print(f"Claude available: {claude.is_available()}")

# Check your .env file
import os
print(f"GOOGLE_API_KEY: {os.getenv('GOOGLE_API_KEY')[:10]}...")
print(f"ANTHROPIC_API_KEY: {os.getenv('ANTHROPIC_API_KEY')[:10]}...")
```

### Issue: Frequent Fallback Switching

**Cause:** Primary provider hitting rate limits

**Solution:**
```bash
# Increase retry parameters in .env
LLM_RETRY_MAX_ATTEMPTS=10
LLM_RETRY_DELAY_SECONDS=10

# Or use Claude (higher limits) as primary
LLM_PRIMARY_PROVIDER=claude
LLM_FALLBACK_PROVIDERS=gemini
```

### Issue: Responses Becoming Less Creative

**Cause:** Temperature set to 0 (deterministic)

**Solution:**
```bash
# Increase temperature for more variety (0.0-1.0)
LLM_TEMPERATURE=0.7

# Or adjust in code
response = factory.generate_content(
    prompt="...",
    temperature=0.7  # More creative
)
```

### Issue: Responses Too Long or Too Short

**Cause:** max_tokens setting

**Solution:**
```bash
# Adjust in .env
LLM_MAX_TOKENS=2048  # Longer responses

# Or in code
response = factory.generate_content(
    prompt="...",
    max_tokens=512  # Shorter responses
)
```

## Best Practices

1. **Use Environment Variables**
   - Never hardcode API keys
   - Use `.env` for all configuration
   - Copy `.env.example` as template

2. **Monitor Provider Status**
   - Check status regularly
   - Set up alerts for fallback usage
   - Log provider switches

3. **Configure Redundancy**
   - Always have at least 1 fallback provider
   - Test both primary and fallback regularly
   - Keep API keys for multiple providers

4. **Optimize Costs**
   - Use Gemini as primary (cheaper)
   - Use Claude as fallback (more expensive, better quality)
   - Monitor actual usage and costs

5. **Handle Errors Gracefully**
   - Don't rely on always getting responses
   - Implement retry logic in your application
   - Have fallback strategies

## Performance Tips

### For Low Latency
```bash
LLM_MAX_TOKENS=512
LLM_TEMPERATURE=0.0
LLM_PRIMARY_PROVIDER=gemini  # Typically faster
```

### For High Quality
```bash
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.3
LLM_PRIMARY_PROVIDER=claude
```

### For Cost Optimization
```bash
LLM_MAX_TOKENS=512
LLM_PRIMARY_PROVIDER=gemini
LLM_FALLBACK_PROVIDERS=claude
```

### For Reliability
```bash
LLM_RETRY_MAX_ATTEMPTS=10
LLM_RETRY_DELAY_SECONDS=10
LLM_FALLBACK_PROVIDERS=claude,openai_provider,backup_provider
```

## File Reference

- **LLM_CONFIGURATION.md** - Complete setup and configuration guide
- **REFACTORING_SUMMARY.md** - Architecture and migration details  
- **LLM_ARCHITECTURE.md** - Detailed diagrams and sequences
- **app/services/llm_providers/base.py** - LLMProvider interface
- **app/services/llm_providers/factory.py** - Factory implementation
- **app/config/__init__.py** - Configuration class

## Support & Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see all LLM provider operations
```

### Check Imports
```bash
python3 -c "from app.services.llm_providers import LLMFactory; print('✓ Imports OK')"
```

### Validate Configuration
```bash
python3 << 'EOF'
from app.config import Config
print(f"Primary: {Config.LLM_PRIMARY_PROVIDER}")
print(f"Fallbacks: {Config.LLM_FALLBACK_PROVIDERS}")
print(f"Temperature: {Config.LLM_TEMPERATURE}")
print(f"Max tokens: {Config.LLM_MAX_TOKENS}")
EOF
```
