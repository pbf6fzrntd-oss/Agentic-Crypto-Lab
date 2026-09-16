Company: Spaceflow (YC S26) — SpaceFlow Technologies, Inc., "AI-native procurement services for the physical economy" (San Francisco / Istanbul team, ~4 people)
NOT the unrelated real-estate-tech company also named "Spaceflow" — confirmed this is the YC S26 agent-infrastructure startup (procurement/supply-chain "company brain") via Y Combinator's company page and multiple press writeups (Dealroom, egirişim, ITU haber, yespress.io) before drafting.

Channel: LinkedIn DM
To: Spaceflow founding team — general, not a verified individual (see below)
Founders identified publicly: Emre Işık (Cambridge), Ali Eren Aytekin, Ali Orçun Şahinoğlu, Hakan Enes Aksu (ITU/Boğaziçi). No confirmed email for anyone on the team, and no single named "AI-team-lead" role — this is a 4-person founding team where anyone could reasonably own agent tooling.
Action before sending: pick one founder's LinkedIn profile (Ali Eren Aytekin and Hakan Enes Aksu both have public "Spaceflow (YC S26)" LinkedIn listings; Emre Işık and Ali Orçun Şahinoğlu are named in press but profiles weren't independently confirmed here) and send the DM below to that individual, not a company page.

---

## Qualification notes (read before sending)

Spaceflow is an unusually well-informed prospect to pitch, which changes the framing:

- **ICP fit on paper:** SMB (4 people), founder-led, clearly building agent-facing infrastructure — fits the "AI-team lead at a small company" persona CLAUDE.md targets.
- **But the obvious "customer" signal isn't really there.** Their core product *is* an MCP-compatible interface — public reporting describes ~285 procurement actions exposed as open, API-first, MCP-callable endpoints, live in production processing ~$400M/yr in supplier spend for enterprise customers. They didn't fail to build an MCP layer for their flagship product; they built one themselves, at real scale, before we'd ever talk to them. Pitching "let Shredly turn your product's API into an MCP server" would be selling them something they've already shipped and are running in production — not honest, and not useful to them.
- **Framing chosen: peer, not customer.** The genuine angle is practitioner-to-practitioner: they've felt the exact pain Shredly exists to remove (hand-building and operating an MCP layer in front of existing systems), just for their own procurement product rather than as a hosted service for others. The honest ask is "how are you handling this outside your core product" (their own internal tools, or as they extend "company brain" to systems beyond procurement) — not a hard pitch to replace live infra they built and that works.
- Message stays short and low-pressure per the peer framing — CTA is "try it if useful" + "happy to compare notes," not a booked-call push, consistent with SMB-PLAYBOOK's self-serve-first default but softened because this isn't a standard unmet-need signal.

---

## Message (LinkedIn DM)

Hi [Founder name] — congrats on the S26 launch. The "company brain" framing for Spaceflow stood out, and the detail that got my attention was the ~285 procurement actions you've exposed as MCP-callable endpoints — that's a real buildout, not a toy integration.

We're working the adjacent problem at Shredly: hosted MCP servers for existing APIs/databases, so a team doesn't have to build and run that protocol layer themselves for every system they want an agent to touch. You've clearly already solved that for your core product — I'm curious how you're thinking about it for anything *outside* procurement, if at all (internal tools, other data sources your own team wires agents into).

Free to try if it's useful for something smaller: shredly.io. Otherwise, happy to just compare notes on the MCP-hosting problem — 15 minutes sometime?
