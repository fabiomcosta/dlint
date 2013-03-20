# About

Dlint checks for bad practices and wasted resources on django-specific code.

# Install

```
pip install dlint
```

# TODO

* separate the print part of the command into a Report and make it an option
* add options for each check, similar to 2to3
* make it possible to create new checks
* The "resources" or "data" should all be lazy so they wont run if a check that dont use it wasnt made.
