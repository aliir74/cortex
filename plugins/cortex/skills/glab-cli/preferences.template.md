# glab-cli preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/glab-cli.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the CLI's default / auto-detect from the current repo."

## default_host
<!--
GitLab host the skill should target by default — e.g. `gitlab.com` or
`gitlab.example.com`. The skill exports `GITLAB_HOST=<value>` when set.
Leave empty to use whatever `glab config get host` returns.
-->
default_host:

## default_group
<!--
GitLab group/namespace used to scope `glab issue`/`glab mr` calls when the
current directory is not a GitLab clone. Leave empty to require running
inside a clone.
-->
default_group:

## default_project
<!--
Project slug (without group prefix) used together with `default_group` to
build the `<group>/<project>` repo identifier for `--repo` flags.
Leave empty to require running inside a clone.
-->
default_project:

## context_files
<!--
Absolute paths Claude should read for additional GitLab context — e.g.
your standard MR description template, project-wide labels cheat sheet,
or a list of common reviewers. One path per line. Leave empty if none.
-->
context_files:
