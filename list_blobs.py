from azure.storage.blob import ContainerClient
from urllib.parse import urlparse
# load env file
from dotenv import load_dotenv

load_dotenv()
import os

CONTAINER_SAS_URL=os.getenv("CONTAINER_SAS_URL")
# from utils.config import CONTAINER_SAS_URL

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


from azure.storage.blob import ContainerClient


def find_blob_url(file_name: str) -> str | None:
    # sas_url must be the container URL with its SAS token
    container_client = ContainerClient.from_container_url(CONTAINER_SAS_URL)

    for blob in container_client.list_blobs():
        # Match the filename, including files inside folders
        if blob.name.split("/")[-1] == file_name:
            blob_client = container_client.get_blob_client(blob.name)

            # Return the complete URL, including the SAS token
            return blob_client.url

    return None



# print(CONTAINER_SAS_URL)
# url = find_blob_url(
#     sas_url=CONTAINER_SAS_URL,
#     file_name="AI Solutions Architect JD.docx"
# )

# if url:
#     print("Blob SAS URL:", url)
# else:
#     print("File not found")