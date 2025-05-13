from typing import Any

from osgeo import gdal


def process_derived_subdatasets_metadata(dataset: gdal.Dataset, attributes: dict[str, Any]) -> None:
    """
    Process derived subdatasets metadata from GDAL dataset.

    :param dataset: GDAL dataset containing derived subdatasets metadata.
    :param attributes: Dictionary to store the processed metadata. The 'derived_subdatasets' key will be populated
                       with a list of dictionaries, each representing a subdataset with the following keys:
                       - 'operation': The operation type (e.g., amplitude, phase, etc.).
                       - 'filepath': The file path associated with the subdataset.
                       - 'description': A textual description of the subdataset.
    """
    # Retrieve metadata from the 'DERIVED_SUBDATASETS' domain of the dataset
    metadata = dataset.GetMetadata(domain='DERIVED_SUBDATASETS')
    # Initialize the 'derived_subdatasets' key in the attributes dictionary
    attributes['derived_subdatasets'] = {}

    # Temporary dictionary to store subdataset information by index
    subdatasets = {}
    for key, value in metadata.items():
        # Split the metadata key to extract the index and type (NAME or DESC)
        parts = key.split('_')
        idx = int(parts[2])  # Extract the numeric index
        field_type = parts[3]  # Extract the field type (NAME or DESC)

        # Initialize a dictionary for the current index if not already present
        if idx not in subdatasets:
            subdatasets[idx] = {}

        if field_type == 'NAME':
            # Split the NAME value to extract operation type and file path
            parts = value.split(':', 2)  # Split into at most 3 parts
            subdatasets[idx]['operation'] = parts[1].lower()  # Convert operation to lowercase
            subdatasets[idx]['filepath'] = parts[2]  # Extract the file path
        else:  # If the field type is DESC
            subdatasets[idx]['description'] = value  # Store the description

    # Convert the subdatasets dictionary to a sorted list by index
    attributes['derived_subdatasets'] = [
        subdatasets[idx] for idx in sorted(subdatasets.keys())
    ]
