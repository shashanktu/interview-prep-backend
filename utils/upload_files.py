from fastapi import FastAPI, UploadFile, File, HTTPException
from azure.storage.blob import BlobClient
from urllib.parse import urlparse
from utils.config import CONTAINER_SAS_URL

app = FastAPI()


# @app.post("/upload")
async def upload_blob(file,folder_name):

    try:
        if not CONTAINER_SAS_URL:
            raise HTTPException(
                status_code=500,
                detail="AZURE_CONTAINER_SAS_URL is not configured"
            )

        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is missing"
            )
        #replace spaces with underscores
        filename = file.filename.lower().replace(" ", "_")
        
        # Also sanitize folder_name
        folder_name = folder_name.replace(" ", "_")
        # Generate unique filename
        blob_name = f"{folder_name}/{filename}"

        # --------------------------------------------------
        # IMPORTANT:
        # Container SAS URL already contains the SAS token.
        # We append the blob name BEFORE the ?.
        # --------------------------------------------------

        parsed = urlparse(CONTAINER_SAS_URL)

        blob_url = (
            f"{parsed.scheme}://"
            f"{parsed.netloc}"
            f"{parsed.path.rstrip('/')}/"
            f"{blob_name}"
            f"?{parsed.query}"
        )

        print("Uploading to:", blob_url)

        # Create BlobClient directly from complete SAS URL
        blob_client = BlobClient.from_blob_url(blob_url)

        # Upload
        await file.seek(0)

        blob_client.upload_blob(
            file.file,
            overwrite=True
        )

        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "blob_name": blob_name,
            "url": blob_url
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )