# Project release index

Updated 2026-09-30. This repository contains applications on separate historical branches. The default branch is an older Crypto snapshot; use the canonical locations below. Merged code does not establish that a hosted service or customer workflow has been verified.

| Project | Canonical code | Release change |
| --- | --- | --- |
| Crypto snapshot research | [research_v2 on claude/tender-maxwell-jxsuo3](https://github.com/pbf6fzrntd-oss/Agentic-Crypto-Lab/tree/claude/tender-maxwell-jxsuo3/research_v2) | [PR #2](https://github.com/pbf6fzrntd-oss/Agentic-Crypto-Lab/pull/2) |
| Keena Growth Ops | [keena-growth-ops on claude/sales-pipeline-chat-zip-gl102o](https://github.com/pbf6fzrntd-oss/Agentic-Crypto-Lab/tree/claude/sales-pipeline-chat-zip-gl102o/keena-growth-ops) | [Merged PR #1](https://github.com/pbf6fzrntd-oss/Agentic-Crypto-Lab/pull/1) |
| CitraChem GTM | [Separate repository](https://github.com/pbf6fzrntd-oss/citrachem-gtm) | [Merged PR #1](https://github.com/pbf6fzrntd-oss/citrachem-gtm/pull/1) |
| Shredly GTM | [Separate repository](https://github.com/pbf6fzrntd-oss/shredly-gtm) | [Merged PR #1](https://github.com/pbf6fzrntd-oss/shredly-gtm/pull/1) |
| Contractor Platform | [Repository](https://github.com/pbf6fzrntd-oss/contractor-platform) | [Merged PR #1](https://github.com/pbf6fzrntd-oss/contractor-platform/pull/1) |
| Idea Lab | [Repository](https://github.com/pbf6fzrntd-oss/Idea-Lab) | [Merged PR #1](https://github.com/pbf6fzrntd-oss/Idea-Lab/pull/1) |
| Breakroom | [Repository](https://github.com/pbf6fzrntd-oss/Breakroom) | [Merged PR #1](https://github.com/pbf6fzrntd-oss/Breakroom/pull/1) |
| Agentic Research | [Repository](https://github.com/pbf6fzrntd-oss/Agentic-Research) | [Merged PR #1](https://github.com/pbf6fzrntd-oss/Agentic-Research/pull/1) |

## Crypto

On the canonical Crypto branch, run `python -m research_v2.demo` and open `.demo/cockpit/index.html`. This standard-library demo uses fictional fixed replay data. Historical journals and reports remain separate and are not evidence of prospective trading performance. The v2 path does not place orders or make paid provider calls. See `docs/SNAPSHOT_V2.md` on that branch for methodology and release limits.

## Keena

Use Node 24 in `keena-growth-ops/`, install with `npm ci`, configure the supplied environment example, and run `npm run dev`. Consult that application's release documentation before hosting. The private pilot requires authentication and durable SQLite storage. Discovery remains supervised; refreshing the queue does not search the web. A dedicated Keena repository remains a future extraction.

## Release prerequisites

CitraChem and Shredly are GTM operator tools. Approved product claims, response ownership and real activation evidence still require supplied business evidence. The Shredly MCP hosting runtime has not been identified in the reviewed repositories.

Contractor deployment must stop and drain old dispatchers, apply the additive recovery migration, deploy, and then restart dispatch. Use an isolated demo database and simulator SMS until provider recovery is verified.

Idea Lab and Keena require authenticated hosting and durable storage; Research can serve its generated static evidence dashboard. Breakroom requires a supervised disposable testnet wallet journey, receipt reconciliation and browser verification before a hosted pilot.

Historical operational copies on older branches are not removed by the separate GTM repositories. Do not treat this index as a history cleanup or a production launch announcement.
