# CI image builds

All builds use BlueBuild with the three recipes (`recipe-main.yml`, `recipe-nvidia.yml`, `recipe-nvidia-legacy.yml`), and every image is signed.

| Workflow | Builds | Tags |
|---|---|---|
| `build.yml` | pushes to `main`, daily at 06:00 UTC, PRs into `main` | `latest`, dated, `<sha7>-<fedora>`; PRs `pr-<n>-<fedora>` |
| `build-unstable.yml` | pushes to `unstable`, daily (dispatched by `schedule-unstable.yml`), PRs into `unstable` | `unstable`, `br-unstable-<fedora>`, `<sha7>-<fedora>`; PRs `pr-<n>-<fedora>` |
| `build-feature.yml` | pushes to `feature/**` branches (no daily rebuild) | `br-<branch, / as _>-<fedora>`, `fb-<branch>-<sha7>-<fedora>` |
| `build-iso.yml` | after each successful `main` build, and by hand | ISO artifacts (see `iso.md`) |

Pushes that change only `.md` files don't build.

## Feature branch images

A branch named `feature/…` gets test images that RedFox Hub lists under Updates › Advanced › Feature Branches (and `ujust rollback-helper branches`). The Hub finds them by the `br-<branch>-<fedora>` tag and describes each one by the first line of a `.redfox-branch` file in the branch, or else its latest commit's subject. Open, non-draft PRs into `unstable` are listed too, from their `pr-<n>-<fedora>` builds. Other branch names (`feat/…`, `fix/…`) don't build an image of their own.

Each build takes about 9 minutes and roughly 7 GB of registry space, so only the newest build of each branch is kept:

- After a build, the workflow tags it `fb-<branch>-<sha7>-<fedora>` (so older builds can still be found once `br-…` has moved on) and deletes the branch's older builds of that image.
- `cleanup-feature.yml` deletes all of a branch's images when the branch is deleted. GitHub runs `delete` workflows from `main`, so this only works once it's been promoted there.

Deleting a build removes its image index, its child manifests and their cosign signature and attestation tags. A build that also carries some other tag (`latest`, `unstable`, a date, a PR tag) is never deleted. The deletion is done by `.github/scripts/feature-images.sh` with the workflow's `GITHUB_TOKEN` (`packages: write`), which needs the repository to have admin access to the packages (the default for packages it published).
