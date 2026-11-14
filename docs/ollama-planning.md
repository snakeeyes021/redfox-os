### Epic 1: Base OS AI Infrastructure
*The OS-level foundation baked into the immutable image.*

* **Task: Bake Native Ollama Engine:** Integrate the `0.21.0` native `.tar.zst` payload directly into the RedFoxOS build process.
* **Task: Configure OS-Level Services:** Create the dedicated `ollama` user, map the `/usr/lib64` library paths for NVML discovery, and bake the `ollama.service` systemd unit so it is enabled on first boot.
* **Task: LLM Environment & Anti-Wedge Tuning:** Determine and inject the optimal environment variables (e.g., `OLLAMA_NUM_CTX`) or create a custom base Modelfile to ensure the models have a sufficient context window to handle large agent tool payloads without hanging.

### Epic 2: The `redfox-ai` CLI Manager (`/usr/bin/redfox-ai`)
*A unified, standalone Python CLI utility matching the architecture of `redfox-config` and `redfox-nord`.*

* **Task: Core Telemetry & Status Engine (`redfox-ai status`):** Single-pane dashboard reporting:
    * Ollama engine systemd status, port responsiveness (11434), and version.
    * GPU/VRAM allocation (via `/dev/nvhost*` / `nvidia-smi` / ROCm discovery).
* **Task: Model Cache Management (`redfox-ai models [list|pull|rm]`):** Clean wrapper around Ollama model lifecycle, reporting quantization levels and disk usage under `/var/lib/ollama/models`.

### Epic 3: Interactive Terminal Agent: OpenCode Integration
*The human-in-the-loop developer companion: a foreground interactive agent that runs inside the terminal (Ptyxis/Tilix), paired with the developer for real-time coding, refactoring, and debugging.*

* **Task: `install-opencode` / `uninstall-opencode` Recipes:** Script the automated deployment of the OpenCode binary to `~/.local/bin/opencode` (or system layer if RPM available).
* **Task: Provider Wiring & Zero-Config Local Inference:** Pre-configure OpenCode (`~/.config/opencode/config.json`) to automatically register the local Ollama instance (`http://localhost:11434/v1`) as a default offline model provider.
* **Task: Secret Integration:** Allow OpenCode to transparently source cloud model API keys (OpenAI, Anthropic, OpenRouter) stored in `~/.config/redfox/config.yaml` via `redfox-config`.
