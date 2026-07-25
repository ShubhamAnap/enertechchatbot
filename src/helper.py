import os
from typing import List

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def _maybe_disable_ssl_verify():
    """Allow model downloads behind corporate SSL inspection."""
    flag = os.getenv("DISABLE_SSL_VERIFY", "").lower()
    if flag not in ("1", "true", "yes"):
        return

    import ssl

    ssl._create_default_https_context = ssl._create_unverified_context
    os.environ["CURL_CA_BUNDLE"] = ""
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    os.environ["SSL_CERT_FILE"] = ""
    os.environ["PYTHONHTTPSVERIFY"] = "0"

    try:
        import urllib3
        import urllib3.util.ssl_ as urllib3_ssl
        from urllib3 import PoolManager

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        _orig_create_ctx = urllib3_ssl.create_urllib3_context

        def _insecure_create_urllib3_context(*args, **kwargs):
            ctx = _orig_create_ctx(*args, **kwargs)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx

        urllib3_ssl.create_urllib3_context = _insecure_create_urllib3_context

        _orig_pool_init = PoolManager.__init__

        def _insecure_pool_init(self, *args, **kwargs):
            kwargs["cert_reqs"] = "CERT_NONE"
            kwargs["assert_hostname"] = False
            kwargs["assert_fingerprint"] = None
            kwargs.pop("ca_certs", None)
            kwargs.pop("ca_cert_dir", None)
            kwargs.pop("ssl_context", None)
            return _orig_pool_init(self, *args, **kwargs)

        PoolManager.__init__ = _insecure_pool_init
    except Exception:
        pass

    try:
        import requests
        from huggingface_hub import configure_http_backend

        _original_request = requests.Session.request

        def _insecure_request(self, method, url, **kwargs):
            kwargs["verify"] = False
            return _original_request(self, method, url, **kwargs)

        requests.Session.request = _insecure_request

        def _backend_factory():
            session = requests.Session()
            session.verify = False
            return session

        configure_http_backend(backend_factory=_backend_factory)
    except Exception:
        pass

    try:
        import httpx

        _orig_httpx_client_init = httpx.Client.__init__
        _orig_httpx_async_init = httpx.AsyncClient.__init__

        def _insecure_httpx_client_init(self, *args, **kwargs):
            kwargs["verify"] = False
            return _orig_httpx_client_init(self, *args, **kwargs)

        def _insecure_httpx_async_init(self, *args, **kwargs):
            kwargs["verify"] = False
            return _orig_httpx_async_init(self, *args, **kwargs)

        httpx.Client.__init__ = _insecure_httpx_client_init
        httpx.AsyncClient.__init__ = _insecure_httpx_async_init
    except Exception:
        pass


# Apply early when helper is imported after dotenv is loaded by callers.
_maybe_disable_ssl_verify()


# Extract Data From the PDF File
def load_pdf_file(data):
    loader = DirectoryLoader(data, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    return documents


def filter_to_minimal_docs(docs: List[Document]) -> List[Document]:
    """
    Given a list of Document objects, return a new list of Document objects
    containing only 'source' in metadata and the original page_content.
    """
    minimal_docs: List[Document] = []
    for doc in docs:
        src = doc.metadata.get("source")
        minimal_docs.append(
            Document(page_content=doc.page_content, metadata={"source": src})
        )
    return minimal_docs


# Split the Data into Text Chunks
def text_split(extracted_data):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    text_chunks = text_splitter.split_documents(extracted_data)
    return text_chunks


# Download the Embeddings from HuggingFace (384 dimensions)
def download_hugging_face_embeddings():
    _maybe_disable_ssl_verify()
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    return embeddings