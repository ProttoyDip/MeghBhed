# Contributing

MeghBhed is built by Team Last_Call during the NASA Space Apps hackathon (13–14 Nov 2026). **No project code may be written before the hackathon starts.** Until then, only documentation changes are allowed.

## Branches

- `main` always works. Nobody pushes to it directly during the hackathon.
- Create one branch per task, named by area: `pipeline/<task>`, `web/<task>`, `api/<task>` or `docs/<task>`.
  Example: `pipeline/hh-hv-change`.

## Commits

- Keep commits small, and write the message in the imperative: `Add WorldCover tree mask`.
- Never commit raw data, credentials, `.netrc` files or API keys. Keys go in environment variables only.
- Never commit invented numbers. Every figure in the app must come from `stats.json`, produced by the pipeline.

## Pull requests

1. Open a pull request into `main` and link the issue.
2. Ask one teammate from a different area to review it.
3. Merge after approval and a passing check. Delete the branch afterwards.

## Owners

| Area | Owner |
| --- | --- |
| `pipeline/` radar processing | Prottoy Saha Dip |
| `pipeline/` statistics | Md. Thouhidul Islam |
| `api/` and AI assistant | S.M. Sao.Mio Rashid Sakin |
| `web/` | Shuvo Singh Partho |
| Validation data | Eva Jahan |
| `docs/` and presentation | Suchismita Sarker |

## Docs

Run `npx markdownlint-cli2 "**/*.md"` before opening a pull request that changes Markdown.
