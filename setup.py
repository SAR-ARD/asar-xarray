import setuptools

setuptools.setup(
    name="asar_xarray",
    version="0.0.1",
    python_requires=">=3.6",
    packages=['asar_xarray'],
    install_requires=[],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'tox>=4.23.2', 'coverage>=7.6.9'],
    test_suite='tests',
)
