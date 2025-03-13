import os

import pytest
import requests
from requests import Response


@pytest.fixture(scope='session')
def resources_dir() -> str:
    """
    Provides path to test resources' directory.
    :return: Path to test resources' directory.
    """
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')


@pytest.fixture(scope='session')
def external_resources() -> dict[str, str]:
    """
    Prepares dictionary of external resources.

    :return: Dictionary where keys are external resource names and values are external resource links.
    """
    resources: dict[str, str] = dict()
    resources[
        'ASA_IMS_1PNESA20040109_194924_000000182023_00157_09730_0000'] = 'https://drive.google.com/file/d/1BShsExnfM9o38KRZRQ1SvJXxbh2OGuHw/view?usp=drive_link'

    return resources


@pytest.fixture(scope='session', autouse=True)
def download_resources(external_resources: dict[str, str], resources_dir: str) -> None:
    """
    Downloads necessary external test resources.

    :param external_resources: Fixture with a dictionary of external test resources.
    :param resources_dir: Fixture specifying where to download resources.
    :return: None.
    """
    for resource, link in external_resources.items():
        resource_file = os.path.join(resources_dir, resource)
        if os.path.exists(resource_file):
            continue

        response: Response = requests.get(link, allow_redirects=True, stream=True)
        response.raise_for_status()

        with open(resource_file, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
