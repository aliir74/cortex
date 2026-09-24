# new-session preferences

## dispatch_mode
<!-- background = launch the new session with `claude --bg` (default); print = only print the command for you to run in a terminal -->
dispatch_mode: background

## default_model
<!-- Model for the new session (alias like opus/sonnet or a full model id). Empty = reuse the launching session's own model -->
default_model:

## default_effort
<!-- low / medium / high / xhigh / max. Empty = omit --effort and use the CLI default -->
default_effort:

## use_worktree
<!-- true = pass --worktree so the new session works in an isolated git worktree (git repos only). Default: false -->
use_worktree: false

## brief_dir
<!-- Directory for brief files. Default: /tmp (ephemeral) -->
brief_dir: /tmp
