# Contributing to ObjTables

We enthusiastically welcome contributions to ObjTables!

## Coordinating contributions

Before getting started, please contact the lead developers at info@objtables.org to coordinate your planned contributions with other ongoing efforts. Please also use GitHub issues to announce your plans to the community so that other developers can provide input into your plans and coordinate their own work. As the development community grows, we will institute additional infrastructure as needed such as a leadership committee and regular online meetings.

## Repository organization

ObjTables follows standard Python conventions:

* `obj_tables/`: source code
* `tests/`: tests
* `docs/`: documentation
* `setup.py`: installation script

## Coding convention

ObjTables follows standard Python style conventions:

* Module names: `lower_snake_case`
* Class names: `UpperCamelCase`
* Function names: `lower_snake_case`
* Variable names: `lower_snake_case`

## Testing

We strive to have complete test coverage of ObjTables. As such, all contributions to ObjTables should be tested. The tests are located in the `tests` subdirectory. The tests are implemented using the `unittest` module. The tests can be executed by running `pytest tests`.

Upon each push to GitHub, GitHub will trigger CircleCI to execute all of the tests.

## Documentation convention

ObjTables is documented using the napoleon Sphinx plugin. The documentation can be compiled by running `sphinx-build docs docs/_build/html`.

## Submitting changes

Please use GitHub pull requests to submit changes. Each request should include a brief description of the new and/or modified features.

## Releasing and deploying new versions

Contact info@objtables.org to request release and deployment of new changes. 