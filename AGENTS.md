# AGENTS.md

## Branches
- **Feature branches** (`feat/*`, `fix/*`, …) are where work happens when we can help it, since people run on `unstable`. Merge them into `unstable` when they're ready, then delete them.
- **`feature/*` branches** get their own test images in CI, for testing from RedFox Hub's Feature Branches list; older ones are deleted on each push and all of them when the branch is deleted. See `docs/ci.md`.
- **`unstable`** is the integration branch. Feature branches merge into it, and docs (`docs/ROADMAP.md`, `docs/dewy.md`, and the rest) are committed to it directly. It builds the `:unstable` image; changes to `.md` files alone don't trigger a build.
- **`main`** is the stable image (`:latest`). It's protected and only changes through pull requests: normally a PR promoting `unstable`, plus Dependabot updates and hotfixes. Never push to it directly.
- **Hotfix for stable** while `unstable` has unready work: branch from `main`, open a PR into `main`, then merge `main` back into `unstable`.
- Scheduled workflows run from `main`, so changes to them take effect only once promoted.

## Backlog
`docs/ROADMAP.md` is the backlog. Dewy's bugs and wishlist go in `docs/dewy.md`.

## Prior notes and pre-existing code are drafts

Notes, backlog and roadmap entries, past chat logs, and pre-existing code (anything written before the current piece of work and not explicitly confirmed since) are drafts: ideas to look into, not decisions. Don't treat a library, format, name or approach as settled just because it appears there. Only explicit, current decisions by the project owner are settled. When unsure, ask.

## How software gets into RedFox

This is how RedFox decides what it ships or offers. What we recommend people do themselves (including Homebrew for command-line tools, and layering as a last resort) is in the user manual: `files/hub/data/manual/03-installing-apps.md`.

Before proposing where an app goes, or questioning where one already is, walk this list.

1. **Who is it for?** Everyone, or one profile?
2. **For everyone and obligatory:** bake it into the image, or put it in the required Flatpak list.
3. **Not obligatory** (offered to everyone, or for one profile), in this order:
   - a Flatpak, if a good one exists, offered through the packs (Hub's Software page, `ujust`);
   - otherwise an AppImage or binary in the user's local bin (AppImages through Gear Lever);
   - otherwise from source or an RPM. Avoid source installs: bake it into the image instead when a source install's friction and risk outweigh the cost of baking it.
4. **Layering (`rpm-ostree install`) is never the answer.** If most users could reasonably want a package, one of the routes above handles it first.
