# About

dlint checks for bad practices and wasted resources on django-specific code.

# Install

```
pip install dlint
```

# Settings

* `DLINT_IGNORED_APPS` - will ignore these apps while running the static analisys.

# TODO

* show if none of the filters or tags from a loaded library are being used
  * warning (yellow) for partially used loaded modules
  * error (red) for unused modules
* separate the print part of the command into a Report and make it an option
* add options for each check, similar to 2to3
* make it possible to create new checks
* The "resources" or "data" should all be lazy so they wont run if a check that dont use it wasnt made.
* new checks:
  * empty models.py files (not necessary till django 1.3? confirm)
