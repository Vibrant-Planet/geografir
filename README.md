# geografir
A collection of Python helpers primarily targeted toward geospatial recipes

## Getting Started

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
