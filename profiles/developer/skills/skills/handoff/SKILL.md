---
name: handoff
description: Write a handoff doc so a fresh agent can continue the work.
version: 1.0.0
author: Hermes Agent (adapted from mattpocock/skills)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [handoff, context, delegation, multi-session]
    related_skills: [dispatching-parallel-agents, executing-plans]
---

# Handoff

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS - not the current workspace.

Include a "suggested skills" section in the document, naming which skills the next agent should call the Skill tool for.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
