# SMB Playbook

Default motion for all Shredly GTM agents when the target is an SMB / self-serve buyer (see `CLAUDE.md` ICP). Deviate only when the task explicitly says otherwise (e.g. a genuine enterprise inbound request).

## Principles
1. **Self-serve is the primary CTA, always.** "Sign in with Google and get a key" beats "book a call" for a $0-$50/mo product bought by one person on a card. Only offer a call when the prospect asks for one or the ask is clearly Private-tier ($50/mo) with real setup questions.
2. **Short cycles.** An SMB AI-team lead decides in days, not a quarter-long procurement cycle. Sequences should be 2-3 touches, not 6-8.
3. **Speak to one person, not a committee.** No "stakeholders," "buying committee," or procurement language. The reader is usually the person who will also do the integration.
4. **Lead with the tier that fits the ask**, not the biggest number: Free to try, $10/mo shared once they're past free limits, $50/mo private only when they actually need isolation/control (a second internal tool, sensitive data, dedicated capacity) — don't upsell Private by default.
5. **Budget-aware, not budget-apologetic.** State the price plainly; don't over-explain or justify a $10-$50/mo cost.

## Default outbound sequence (outbound-sdr)
- **Touch 1**: Signal-based, short (under 120 words). One concrete observation about their repo/product, the value prop, a "try it in 2 minutes" link. No pricing needed yet.
- **Touch 2** (if no reply, ~4-5 days later): One new angle (a differentiator or a specific use case relevant to what they're building), still short, same CTA.
- **Touch 3** (final, ~1 week later): Direct "should I close the loop on this" — low-pressure, keeps door open, no more chasing after this.

## Default inbound flow (inbound-demo)
- Default reply assumes they can self-serve today: answer their question, give the Free-tier signup path, mention $10/$50 tiers only if their question implies they'll outgrow Free.
- Only propose a call if they ask for one, or their message describes a Private-tier scenario (compliance, isolation, multiple internal data sources) that's genuinely worth 15 minutes.

## Default onboarding/expansion (customer-success)
- Onboarding email goal: get their first MCP server live and connected to a client (Claude Desktop/Cursor/Continue/Windsurf) within the first session — one concrete next action, not a feature tour.
- Expansion nudge from Free → $10/mo: trigger off an actual limit being hit, not a calendar date. Say what limit, plainly.
- Expansion nudge from $10/mo → $50/mo: trigger off a real need for isolation/control the customer has expressed, not a generic upsell.

## Objection handling notes
- "Too expensive": at $10-$50/mo, the honest comparison is engineering time to self-host — point at the vs.-self-hosting differentiator in `CLAUDE.md`, don't discount reflexively.
- "We'll just build it ourselves": legitimate for a team with spare eng time; be honest about that tradeoff rather than oversell against it.
