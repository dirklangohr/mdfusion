# first, bump the version in pyproject.toml manually! Then:
source ./venv/bin/activate
python -m build
twine upload dist/*