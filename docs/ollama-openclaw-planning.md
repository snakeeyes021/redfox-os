### Epic 1: Base OS AI Infrastructure
*The OS-level foundation baked into the immutable image.*

* **Task: Bake Native Ollama Engine:** Integrate the `0.21.0` native `.tar.zst` payload directly into the RedFoxOS build process.
* **Task: Configure OS-Level Services:** Create the dedicated `ollama` user, map the `/usr/lib64` library paths for NVML discovery, and bake the `ollama.service` systemd unit so it is enabled on first boot.

### Epic 2: Core Agent Management (The Base `ujust` Recipes)
*The baseline user experience for installing a standalone OpenClaw CLI agent.*

* **Task: LLM Environment & Anti-Wedge Tuning:** Determine and inject the optimal environment variables (e.g., `OLLAMA_NUM_CTX`) or create a custom base Modelfile to ensure the models have a sufficient context window to handle massive OpenClaw tool payloads without hanging.
* **Task: `install-openclaw` Recipe:** Script the deployment of the OpenClaw CLI, inject it into the user's `PATH`, and research/leverage the `ollama launch openclaw --yes` command for silent baseline configuration.
* **Task: `uninstall-openclaw` Recipe:** Script the clean purge of the `~/.local/bin/openclaw` binary and the `~/.openclaw` workspace/database, ensuring the OS-level Ollama engine remains untouched.

### Epic 3: The Swarm Orchestrator (The Control `ujust` Recipes)
*The logic, tracking, networking, and daemon infrastructure to turn a RedFox machine into the "Brain."*

* **Task: Evaluate & Deploy Forgejo Tracker:** Research and implement the most resilient deployment method for the local issue tracker (comparing a standard Podman container against a native Fedora Podman Quadlet).
* **Task: Orchestrator Networking & Firewall:** Script `firewall-cmd` rules to open the Forgejo port (3000) and the Ollama port (11434) to the local subnet so workers can actually connect.
* **Task: Global Git Credential Management:** Configure a global OS-level Git Credential Helper to securely store the Forgejo auth token, allowing agents to run standard `git push` without embedding tokens in URLs.
* **Task: Native OpenClaw Secrets Wiring:** Automate the installation of OpenClaw's native Forgejo Skill and inject the API token directly into the Secrets manager (eliminating the need for raw `curl` hacking).
* **Task: Task & Model Assigner (Python Script):** Write the custom Orchestrator brain that reads the queue, ingests worker heartbeats (VRAM/online status), evaluates ticket complexity, and dynamically assigns roles and specific models to available workers.
* **Task: Orchestrator Systemd Service:** Wrap the Orchestrator's Python routing script into a persistent background daemon.
* **Task: `install-openclaw-orchestrator` Recipe:** The master setup script that deploys Forgejo, creates the API tokens, wires the credentials, configures the firewall, and starts the Orchestrator daemon.
* **Task: `uninstall-openclaw-orchestrator` Recipe:** The exact inverse to tear down the tracker, revoke tokens, close ports, and disable the daemon.

### Epic 4: Swarm Worker Nodes (The Drone `ujust` Recipes)
*The infrastructure, telemetry, and capabilities to allow auxiliary machines to bind to the swarm as dynamic team members.*

* **Task: Worker Telemetry & Heartbeat:** Develop the background script that constantly pings the Orchestrator with the worker's status ("Online," "Idle") and hardware capabilities ("8GB VRAM available").
* **Task: Task Lifecycle & Escalation Skills:** Implement the specific OpenClaw tools required for swarm physics:
    * *Context Handoff:* A procedure to commit partial progress to a `wip/` branch.
    * *Bailout/Escalate:* A tool to gracefully drop a failing task and tag the Forgejo issue (e.g., `Needs-Tortoise`).
* **Task: Dynamic Model & Role Switching:** Ensure the worker agent is a blank slate that can accept dynamic role ingestion (e.g., "Act as Junior Linter" vs "Act as Architect") and switch its active Ollama model based purely on the Orchestrator's assignment.
* **Task: Cold Start Model Pulls:** Script a background `ollama pull` for baseline models so the worker isn't dead in the water downloading weights when it receives its first assignment.
* **Task: Worker Systemd Service:** Wrap the local OpenClaw agent in a daemon that listens to the Orchestrator and executes assigned tasks.
* **Task: `install-openclaw-worker` Recipe:** The setup script that interactively collects the Orchestrator's IP and Token, pulls baseline models, wires the remote secrets, and starts the telemetry/worker daemons.
* **Task: `uninstall-openclaw-worker` Recipe:** The exact inverse to stop the daemon, purge the remote tracker credentials, and revert the node to a standalone base agent.