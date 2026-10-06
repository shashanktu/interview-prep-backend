import pymupdf as fitz
from azure.storage.blob import BlobClient

def extract_pdf_text(blob_url: str) -> str:

    blob_client = BlobClient.from_blob_url(blob_url)

    pdf_bytes = blob_client.download_blob().readall()

    pdf = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    text = ""

    for page in pdf:
        text += page.get_text()

    pdf.close()

    return text

