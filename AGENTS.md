# AGENTS.md

## Branches
- **`unstable`** is where work lands, including all docs (`docs/ROADMAP.md`, `docs/dewy.md`, and the rest). It builds the `:unstable` image; changes to `.md` files alone don't trigger a build.
- **`main`** is the stable image (`:latest`). It's protected and only changes through pull requests: normally a PR promoting `unstable`, plus Dependabot updates and hotfixes. Never push to it directly.
- **Hotfix for stable** while `unstable` has unready work: branch from `main`, open a PR into `main`, then merge `main` back into `unstable`.
- Scheduled workflows run from `main`, so changes to them take effect only once promoted.

## Backlog
`docs/ROADMAP.md` is the backlog. Dewy's bugs and wishlist go in `docs/dewy.md`.
