import os

import pytest


@pytest.fixture(scope='session')
def resources_dir():
    """
    Provides path to test resources directory.
    :return: Path to test resources directory
    """
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
