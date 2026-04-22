# Environment snapshots

This folder is meant to hold **machine-specific** snapshots of what actually worked when loading/training models.

Suggested filenames:

- `python.txt` (output of `python -V`)
- `pip-freeze.<os>.txt` (output of `python -m pip list --format=freeze`)

Keep **separate** snapshots for separate roles (for example training on a GPU server vs inference on a laptop).
