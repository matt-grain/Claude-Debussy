# Docker Sandbox for Claude Workers

This document captures the setup and known issues for running Claude Code inside Docker containers (the "devcontainer" sandbox mode).

## Authentication

Claude Code workers inside containers use **OAuth authentication**, not API keys.

The OAuth credentials are stored in `~/.claude/.credentials.json` on the host and must be mounted into the container:

```bash
-v "/path/to/.claude:/home/claude/.claude:rw"
```

**Note:** Mount as `rw` (read-write) because Claude Code writes to:
- `debug/` - debug logs
- `stats-cache.json` - usage stats
- `file-history/` - file access history

## Windows Path Conversion

Git Bash on Windows performs automatic path conversion that breaks Docker commands.

### Problem

```bash
# This fails - Git Bash converts paths
docker run -v "/home/claude/.claude:/home/claude/.claude:rw" ...
# Error: invalid mode: \Program Files\Git\home\claude\.claude;rw
```

### Solutions

1. **Set MSYS_NO_PATHCONV=1** (recommended for subprocess calls):
   ```bash
   MSYS_NO_PATHCONV=1 docker run ...
   ```

2. **Use double-slash prefix** for container paths:
   ```bash
   docker run -v "/mnt/c/Users/me/.claude://home/claude/.claude:rw" ...
   ```

3. **Use WSL docker directly** with proper path format:
   ```bash
   wsl docker run -v "/mnt/c/Users/me/.claude:/home/claude/.claude:rw" ...
   ```

## Known Issues

### 1. Skills Not Available in Container

Claude Code skills like `/remember`, `/debussy-done` are installed on the **host**, not in the container.

**Symptoms:**
```
[ERR] /bin/bash: line 1: /remember: No such file or directory
[ERR] /bin/bash: line 1: /debussy-done: No such file or directory
```

**Cause:** Worker Claude tries to run skill commands as bash commands. Skills use the Skill tool, but the containerized Claude doesn't have access to host skills.

**Workaround:** Disable LTM learnings (`--no-learnings`) when using sandbox mode, or install LTM in the container image.

### 2. uv Command Not Found (FIXED)

**Symptoms:**
```
[ERR] /bin/bash: line 1: uv: command not found
```

**Root Cause (multiple layers):**
1. Docker's `ENV PATH=...` in Dockerfile is overridden at runtime by inherited environment
2. Git Bash's MSYS path conversion mangles `/home/claude/...` to `C:\Program Files\Git\home\claude\...`
3. Even with `MSYS_NO_PATHCONV=1`, asyncio subprocess doesn't honor it consistently

**Fix:** Wrap entire docker command in `wsl -e sh -c '...'` to bypass Git Bash path conversion entirely:
```bash
# Instead of: wsl docker run -e PATH=/home/... ...
# Use: wsl -e sh -c 'docker run -e PATH=/home/... ...'
```

This is implemented in `ClaudeRunner._build_claude_command()` which builds the docker command as a shell string and passes it to `sh -c`.

**Debug Commands:**
```bash
# Verify uv is installed
wsl docker run --rm --entrypoint bash debussy-sandbox:latest -c 'which uv && uv --version'

# This FAILS (Git Bash mangles paths):
wsl docker run --rm -e PATH=/home/claude/.local/bin:/usr/bin debussy-sandbox:latest ...

# This WORKS (sh -c wrapper):
wsl -e sh -c 'docker run --rm -e PATH=/home/claude/.local/bin:/usr/bin debussy-sandbox:latest ...'
```

### 3. WSL/MSYS Path Conversion (FIXED)

When running Docker through WSL from Git Bash, paths get converted to Windows format.

**Symptoms:**
- PATH shows `/mnt/c/Users/...` or `/c/Users/...` instead of Linux paths
- `/home/claude` becomes `C:\Program Files\Git\home\claude`

**Root Cause:** Git Bash's MSYS layer converts Unix-like paths to Windows paths before passing to WSL.

**Solution:** Implemented in `ClaudeRunner._build_claude_command()` - we now explicitly set `PATH` environment variable when launching containers to isolate them from host environment.

### 4. Windows .venv Mounted in Linux Container (FIXED)

**Symptoms:**
```
failed to locate pyvenv.cfg: The system cannot find the file specified.
```

**Root Cause:** Windows-created `.venv` directories are incompatible with Linux. When the project is mounted into the container, the Windows venv breaks Python tooling.

**Solution:** Mount empty tmpfs volumes over host-specific directories to "shadow" them:
```bash
--mount type=tmpfs,destination=/workspace/.venv
--mount type=tmpfs,destination=/workspace/.git
--mount type=tmpfs,destination=/workspace/__pycache__
```

This is now implemented in `ClaudeRunner._build_claude_command()`.

### 5. Prompt Shell Quoting (FIXED)

**Symptoms:**
- Docker container starts but no output appears
- Process runs for extended time then exits with code 2
- No streaming logs visible

**Root Cause:** The prompt passed to `-p` contains spaces, newlines, and special characters. When building the docker command as a shell string for `sh -c`, the prompt must be shell-quoted.

**Fix:** Use `shlex.quote(prompt)` in `ClaudeRunner._build_claude_command()` before joining the docker command string.

## Solutions Summary

| Issue | Status | Solution |
|-------|--------|----------|
| Skills not in container | Workaround | Use `--no-learnings` flag |
| uv not found | FIXED | `wsl -e sh -c` wrapper + explicit PATH |
| MSYS path conversion | FIXED | Shell command string via `sh -c` |
| Windows .venv in container | FIXED | tmpfs mounts to shadow host dirs |
| Prompt shell quoting | FIXED | `shlex.quote()` for prompt in shell string |

## Docker Image

The sandbox uses `debussy-sandbox:latest` built from `src/debussy/docker/Dockerfile.sandbox`.

**Key components:**
- Base: `node:20-slim`
- Claude Code: installed globally via npm
- Python/uv: for Debussy quality gates
- User: `claude` (UID 1001)

**Build command:**
```bash
debussy sandbox-build --no-cache
```

## Running Manually

```bash
# With OAuth auth (recommended)
MSYS_NO_PATHCONV=1 wsl docker run --rm \
  -v "/mnt/c/Users/YOU/.claude:/home/claude/.claude:rw" \
  -v "/mnt/c/Projects/myproject:/workspace:rw" \
  -w /workspace \
  debussy-sandbox:latest \
  --dangerously-skip-permissions \
  --print "Your prompt here"

# Check container environment
MSYS_NO_PATHCONV=1 wsl docker run --rm \
  --entrypoint /bin/bash \
  debussy-sandbox:latest \
  -c 'whoami && echo PATH=$PATH && which uv'
```

## Debussy Integration

Set in `.debussy/config.yaml`:
```yaml
sandbox_mode: devcontainer
```

Or use CLI flags:
```bash
debussy run --sandbox plan.md    # Enable sandbox
debussy run --no-sandbox plan.md # Disable sandbox
```
