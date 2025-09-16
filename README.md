# geografir
Testing GitHub Integration
A collection of Python helpers primarily targeted toward geospatial recipes.

- `geometry` ([🔗](https://github.com/Vibrant-Planet/geografir/tree/main/geometry)) - Classes for representing geospatial shapes.
- `raster_array` ([🔗](https://github.com/Vibrant-Planet/geografir/tree/main/raster_array)) - Geospatial numpy arrays.
- `object_storage` ([🔗](https://github.com/Vibrant-Planet/geografir/tree/main/object_storageg)) - Helpers for interacting with objects stored on S3.

> [!WARNING]
> These packages are under heavy active development and can only be installed via GitHub.

## Getting Started

Install individual packages directly from GitHub with this pattern `git+https://github.com/Vibrant-Planet/geografir.git#subdirectory=<package name>`

```shell
# install object_storage with pip
pip install git+https://github.com/Vibrant-Planet/geografir.git#subdirectory=object_storage

# install object_storage with uv
uv add git+https://github.com/Vibrant-Planet/geografir.git#subdirectory=object_storage
```

## Contributing

Contribute to this project by cloning the repo, following the instructions below, then submitting a PR.

```shell
# 1. clone repo
git clone git@github.com:Vibrant-Planet/geografir.git
cd geografir

# 2. Install uv: https://docs.astral.sh/uv/#installation
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install pre-commit
uvx pre-commit install

# 4. Install dependencies
uv sync --dev

# 5. verify everything is working as it should
uv run pre-commit run --all-files
```

## Add a new package to be published out of this repo

This repository publishes multiple library packages. To add a new one, run these commands.

```shell
uv init --lib my_new_library_package
```

Add dependencies for just that package with the following (`pydantic` is an example dependency):
```shell
uv add --package my_new_library_package pydantic
```
