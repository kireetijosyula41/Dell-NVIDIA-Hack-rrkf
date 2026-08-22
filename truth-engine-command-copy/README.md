# Truth Engine Dashboard

Build a high-tech, futuristic dark-mode Mission Control Dashboard for an AI Multi-Agent system called "The Meeting Room Truth Engine" powered by OpenClaw and OpenShell.

### Overall Aesthetic:
- Dark theme: Slate-900 background (#0F172A), cyber glassmorphism cards with glowing borders (neon blue, amber, emerald, purple).
- Top Bar: Header showing "OPENCLAW MISSION CONTROL // THE TRUTH ENGINE", a green badge saying "OPENSHELL: ZERO-EGRESS AIR-GAPPED", and a hardware indicator "NVIDIA DGX SPARK (GB10)".

### Top Demo Controls Bar (Stage Action Bar):
Include 4 prominent trigger buttons at the top of the dashboard:
1. "Scenario 1: Re-Inventing Wheel"
2. "Scenario 2: Prod Fire"
3. "Scenario 3: Cloud GPU Waste"
4. "Scenario 4: 6-Month Refactor"

When any button is clicked, trigger a multi-step simulated execution sequence (1-2 second delay per step) that animates the Agent Office, populates the Terminal Logs line-by-line, moves a task card on the Kanban Board, and displays the Ironic Decision Card modal.

---

### Dashboard Layout (4 Main Grid Sections):

#### Section 1: Agent Office (Top-Left 2x2 Grid)
Render 4 agent cards with glowing status indicators:
- Vigil (Signal Sentinel) - Blue glow (#38BDF8) - Role: Audio Ingestion & Intent Router
- Audit (Ground-Truth Auditor) - Amber glow (#F59E0B) - Role: Git Repo & Log Scanner
- Forge (Patch Builder) - Emerald glow (#10B981) - Role: Code Diff Generator
- Chief (Chief of Staff) - Purple glow (#8B5CF6) - Role: Orchestrator & Approval Manager
Each agent card should display an animated pulsing ring when active ("LISTENING", "AUDITING", "PATCHING", "AWAITING APPROVAL").

#### Section 2: Real-Time Event Feed & Terminal Stream (Top-Right)
- A dark terminal console output box with green/cyan/amber monospace text.
- Auto-scrolls and streams log lines sequentially whenever a scenario button is triggered.
- Includes timestamps like `[18:04:12]` and tags like `[Vigil]`, `[Audit]`, `[OpenShell]`, `[Forge]`.

#### Section 3: Interactive Task Kanban Board (Bottom-Left)
4 Columns: "Inbox", "Auditing", "Review (Action Needed)", "Done".
- When a scenario starts, a task card spawns in "Inbox", moves to "Auditing", and lands in "Review".
- Clicking the Approval Button on the Decision Card moves the task card into "Done" with a green checkmark animation.

#### Section 4: CTO Decision & Ironic Report Card (Bottom-Right / Modal Overlay)
This is the core highlight. When the simulation reaches the "Review" phase, render a high-impact report card with:
- Bold Header Banner: (e.g. "🚨 PROJECT TITAN PROPOSAL REPORT")
- PM / Dev Estimate Box (Red/Amber outline)
- Agent Verdict Box (Glassmorphic dark box with neon text) containing ironic, funny, and punchy text (e.g. "Bro, you can literally npm install...")
- Huge Glowing Action Button (e.g., "[ 🟢 APPROVE PR & SAVE $32,000 ]" or "[ 🔴 APPROVE EMERGENCY ROLLBACK ]")

---

### Scenario Data States to Code Into the App:

#### Scenario 1 Data:
- Trigger Button: "Scenario 1: Re-Inventing Wheel"
- Audio Claim: "Team, we're kicking off Project Titan! We need to build a brand-new internal notification and queue service from the ground up."
- Terminal Logs:
  - `[Vigil] Audio Ingested -> Event: NEW_PRODUCT_PROPOSAL`
  - `[OpenShell] Sandboxed Audit: Scanning local git trees...`
  - `[Audit] MATCH FOUND: /packages/core-pubsub (Shipped 8 months ago)`
  - `[Audit] INBOX MATCH: 4 other teams requested access to core-pubsub last week.`
  - `[Forge] Generated Pull Request: import @internal/core-pubsub`
- Ironic Report Content:
  - Title: "PROJECT TITAN PROPOSAL REPORT"
  - PM Estimate: "4 Engineers | 160 Hours | $32,000 Budget | Delivery: Q4"
  - Required Accesses: "AWS SQS, GCP PubSub, PagerDuty Admin"
  - Agent Verdict: "Bro, you can literally npm install @internal/core-pubsub. It's been running in production for 240 days. I created a PR importing it into your repo. You're welcome."
  - Action Button: "[ 🟢 APPROVE PR & SAVE $32,000 ]"

#### Scenario 2 Data:
- Trigger Button: "Scenario 2: Prod Fire"
- Audio Claim: "Product Phoenix launched yesterday! It's running smooth as butter in production, zero downtime, time to celebrate!"
- Terminal Logs:
  - `[Vigil] Audio Ingested -> Event: STATUS_CLAIM_STABLE`
  - `[Audit] Querying BQL Logs... ALERT: 14,200 '500 Internal Server Errors'`
  - `[Audit] Scanning Support Inbox... ALERT: 18 angry emails from VP of Sales`
  - `[Forge] Fetching Local Runbooks... Drafting Git Revert Patch to Tag v1.4.2`
- Ironic Report Content:
  - Title: "PRODUCTION REALITY CHECK"
  - Dev Claim: "Smooth as butter, zero issues."
  - Ground Truth: "14,200 database deadlocks logged, 18 high-priority support tickets, CTO inbox is on fire."
  - Agent Verdict: "Developer is delusional. Production is actively burning. I drafted an emergency Git Rollback to tag v1.4.2 and executed the emergency runbook."
  - Action Button: "[ 🔴 APPROVE EMERGENCY ROLLBACK & REVERT ]"

#### Scenario 3 Data:
- Trigger Button: "Scenario 3: Cloud GPU Waste"
- Audio Claim: "Our customer feedback sentiment model is getting slow. We need to provision 8x H100 GPU instances on AWS for $15,000/month to keep up."
- Terminal Logs:
  - `[Vigil] Audio Ingested -> Event: INFRASTRUCTURE_REQUEST`
  - `[Audit] Analyzing code complexity: sentiment_classifier.py`
  - `[Audit] AST Result: Sentiment script is running a 3,000-line IF-ELSE regex loop.`
  - `[Forge] Refactoring regex to 3B local model on DGX Spark via Ollama.`
- Ironic Report Content:
  - Title: "INFRASTRUCTURE AUDIT REPORT"
  - PM Request: "$15,000/month AWS Cloud Provisioning ($180,000/year)"
  - Agent Discovery: "You are trying to rent an H100 GPU cluster to run a nested IF/ELSE statement written in 2021."
  - Agent Verdict: "I refactored the regex into a 3B local model running on our DGX Spark inside OpenShell for $0.00. I auto-declined the AWS cloud request."
  - Action Button: "[ 🟢 APPROVE LOCAL REFACTOR & CANCEL AWS ]"

#### Scenario 4 Data:
- Trigger Button: "Scenario 4: 6-Month Refactor"
- Audio Claim: "Our billing service codebase is technical debt hell. We need a 6-month complete feature freeze to rewrite the entire system in Rust."
- Terminal Logs:
  - `[Vigil] Audio Ingested -> Event: CODEBASE_REWRITE_PROPOSAL`
  - `[Audit] AST Analysis: 94% of bugs originate from ONE 600-line file.`
  - `[Audit] Git Blame: billing_parser.py written by Dave in 2023.`
  - `[Forge] Rewriting billing_parser.py into clean modular Python. Passing 48/48 unit tests.`
- Ironic Report Content:
  - Title: "ENGINEERING REFACTOR REPORT"
  - Dev Request: "6 Months Code Freeze | 1,000 Engineering Hours | $150,000 Lost Velocity"
  - Agent Discovery: "The entire codebase isn't broken. Just billing_parser.py written by Dave in 2023 while sleep-deprived."
  - Agent Verdict: "I refactored Dave's file in 1.4 seconds. All unit tests passed. You can keep shipping features on Monday."
  - Action Button: "[ 🟢 APPROVE REFACTOR & CANCEL CODE FREEZE ]"

---

### Interactive Polish & Animations:
- Include a "Reset / Clear Board" button.
- When the user clicks any "APPROVE" button on the Report Card, display a toast notification: "PR Executed & Local Memory Updated! $ Saved Recorded in memory.md", move the task card to "Done", and play a subtle success sound effect.
- Make the app feel responsive, dark-themed, sleek, and ready for live stage presentation.

This project was built with [Lovable](https://lovable.dev).

**Live app**: https://truth-engine-command.lovable.app

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/53e09458-226e-48e0-9e17-6018b3d6a1dd).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
