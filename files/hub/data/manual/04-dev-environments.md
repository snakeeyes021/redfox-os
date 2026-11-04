# Shared dev environments

To give a whole team the same tools, such as one exact Node version, put the project in a dev container.

## Dev containers

A dev container is a container described by a file in the project, `.devcontainer/devcontainer.json`. VS Code opens the project inside it, so everyone who opens the project gets the same operating system, the same Node and the same tools, on RedFoxOS, macOS or Windows alike. Nothing is installed on your own system.

RedFoxOS comes ready for this: **VS Code**, **Docker** and **Podman** are in the image, and VS Code's **Dev Containers** extension is installed the first time you log in.

## Set one up

1. Open the project folder in VS Code.
2. Press `Ctrl+Shift+P` and run **Dev Containers: Add Dev Container Configuration Files**.
3. Pick **Node.js & TypeScript** (or another starting point), then the Node version.
4. Run **Dev Containers: Reopen in Container**. The first start downloads the image; later starts are quick.
5. Commit the `.devcontainer` folder, so your collaborators get the same setup.

The Node version is the image tag in `devcontainer.json`, for example `mcr.microsoft.com/devcontainers/typescript-node:22`. Change the tag and rebuild to move everyone to a new version at once.

Collaborators need Docker (or Podman) and VS Code with the Dev Containers extension. When they open the project, VS Code offers to reopen it in the container.

## If Docker says "permission denied"

Your account is added to the `docker` group when RedFoxOS first starts. Log out and back in once for it to take effect. To check:

```sh
docker run --rm hello-world
```

## Distrobox, for your own setup

If you only need a fixed toolset for yourself, a Distrobox is simpler: a long-lived container that shares your home folder. See [Installing apps](manual:installing-apps).

```sh
distrobox create --name dev --image ubuntu:24.04
distrobox enter dev
```

Inside it, install the Node version you need with that system's packages or a version manager. It stays separate from everything else on the machine. For a team, prefer dev containers: the setup lives in the project, not on each person's machine.
