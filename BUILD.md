# Build instructions for mdfusion

This project can built and uploaded to PyPi using the following commands:

```powershell
.venv\Scripts\activate
python -m build
twine upload dist\*
```

Use `build.sh` under Linux.
