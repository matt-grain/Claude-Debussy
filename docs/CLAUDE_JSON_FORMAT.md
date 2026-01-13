# Claude CLI Stream-JSON Output Format

When using `claude -p --output-format stream-json --verbose`, Claude CLI outputs newline-delimited JSON events.

## Event Types

### 1. System Init Event
First event after hook responses, contains session metadata:
```json
{
  "type": "system",
  "subtype": "init",
  "cwd": "c:\\Projects\\...",
  "session_id": "uuid",
  "tools": ["Task", "Bash", "Read", ...],
  "model": "claude-opus-4-5-20251101",
  "context_window": 200000
}
```

### 2. Assistant Message Event
Contains Claude's response and usage data:
```json
{
  "type": "assistant",
  "message": {
    "model": "claude-opus-4-5-20251101",
    "content": [{"type": "text", "text": "..."}],
    "usage": {
      "input_tokens": 2,
      "output_tokens": 9,
      "cache_creation_input_tokens": 7924,
      "cache_read_input_tokens": 13368,
      "cache_creation": {
        "ephemeral_5m_input_tokens": 7924,
        "ephemeral_1h_input_tokens": 0
      },
      "service_tier": "standard"
    }
  },
  "session_id": "uuid"
}
```

### 3. Content Block Delta (Streaming)
Real-time text chunks:
```json
{
  "type": "content_block_delta",
  "delta": {
    "type": "text_delta",
    "text": "chunk of text"
  }
}
```

### 4. User Event (Tool Results)
Contains tool execution results:
```json
{
  "type": "user",
  "message": {
    "content": [
      {
        "type": "tool_result",
        "tool_use_id": "...",
        "is_error": false,
        "content": "..."
      }
    ]
  }
}
```

### 5. Result Event (Final)
Last event with session summary:
```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "duration_ms": 3952,
  "duration_api_ms": 12932,
  "num_turns": 1,
  "result": "final text response",
  "session_id": "uuid",
  "total_cost_usd": 0.10457895,
  "usage": {
    "input_tokens": 2,
    "output_tokens": 9,
    "cache_creation_input_tokens": 7924,
    "cache_read_input_tokens": 13368,
    "server_tool_use": {
      "web_search_requests": 0,
      "web_fetch_requests": 0
    },
    "service_tier": "standard"
  },
  "modelUsage": {
    "claude-opus-4-5-20251101": {
      "inputTokens": 8,
      "outputTokens": 269,
      "cacheReadInputTokens": 23048,
      "cacheCreationInputTokens": 13507,
      "contextWindow": 200000,
      "costUSD": 0.10270775
    }
  }
}
```

## Key Fields for Token Tracking

- **`result.usage.input_tokens`**: Total input tokens for the session
- **`result.usage.output_tokens`**: Total output tokens for the session
- **`result.usage.cache_read_input_tokens`**: Tokens read from cache (cheaper)
- **`result.usage.cache_creation_input_tokens`**: Tokens written to cache
- **`result.total_cost_usd`**: Total cost in USD
- **`result.modelUsage[model].contextWindow`**: Context window size (default 200000)

## Context Window Calculation

To calculate context usage percentage:
```python
# Current context = input + cache reads (what's "in memory" for this session)
current_context = input_tokens + cache_read_input_tokens + cache_creation_input_tokens
context_pct = (current_context / context_window) * 100
```

Note: The actual context usage per turn depends on conversation history.
The `result` event gives cumulative totals for the session.
