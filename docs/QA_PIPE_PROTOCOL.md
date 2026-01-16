# Q&A Pipe Protocol

This document describes the JSON IPC protocol for integrating Debussy's `plan-from-issues` command with parent processes like Claude Code.

## Overview

When running `plan-from-issues` in a Claude Code conversation, the Q&A gap-filling process needs to route questions through Claude Code's `AskUserQuestion` tool rather than prompting directly in the terminal. The pipe protocol enables this by:

1. Emitting questions as JSON to **stdout**
2. Reading answers as JSON from **stdin**
3. Sending logs to **stderr** to keep stdout clean for IPC

## Enabling Pipe Mode

Set the `DEBUSSY_QA_PIPE` environment variable to `1`:

```bash
export DEBUSSY_QA_PIPE=1
debussy plan-from-issues --repo owner/repo
```

When this variable is set, the Q&A handler switches from interactive terminal prompts to JSON IPC.

## Protocol Messages

### Question Message (stdout)

When Debussy needs user input, it emits a JSON message to stdout:

```json
{
  "type": "question",
  "gap_type": "tech_stack",
  "question": "Which database will this project use?",
  "options": ["PostgreSQL", "MySQL", "SQLite", "MongoDB"],
  "context": "No database mentioned in issues"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Always `"question"` for questions |
| `gap_type` | string | Yes | The category of gap being addressed. Values: `acceptance_criteria`, `tech_stack`, `dependencies`, `validation`, `scope`, `context`, `general` |
| `question` | string | Yes | The question text to present to the user |
| `options` | string[] | No | Suggested answer options (may be empty for open-ended questions) |
| `context` | string | No | Additional context about why this question is being asked |

### Answer Message (stdin)

The parent process should respond with a JSON message on stdin:

```json
{
  "type": "answer",
  "gap_type": "tech_stack",
  "answer": "PostgreSQL"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Always `"answer"` for answers |
| `gap_type` | string | Yes | Should match the question's `gap_type` |
| `answer` | string | Yes | The user's answer. Use `"skip"` to skip the question |

## Special Answers

- `"skip"` (case-insensitive): Skip this question and move to the next one

## Timeout Handling

By default, Debussy waits 30 seconds for each answer. Configure with:

```bash
export DEBUSSY_QA_TIMEOUT=60  # 60 seconds
```

If a timeout occurs, Debussy falls back to terminal prompts for that question.

## Error Handling

If the pipe protocol encounters errors (invalid JSON, missing fields, timeout), Debussy automatically falls back to terminal prompts. Error messages are logged to stderr.

Common errors:
- **Timeout**: No response within timeout period
- **Invalid JSON**: Response is not valid JSON
- **Invalid format**: JSON doesn't match the QAAnswer schema
- **EOF**: stdin closed unexpectedly

## Claude Code Integration Example

When Claude Code runs `plan-from-issues`, it should:

1. Set `DEBUSSY_QA_PIPE=1` in the subprocess environment
2. Capture stdout and parse JSON question messages
3. For each question, use the `AskUserQuestion` tool to get user input
4. Write the JSON answer to the subprocess stdin
5. Repeat until all questions are answered

**Pseudo-code:**

```python
import subprocess
import json

proc = subprocess.Popen(
    ["debussy", "plan-from-issues", "--repo", "owner/repo"],
    env={**os.environ, "DEBUSSY_QA_PIPE": "1"},
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

while True:
    line = proc.stdout.readline()
    if not line:
        break

    try:
        question = json.loads(line)
        if question.get("type") == "question":
            # Route through AskUserQuestion tool
            user_answer = ask_user_question(
                question=question["question"],
                options=question.get("options", []),
                header=question["gap_type"][:12].title(),
            )

            # Send answer back
            answer = {
                "type": "answer",
                "gap_type": question["gap_type"],
                "answer": user_answer,
            }
            proc.stdin.write(json.dumps(answer) + "\n")
            proc.stdin.flush()
    except json.JSONDecodeError:
        # Not a JSON line - might be regular output
        pass
```

## Stdout/Stderr Separation

| Stream | Content |
|--------|---------|
| **stdout** | JSON question messages only |
| **stderr** | Logs, progress messages, errors |

This separation allows the parent process to reliably parse questions from stdout while displaying logs to the user.

## Gap Types

The `gap_type` field categorizes what information is missing:

| Gap Type | Description |
|----------|-------------|
| `acceptance_criteria` | Issue lacks clear definition of "done" |
| `tech_stack` | No technology or framework mentioned |
| `dependencies` | No dependency or blocking information |
| `validation` | No testing or validation requirements |
| `scope` | Issue body is too short or lacks structure |
| `context` | No problem statement or background |
| `general` | Other questions not tied to specific gap |

## Pydantic Models

The protocol uses Pydantic models for validation. See `src/debussy/planners/models.py`:

```python
from debussy.planners.models import QAQuestion, QAAnswer

# Create a question
question = QAQuestion(
    gap_type="tech_stack",
    question="Which database?",
    options=["PostgreSQL", "MySQL"],
    context="No DB mentioned",
)
json_str = question.model_dump_json()

# Parse an answer
answer = QAAnswer.model_validate({
    "type": "answer",
    "gap_type": "tech_stack",
    "answer": "PostgreSQL",
})
```

## Backward Compatibility

- Terminal mode remains the default when `DEBUSSY_QA_PIPE` is not set
- Existing terminal-based workflows continue to work unchanged
- Fallback to terminal mode on any pipe errors ensures reliability
