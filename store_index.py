import os
import ssl
import time

from dotenv import load_dotenv

load_dotenv()

# Local Windows SSL workaround (not needed on Render)
if os.getenv("DISABLE_SSL_VERIFY", "").lower() in ("1", "true", "yes"):
    ssl._create_default_https_context = ssl._create_unverified_context
    os.environ["PYTHONHTTPSVERIFY"] = "0"
    try:
        import requests

        _orig = requests.Session.request

        def _insecure(self, method, url, **kwargs):
            kwargs["verify"] = False
            return _orig(self, method, url, **kwargs)

        requests.Session.request = _insecure
    except Exception:
        pass
    try:
        import httpx

        _c = httpx.Client.__init__
        _a = httpx.AsyncClient.__init__

        def _ci(self, *args, **kwargs):
            kwargs["verify"] = False
            return _c(self, *args, **kwargs)

        def _ai(self, *args, **kwargs):
            kwargs["verify"] = False
            return _a(self, *args, **kwargs)

        httpx.Client.__init__ = _ci
        httpx.AsyncClient.__init__ = _ai
    except Exception:
        pass

from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from src.helper import (
    filter_to_minimal_docs,
    get_embeddings,
    load_pdf_file,
    text_split,
)

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found.")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found.")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

index_name = os.getenv("PINECONE_INDEX_NAME", "enertech-chatbot")
dimension = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))

extracted_data = load_pdf_file(data="data/")
filter_data = filter_to_minimal_docs(extracted_data)
text_chunks = text_split(filter_data)
embeddings = get_embeddings()

pc = Pinecone(api_key=PINECONE_API_KEY)

# Recreate index so old HuggingFace MiniLM vectors are not mixed with OpenAI vectors
if pc.has_index(index_name):
    print(f"Deleting existing index '{index_name}' ...")
    pc.delete_index(index_name)
    time.sleep(5)

print(f"Creating index '{index_name}' (dim={dimension}) ...")
pc.create_index(
    name=index_name,
    dimension=dimension,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
)

# Wait until index is ready
for _ in range(30):
    desc = pc.describe_index(index_name)
    status = getattr(desc, "status", None)
    ready = False
    if isinstance(status, dict):
        ready = bool(status.get("ready"))
    else:
        ready = bool(getattr(status, "ready", False))
    if ready:
        break
    time.sleep(2)

print(f"Upserting {len(text_chunks)} chunks ...")
PineconeVectorStore.from_documents(
    documents=text_chunks,
    index_name=index_name,
    embedding=embeddings,
)
print("Done. Pinecone index is ready for Render.")
