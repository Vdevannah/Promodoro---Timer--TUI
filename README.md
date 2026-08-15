# Pip Modules Lab

### Prerequisite 

* [Python Fundamentals Exercise 9](https://github.com/Zipcoder/PythonFundamentals.Exercises.Part9)
* [NOAA Daily Summaries](https://github.com/Zipcoder/DataEngineering.Labs.NOAADailySummaries)

### Reference

* [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)

### Part 1

* Create the following file structure:

```
json_helper/
    json_helper/
        __init__.py
        json_to_pandas.py
    setup.py
    LICENSE.rst
    README.md
```
* Use the logic from the json_helper module created in the NOAA Daily Summaries lab to fill in json_to_pandas.py.

* Open __init__.py file and add the following:

```python
from . import json_to_pandas
```

By doing so, whenever the json_helper module is imported, it will automatically import the functionality from json_to_pandas.
If we don't do this, the user will have to manually import the module like so:

```python
from json_helper import json_to_pandas
```

* Following the example from the [packaging projects documentation](https://packaging.python.org/tutorials/packaging-projects/#creating-setup-py), setup the file setup.py.

* Add information to your README.md file. See the [docs](https://packaging.python.org/tutorials/packaging-projects/#creating-readme-md) for details.

* Install the package using pip (locally)

Open a terminal and cd into the directory containing the setup.py file.

```
pip install .
```
* Validate that the module works as expected.

We can now use this module in any of our notebooks with a simple import.
