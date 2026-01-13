# Future Improvements

Items to revisit when upstream dependencies are fixed or new features become available.

## Claude Code Token Reporting Bug

**Status**: Waiting for Anthropic fix
**Affected**: Context percentage display in TUI (shows >100%)

The 331% context percentage bug is caused by Claude Code's stream-json output reporting cumulative session totals instead of current context window usage. Our formula is correct.

### Related GitHub Issues

- [#13783 - Statusline context_window JSON contains cumulative tokens](https://github.com/anthropics/claude-code/issues/13783) - Main issue
- [#13557 - Context Usage > 100% on fresh session](https://github.com/anthropics/claude-code/issues/13557)
- [#13842 - Context tracking not updated after compression/compact](https://github.com/anthropics/claude-code/issues/13842)
- [#11335 - Context Remaining Display Shows 0% When ~50% Available](https://github.com/anthropics/claude-code/issues/11335)

### Current Behavior

- `input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens` are cumulative across the session
- Values keep growing even after auto-compact discards old context
- Makes context percentage display meaningless

### When Fixed

Once Anthropic fixes the stream-json output to report current context (not cumulative), the TUI should display accurate percentages without any code changes on our side.

### Potential Workaround (Not Implemented)

Could cap display at 100% or show "N/A" when over 100%, but this would hide useful information if the underlying data ever becomes accurate.
