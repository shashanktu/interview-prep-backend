from azure.storage.blob import ContainerClient
from urllib.parse import urlparse

# from utils.config import CONTAINER_SAS_URL
CONTAINER_SAS_URL = "https://devopsmafsa.blob.core.windows.net/agents?sp=racwl&st=2026-09-02T06:52:04Z&se=2027-02-04T15:07:04Z&spr=https&sv=2026-02-06&sr=c&sig=J5alsvFOMXahFhJd4HRVC2Ck95HpUpJ5XZlrtbnQOAc%3D"


from azure.storage.blob import ContainerClient
from urllib.parse import urlparse

def get_files_from_blob(folder_path: str):

    container_client = ContainerClient.from_container_url(
        CONTAINER_SAS_URL
    )

    # Extract the base container URL without the SAS token query parameters
    parsed_url = urlparse(CONTAINER_SAS_URL)
    base_container_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    
    # Extract the SAS token query string (e.g., "?sv=2021-08-06&ss=b...")
    sas_token = parsed_url.query

    files = []

    for blob in container_client.list_blobs(
        name_starts_with=folder_path
    ):
        # 1. Build the clean, permanent URL of the file
        full_url = f"{base_container_url}/{blob.name}"
        
        # 2. Build the authenticated URL (if you need people to actually download it right now)
        authenticated_url = f"{full_url}?{sas_token}" if sas_token else full_url

        files.append({
            "file_name": blob.name.split("/")[-1],
            "blob_path": blob.name,
            "url": authenticated_url  # Or use 'full_url' depending on your authorization needs
        })

    return files




# def get_files_from_blob(folder_path: str):

#     container_client = ContainerClient.from_container_url(
#         CONTAINER_SAS_URL
#     )

#     files = []

#     for blob in container_client.list_blobs(
#         name_starts_with=folder_path
#     ):
#         print(vars(blob))
#         files.append({
#             "file_name": blob.name.split("/")[-1],
#             "blob_path": blob.name,
#             "url": f"{blob}"
#         })

#     return files
