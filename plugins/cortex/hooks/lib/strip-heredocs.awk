# Remove heredoc bodies from a (possibly multi-line) shell command string.
# grep is line-based, so without this a documentation or payload line inside a
# heredoc that happens to start with a tool name is read as a real invocation.
# The `<<DELIM` line itself is kept; every line up to and including the closing
# delimiter is dropped.
skip {
  if ($0 ~ delim_re) { skip = 0 }
  next
}
{
  print
  line = $0
  if (match(line, /<<-?[ \t]*[\047\042]?[A-Za-z_][A-Za-z0-9_]*/)) {
    d = substr(line, RSTART, RLENGTH)
    sub(/^<<-?[ \t]*[\047\042]?/, "", d)
    delim_re = "^[ \t]*" d "[ \t]*$"
    skip = 1
  }
}
