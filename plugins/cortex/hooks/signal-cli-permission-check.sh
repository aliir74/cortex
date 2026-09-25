#!/bin/bash
# signal-cli permission hook — Pattern A (read/write gating).
# signal-cli is usually linked to a personal Signal account as a secondary device, so
# every write op touches real conversations. Gate them.
# Note: `receive` is allowed (read) but it drains this device's queue — see the signal-cli skill.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# grep is line-based; strip heredoc bodies so a payload line that documents a
# tool invocation is not read as a real one.
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$HOOK_DIR/lib/strip-heredocs.awk" ]; then
  CMD_SCAN=$(printf '%s\n' "$COMMAND" | awk -f "$HOOK_DIR/lib/strip-heredocs.awk")
else
  CMD_SCAN="$COMMAND"
fi

# Only intercept signal-cli invocations (optionally path-prefixed), not the literal
# word used as an argument elsewhere (e.g. `echo signal-cli is installed`).
if ! echo "$CMD_SCAN" | grep -qE '(^|&&|\|\||;|\|)[[:space:]]*[^[:space:];&|]*signal-cli([[:space:]]|$)'; then
  exit 0
fi

# Always safe: --help / -h anywhere
if echo "$CMD_SCAN" | grep -qE '(^|[[:space:]])(--help|-h)([[:space:]]|$)'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "signal-cli: help flag"}}'
  exit 0
fi

# Always safe: version metadata
if echo "$CMD_SCAN" | grep -qE 'signal-cli([[:space:]]+[^[:space:]]+)*[[:space:]]+(version|--version)([[:space:]]|$)'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "signal-cli: version"}}'
  exit 0
fi

# Write verbs — checked BEFORE the read allow, because a chained command
# (`signal-cli listContacts && signal-cli send ...`) would otherwise match the read
# verb and let the send through ungated.
WRITE_VERBS='send|sendReaction|sendReceipt|sendTyping|sendStory|sendContacts|sendSyncRequest|sendPaymentNotification|sendPollCreate|sendPollVote|sendPollTerminate|sendPinMessage|sendUnpinMessage|sendMessageRequestResponse|sendAdminDelete|remoteDelete|block|unblock|trust|joinGroup|quitGroup|updateGroup|updateProfile|updateContact|updateAccount|updateDevice|updateConfiguration|removeContact|removeDevice|removePin|setPin|addDevice|addStickerPack|uploadStickerPack|link|register|verify|unregister|deleteLocalAccountData|startCall|acceptCall|hangupCall|rejectCall|startChangeNumber|finishChangeNumber|submitRateLimitChallenge|daemon|jsonRpc'
if echo "$CMD_SCAN" | grep -qE "signal-cli([[:space:]]+[^[:space:]]+)*[[:space:]]+($WRITE_VERBS)([[:space:]]|$)"; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "ask", permissionDecisionReason: "signal-cli write/modify operation on a personal Signal account — confirm before proceeding"}}'
  exit 0
fi

# Read-only verbs. Global flags (-o json, -a <number>, -d <dir>, --verbose ...) may
# precede the subcommand, so allow intervening tokens before the verb.
READ_VERBS='listAccounts|listContacts|listGroups|listDevices|listIdentities|listCalls|listStickerPacks|getUserStatus|getAttachment|getAvatar|getSticker|receive'
if echo "$CMD_SCAN" | grep -qE "signal-cli([[:space:]]+[^[:space:]]+)*[[:space:]]+($READ_VERBS)([[:space:]]|$)"; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "signal-cli read-only operation"}}'
  exit 0
fi

# Everything else is a write, an account/device change, or an unrecognised subcommand.
# Includes send*, block/unblock, trust, *Group, update*, remove*, link/register/unregister,
# deleteLocalAccountData, and the call verbs.
jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "ask", permissionDecisionReason: "signal-cli write/modify operation on a personal Signal account — confirm before proceeding"}}'
exit 0
