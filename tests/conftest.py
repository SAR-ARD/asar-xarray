import os

import boto3
import pytest
import requests
from requests import Response
from urllib.parse import urlparse

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
        'ASA_IMS_1PNESA20040109_194924_000000182023_00157_09730_0000.N1'] = \
        's3://ard4sar/resources/ASA_IMS_1PNESA20040109_194924_000000182023_00157_09730_0000.N1'

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

        if "s3://" in link:
            _download_s3_resource(link, resource_file)

        else:
            _download_general_resource(link, resource_file)


def _download_general_resource(resource: str, destination: str) -> None:
    response: Response = requests.get(resource, allow_redirects=True, stream=True)
    response.raise_for_status()

    with open(destination, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)


def _download_s3_resource(resource: str, destination: str) -> None:
    s3_access_key = os.getenv('S3_ACCESS_KEY')
    s3_secret_key = os.getenv('S3_SECRET_KEY')
    endpoint_url = 'https://s3.achaad.eu/'

    parsed_url = urlparse(resource)
    bucket = parsed_url.netloc
    key = parsed_url.path.lstrip('/')

    # add verify=False if working behind ZScaler
    s3 = boto3.client('s3', aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key,
                      endpoint_url=endpoint_url
                      )
    s3.download_file(bucket, key, destination)
