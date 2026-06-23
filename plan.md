/plan

## Goal
Implement x402 billing support for an MCP server skill (add usage-based micropayments via x402/USDC), including current pricing, integration patterns, and best practices for June 2026. Create or extend a concrete example within the skills/grok-build test area (skills/x402-mcp-biller/).

## Research Findings (from run of research-dispatcher + external sources June 2026)
**Dispatcher behavior (as required):**
- The research-dispatcher hook in run-grok-task.sh was automatically invoked during `run-grok-task.sh plan`.
- Decision: **HIGH** signal detected.
- Trigger pattern: `pricing` (first match in HIGH_CONFIDENCE_PATTERNS; also matched 'x402', '2026', 'billing', 'monetiz' etc.).
- Cache status: **MISS** (no entry under memory/research-cache/ for the normalized prompt; first run).
- Log output captured:
  ```
  == research-dispatcher: HIGH signal detected ==
  HIGH confidence external research required (trigger: pricing)
  Cache status: MISS (research sub-agents recommended before execute)
  ```
- INTERNAL test (separate prompt "purely internal refactor..."): correctly classified as INTERNAL, research disabled. Trigger reported as "purely internal".
- No cache was used. Research Findings below synthesized from live web data + prior cached project research (2026-06-18/19) + x402-mcp-biller/SKILL.md.

**Quick facts (pricing, facilitators, status as of ~June 2026):**
- Protocol: Mature. x402 Foundation (Linux Foundation + Coinbase et al., partners include Stripe, Cloudflare, Visa, AWS, Google). 120M–165M+ cumulative transactions, ~$41M–$50M+ USDC volume. Avg payment ~$0.05. Dominant chain: Base (majority share), also Solana, Polygon (recent facilitator support).
- Facilitators: Coinbase CDP (recommended; https://api.cdp.coinbase.com/platform/v2/x402 , generous free tier e.g. 1000 tx/mo noted historically, now minimal fee ~$0.001/settled payment in some notes). Cloudflare (edge + Agents SDK, batching). x402.org testnet for quickstarts. Stripe integrations for hybrid fiat+USDC.
- Pricing reality: Viable micropayments $0.001–$0.05 (or $0.01–$0.10) USDC per call/tool. Sub-cent possible on Base (<$0.0001 gas). Format in middleware: `"$0.001"`.
- Networks (CAIP-2): Base Sepolia `eip155:84532`, Base main `eip155:8453`, Solana, Polygon etc.
- MCP + x402: Coinbase ships official MCP examples (clients + paid resource servers). Cloudflare `withX402` + MCP. MCP servers use Streamable HTTP transport to surface 402 at HTTP layer. Discovery via agentic.market, x402.org/ecosystem, MCPize/Glama extensions.
- Packages (seller/server side): `@x402/express`, `@x402/hono`, `@x402/next`, `@x402/core`, `@x402/evm` (and svm). Python: `x402[fastapi]`. Go support exists. Client side: `@x402/axios` etc for auto-paying agents.
- Free tier common recommendation: 50–100 calls/day for discovery before paywall.

**Deep context (patterns, pitfalls, best practices June 2026):**
- Canonical server pattern (from Coinbase quickstart + examples): Create `x402ResourceServer` + register `ExactEvmScheme`, apply `paymentMiddleware({ "GET /my-tool": { accepts: [{scheme:"exact", price:"$0.01", network:"eip155:84532", payTo:"0x..."}], description, mimeType } }, server)`. Protected routes return 402 automatically on missing/invalid payment; facilitator verifies + settles before handler runs.
- For MCP servers specifically: Prefer HTTP-based MCP (not just stdio) so the 402 challenge/response works at transport level. Wrap specific tools or entire server. Reference: Coinbase MCP + x402 examples, Cloudflare Agents SDK + `withX402(new McpServer...)`.
- Client/agent side: Agents detect 402 + PAYMENT-REQUIRED header, sign authorization (EIP-3009 or SVM), retry with X-PAYMENT / PAYMENT-SIGNATURE header. Use wallet guardrails (per-call + per-session spend caps).
- Integration architecture for skill: "Wrapper" approach (as described in existing x402-mcp-biller/SKILL.md) — take an existing MCP server implementation and layer payment config + middleware without forking core logic. Or ship a reference billable MCP server example.
- Discovery & monetization: Instrument usage first. Offer generous free tier + paid deeper calls. Register in x402 Bazaar / agentic.market / MCPize. Hybrid (subscription + per-call) often wins over pure usage.
- Common pitfalls:
  - Pricing too low (perceived low value) or too high (no traffic).
  - No free tier → zero discovery/adoption.
  - Forgetting graceful 402 handling / fallback in clients.
  - Missing observability (log 402 challenges, tx receipts, settlement success).
  - Running hot wallet on VPS without custody (use CDP or equivalent).
  - Ignoring protocol fragmentation (plan for x402 as primary; Stripe MPP hybrid possible).
  - Dynamic routes: use named params for Bazaar compatibility.
- Best practices: Start on Base Sepolia (faucet). Use CDP facilitator. Price in whole cents or $0.001 increments. Add description + mimeType. Log everything. Test end-to-end with an x402-aware client (Claude Desktop MCP or custom agent). Volume is real but "demand not tech" is the gap — focus on high-utility niche tools.
- Sources: Coinbase CDP docs (quickstart-for-sellers, mcp-server), x402.org, Cloudflare x402 blog, eco.com guides, GitHub x402-foundation/x402 examples (express, mcp clients/servers), prior project research.md files, awesome-x402.

**Gaps / unknowns noted in research:** Exact current CDP free tier limits can fluctuate (check at integration time); specific MCPize revenue share numbers; exact on-chain volumes are reported variably.

## Context
- Workdir: /root/.openclaw/workspace
- Zone: green (skills/grok-build + new/updated MCP billing skill example; specifically extend skills/x402-mcp-biller/)
- Requester channel: (per user query context)
- Related files: 
  - skills/grok-build/scripts/research-dispatcher.sh
  - skills/grok-build/scripts/run-grok-task.sh
  - skills/grok-build/SKILL.md
  - skills/grok-build/references/{research-augmented-plan.md,prompt-template.md,subagent-*.md}
  - skills/x402-mcp-biller/SKILL.md (existing descriptive skill with prior research)
  - projects/mossfund/3a-mcp-servers/ and 3c-x402-payments/ (prior research + next-steps)
  - memory/grok-plans/plan-test-research-dispatcher.md (identical test prompt)

## Requirements
- Trigger and capture the research-dispatcher hook automatically by invoking `skills/grok-build/scripts/run-grok-task.sh plan <workdir> <prompt-file>`. Document HIGH + exact trigger pattern + MISS in the plan and summary.
- Produce a plan.md that includes a concrete "Research Findings" section grounded in June 2026 data (pricing $0.001–$0.05, Coinbase CDP primary, middleware patterns, MCP HTTP examples, pitfalls).
- Extend or create example code under skills/x402-mcp-biller/ (examples/ dir) showing a billable MCP server or wrapper:
  - Concrete middleware setup for one or more tools (price per call).
  - Support for Base (Sepolia + mainnet notes).
  - Reference to official packages (@x402/express or equivalent + MCP SDK over HTTP).
  - Free tier guidance + config example.
  - Simple test instructions (no secrets).
- Keep full Telegram approval gate intact (plan phase → pending → owner "ja/kör/ok" → execute phase). No changes to that flow.
- Document how the dispatcher was detected (this prompt matched HIGH via pricing/x402/2026/monetization keywords).
- Update or extend the x402-mcp-biller/SKILL.md "Steps", "Examples", and "References" with fresh patterns if appropriate (as part of the skill example).
- Verification steps must be runnable locally without real keys/deployment (mock or testnet notes only).
- Preserve all existing safety: no secret handling, no external changes outside green zone.

## Out of scope
- Real deployment, production wallets, mainnet secrets, or live USDC flows.
- Changes outside skills/grok-build + skills/x402-mcp-biller test area.
- Full production-ready MCP server beyond the illustrative example/wrapper.
- Implementing new research sub-agent spawning logic (just document the current hook behavior and use of prepare/write_cache if relevant).
- Any internal refactor that would trigger INTERNAL (explicitly test and confirm blocking).

## Verification
- Reproduce dispatcher log: Run `skills/grok-build/scripts/run-grok-task.sh plan . <clean-prompt-file>` and confirm output contains:
  - "== research-dispatcher: HIGH signal detected =="
  - "HIGH confidence external research required (trigger: pricing)" (or equivalent x402/2026 match)
  - "Cache status: MISS ..."
- A separate prompt containing "purely internal refactor" + "skip research" must classify INTERNAL and suppress the block.
- After plan approval + (future) execute: 
  - skills/x402-mcp-biller/ contains new examples/ (e.g. express-mcp-biller.ts or python equivalent + README).
  - Example demonstrates paymentMiddleware + MCP tool registration with realistic $0.01 price.
  - SKILL.md (or new EXAMPLE.md) references the code + updated best practices.
  - `ls skills/x402-mcp-biller/examples` + simple node/pytest dry-run or config validation passes.
  - plan.md and Telegram summary include citations to research sources + dispatcher evidence.
- No plan.md changes or code edits occur before explicit execute approval.
- Cache remains MISS for this prompt (or gets populated only via explicit write if sub-agents were run).

## Rules (planning phase)
- PLANNING ONLY — explore, read files, search (web + local), run dispatcher via the official script, write plan.md. 
- Do NOT modify source files except plan.md in this phase.
- The research-dispatcher hook **must** run automatically via run-grok-task.sh (achieved; logs captured).
- When the plan is ready, summarize it clearly (see end of this document) and STOP.
- Do not implement until a separate execution phase (after owner approval via Telegram keywords).
- Always cite research sources in the final plan summary sent to Telegram.
- Internal-only test case must remain blocked.

---

**Research Augmentation Rule:** Followed. The orchestrator (via run-grok-task.sh) ran the hook; findings injected here. Sub-agent style research (Serper/web + synthesis from existing + direct docs) used.

**Next after owner OK:** Use `skills/grok-build/scripts/run-grok-task.sh execute . <channel> <target>` (or equivalent spawn). The execute prompt will instruct to read this plan.md exactly and implement only the listed items.
