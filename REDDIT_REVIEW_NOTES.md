# Reddit API Review Notes

## App name

AVA Trend Research

## Intended use

Private, local, read-only research tool for identifying recurring software/tool problems, unmet user needs, and general tool-development trends in public Reddit discussions.

## Important clarification

The app is **not intended to track, collect, copy, monitor, or appropriate ideas, projects, product concepts, inventions, or user-specific idea histories posted by Reddit users**.

Its purpose is limited to observing incoming problem signals and recurring difficulties, for example:

- users repeatedly struggling with the same task,
- requests for simpler tools,
- recurring manual workflows,
- gaps in existing consumer software,
- general trends showing where a problem remains insufficiently solved.

The analysis focuses on problem patterns and trends rather than individual Redditors.

## Reddit actions

Read-only:

- public search,
- public post metadata/text,
- selected public comments when needed for context.

Not used:

- posting,
- commenting,
- voting,
- messaging,
- following,
- moderation actions,
- private-data access.

## Data handling

The reference client returns a minimized JSON representation to a local process. It does not build a user-profile database and does not train AI/ML models on Reddit data.

## Why Devvit is not sufficient

The intended workflow runs locally outside Reddit and needs read-only discovery across multiple public communities. It does not provide an on-Reddit experience, moderation feature, or community-installed interactive application.
