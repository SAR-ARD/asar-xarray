# asar-xarray

Synthetic Aperture Radar (SAR) Level-1 python mapper of ESR/ASAR products.

This python library reads ESR/ASAR products and converts them into [Xarray](https://xarray.pydata.org/) data.

## Installation

### Conda

### PyPi

### Source

## Usage

### Xarray metadata structure
Below is provided the metadata structure used by asar-xarray

```
Dataset:
   Dimensions: (slant_range_time: int, azimuth_time: int)
   Coordinates:
      pixel:    (slant_range_time) int64...
   Attributes:
      antenna_elevation_pattern:
         
```


## Contribution

### Branching model

Below are listed basic contribution rules as well as description of the preferred branch system.

The development should be performed on issue branches, and new commits to the master branch should be added
using pull requests.

The project uses [semantic versioning 2.0](https://semver.org/), i.e. v\${MAJOR}.\${MINOR}.\${PATCH} (e.g. v0.1.123)

The project is configured with automatic releases on any commits to the master branch.
All the merge commits should be prepended with a tag from the list below _(e.g. "feat: Add ESR support"_):

| Tag      | Description                                                |
|----------|------------------------------------------------------------|
| feat     | New feature                                                |
| fix      | Bug fix                                                    |
| docs     | Documentation only changes                                 |
| style    | Only code style changes                                    |
| refactor | Code refactoring                                           |
| perf     | Performance improvements                                   |
| test     | Adding new or correcting existing tests                    |
| build    | Changes which modify the application build or dependencies |
| ci       | Changes to the CI/CD configuration                         |
| revert   | Previous commit reverts                                    |

### git lfs
The project uses git lfs for tracking satellite imagery. In order to use git lfs, execute 
`git lfs install`. The repository is already configured to track _.N1_ files.

If you need to track any other large files, execute `git lfs track "*.${extension}"`.

### flak8 documentation

The project actively uses flake8 for documentation and code style checking. Before pushing the changes,
it is highly recommended to run:
```bash

pip install flake8 flake8-docstrings
flake8 .
```
The repository is configured to run flake8 checks on every commit. If the code style is not correct, the commit will be rejected.

If using Pycharm for development, use of _flake8-for-pycharm_ plugin is recommended. Installation instructions can be 
found 
[here](https://pypi.org/project/flake8-for-pycharm/).

### Issue tracking
When the development on the issue begins, tag _In progress_ should be added to it.

## Maintainers:

- Anton Perepelenko (anton.perepelenko@cgi.com)
- Priit Pender (priit@alloca.ee)

## Funding:

The initial development of the project was funded by the European Space Agency.