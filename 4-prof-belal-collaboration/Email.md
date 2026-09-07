# First-contact email — Prof. Belal Alsinglawi

**To:** balsinglawi@zu.ac.ae (confirm current address)
**Subject:** Securing autonomous AI agents — a working prototype and a proposal built around your work
**Attachments:** `Proposal.docx` (or `Proposal.html`), `Appendix-Auditing-Agent.docx`

---

Dear Prof. Alsinglawi,

I'm Evelyn Du, an AI engineer working on the security and verifiability of autonomous AI agents. I'm writing because your published work is an unusually direct fit for a problem I've already begun building on, and I'd value thirty minutes of your time to choose where to take it.

The problem in one sentence: agents now install third-party capabilities — MCP servers, skills, plugins — from public registries with almost no review, and the supply-chain, credential-revocation and accountability questions this raises are the agent-era continuation of your IoT and microservices security research, your smart-contract key revocation work in IoT/WoT environments, and your ensemble intrusion-detection and explainable-ML work.

Two things I want to be concrete about up front:

**The core is already built, not hypothetical.** The sandbox-and-verify auditing agent at the centre of my recommended direction exists today as a working, tested system — a four-stage pipeline with a hash-chained audit trail, evaluated on 121 real annotated contracts from the SmartBugs corpus. I report its result honestly, including where it currently trails a rule-based baseline; that measured baseline is exactly what makes the adversarial-screening and public-benchmark work the valuable next step. The architecture and the exploit-corpus schema are in the attached technical appendix, and I'm glad to share the repository before we speak.

**The division of labour keeps your time on the parts only you can do.** I would take on the build and the filing: the screening tool (open source), a labelled public benchmark with a leaderboard website, and the provisional patent on the method. From you I'd ask scoping judgement on the threat taxonomy, review of the evaluation design, your name on the outputs, and — if you'd like it — the paper, led from your side. No compute or data budget is needed on your end; the corpus comes from public registries and I can begin immediately.

The attached proposal sets out five directions, ranked rather than offered as equals. Direction 1 (adversarially-robust screening for agent skills and MCP servers, with the public benchmark the field lacks) is my recommendation. Direction 2 (extending your smart-contract key revocation to autonomous agents — revoking a live delegation tree with a propagation guarantee) is the strongest alternative and the closest to your own line. Direction 3 (tamper-evident audit trails for regulated agents) follows naturally from either. Directions 4 and 5 sit closest to your intrusion-detection and healthcare work, and I'm candid in the document about why I'd attach each to an active track rather than run it standalone.

One constraint shapes every timeline: public disclosure ahead of a provisional patent filing forecloses protection, so each filing gate sits before the corresponding release. That's the one part of the schedule I'd ask not to compress, since it protects joint IP.

Could we find thirty minutes to choose a starting point? I'm ready to begin Direction 1 immediately, at no resource cost to you.

With thanks for your consideration,

Evelyn Du
120987698dwk@gmail.com

---

*Notes for me (not part of the email):*
- *Attach `Proposal.docx` for editability, or `Proposal.html` if sending a link/preview. Include `Appendix-Auditing-Agent.docx`.*
- *For NIW value, make sure any written agreement names **me** as an inventor on the provisional filing and as lead/co-author on the tool and benchmark (see Proposal §9).*
- *Confirm his current email at zu.ac.ae before sending.*
