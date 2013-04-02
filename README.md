# About

dlint checks for bad practices and wasted resources on django-specific code.

# Install

```
pip install dlint
```

# Settings

* `DLINT_IGNORED_APPS` - will ignore these apps while running the static analisys.

# Architecture

* Lazy resources - data that is only extracted if a check that uses that data is done.
  For example initializing the template loaders and looking for all the templates
  will only happen if a check that needs the template paths runs.
* Checks - classes that will use data to check for errors and warnings on the code and
  create a DataReport object that will be used by the reporter to generate output.
* Reporters - classes that will receive the DataReport and print it in a specific format.
  Ex: StdoutReporter

                               Checks                                Reporters

   +-----------------+        +-----------------------+
   | Resources       |        | UnusedLoadedLibraries |+--+
   |-----------------|        +-----------------------+   |
   | Templates       |                                    |         +--------+    +------------+
   | PythonSources   |        +--------------+     +------+-------->+ Stdout |    | JenkinsXML |
   | AnotherResource |        | AnotherCheck ++----+                +--------+    +------------+
   +-----------------+        +--------------+

Generated with:
http://www.asciiflow.com/#Draw8391832784659153421/2106347051

When dlint is called, the defined checks are going to be executed, each one using the necessary resources.
They can execute in parallel, if performance is a problem.

After each check is complete, a DataReport object is generated with the data collected from the check.

An array of DataReports is generated and passed to each reporter. They can also execute in parallel if necessary.

# TODO

* show if none of the filters or tags from a loaded library are being used
  * warning (yellow) for partially used loaded modules
  * error (red) for unused modules
* separate the print part of the command into a Report and make it an option
* add options for each check, similar to 2to3
* make it possible to create new checks
* the "resources" or "data" should all be lazy so they wont run if a check that dont use it wasnt made.
* option to autofix the code?
* new checks:
  * empty models.py files (not necessary till django 1.3? confirm)
  * unused templatetag library - checks if a templatetag library from one of the installed
    apps are not used in any of the templates.
