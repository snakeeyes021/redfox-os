# Python

Use uv for Python projects and pixi for conda-style ones; both come with RedFoxOS.

## Why not pip?

The system's own Python is part of the read-only image, and RedFoxOS's tools rely on it. `pip install` into it doesn't work, and `sudo pip` can't change it either. Give each project its own environment instead. **uv** and **pixi** are preinstalled for that, and update with the system.

## uv: Python projects

[uv](https://docs.astral.sh/uv/) makes and manages virtual environments, installs packages and fetches Python versions. Start a project:

```sh
uv init myproject
cd myproject
uv add requests
uv run main.py
```

`uv add` records the package in `pyproject.toml` and the exact versions in `uv.lock`. Commit both, and `uv sync` gives anyone the same environment.

A specific Python version, for this project only:

```sh
uv python pin 3.12
```

A plain virtual environment in the current folder, for scripts that expect one:

```sh
uv venv
uv pip install numpy
```

A command-line tool written in Python, installed for you alone:

```sh
uv tool install ruff
```

A one-off script with a package it needs, without setting anything up:

```sh
uv run --with rich script.py
```

## pixi: conda-style projects

[pixi](https://pixi.sh) installs packages from conda-forge, including non-Python ones such as compilers, CUDA libraries or R. Use it when a project's instructions say `conda`, or when you need libraries pip can't provide.

```sh
pixi init myproject
cd myproject
pixi add python=3.12 numpy
pixi run python
```

Tools installed with `pixi global install` go in `~/.pixi/bin`, which is already on your `PATH`.

## In a dev container

For a team project, a dev container pins Python as firmly as Node. See [Shared dev environments](manual:dev-environments).
