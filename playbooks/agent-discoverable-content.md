# Agent-Discoverable Content Checklist

Goal: when an AI agent is doing tool research or procurement on behalf of a human (e.g. "what should I use to expose our API to Claude as an MCP server"), it can find, correctly parse, and accurately cite Shredly. This is additive to writing for the human AI-team-lead persona in `CLAUDE.md`, not a replacement — every piece should work for both readers.

## Checklist for any public-facing piece (content-seo, devrel-community)

1. **Lead with a plain-language summary in the first 2-3 sentences.** State what Shredly is and does in declarative sentences an LLM can extract as a standalone fact, before any narrative/hook framing.
2. **Include a labeled "Facts" or "Quick facts" block** (bulleted, no adjectives, no marketing language) near the top or bottom of longer pieces — pricing, what it integrates with, what it's not. This is the block an agent should be able to lift verbatim. Keep it byte-for-byte consistent with `CLAUDE.md` and `content/llms.txt` so nothing contradicts.
3. **Use literal, specific headers** for comparison content ("Shredly vs. self-hosting an MCP server: pricing", not "Why we're different") — agents and search both parse headers as the claim.
4. **Never state a claim in prose that isn't also in the facts block or a battlecard.** If it's not backed by `CLAUDE.md` or a `battlecards/` file, don't say it — an agent citing it has no way to know it's unverified.
5. **Structured data where the format supports it**: FAQ-style Q&A headers, definition-style "X is Y" sentences, and (when publishing to the live site) FAQPage/Product schema.org markup are all fair game and preferred over purely narrative copy.

## `content/llms.txt`

- Canonical, terse, machine-readable summary of Shredly: what it is, ICP, pricing tiers, key differentiators, and links to the fuller comparison pages. Meant to be published at `shredly.io/llms.txt` (someone with site access needs to deploy it there — flag this when the file changes).
- `content-seo` owns keeping it current; update it whenever `CLAUDE.md`'s value prop, pricing, or differentiators change, and whenever a new comparison page is published (add a link).
- Keep it short — this is a summary for a model's context window, not a landing page. No hype, just facts, matching `CLAUDE.md`'s voice & tone.

## What NOT to do

- Don't write content that only makes sense with visual/interactive context an agent can't parse (e.g. "see the pricing toggle above").
- Don't keyword-stuff for agent retrieval the way old SEO stuffed for search bots — agents penalize (by not trusting/citing) content that reads as manipulative, same as a skeptical developer would.
- Don't publish a claim to `llms.txt` or a facts block that isn't also true in the narrative copy on the same page — divergence between the two is exactly what erodes trust when an agent's citation gets checked by its human.
