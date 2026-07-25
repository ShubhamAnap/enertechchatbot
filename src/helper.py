import os
from typing import List

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def _ensure_ca_bundle():
    """Point SSL libs at certifi for OpenAI / Pinecone on Linux (Render)."""
    try:
        import certifi

        ca = certifi.where()
        os.environ.setdefault("SSL_CERT_FILE", ca)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", ca)
        os.environ.setdefault("CURL_CA_BUNDLE", ca)
    except Exception:
        pass


def _maybe_disable_ssl_verify():
    """
    Local-only workaround for corporate SSL inspection (Windows).
    Do NOT set DISABLE_SSL_VERIFY on Render.
    """
    flag = os.getenv("DISABLE_SSL_VERIFY", "").lower()
    if flag not in ("1", "true", "yes"):
        _ensure_ca_bundle()
        return

    import ssl

    ssl._create_default_https_context = ssl._create_unverified_context
    os.environ["PYTHONHTTPSVERIFY"] = "0"
    _ensure_ca_bundle()

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


_maybe_disable_ssl_verify()


def load_pdf_file(data):
    loader = DirectoryLoader(data, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    return documents


def filter_to_minimal_docs(docs: List[Document]) -> List[Document]:
    minimal_docs: List[Document] = []
    for doc in docs:
        src = doc.metadata.get("source")
        minimal_docs.append(
            Document(page_content=doc.page_content, metadata={"source": src})
        )
    return minimal_docs


def text_split(extracted_data):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    text_chunks = text_splitter.split_documents(extracted_data)
    return text_chunks


def get_embeddings():
    """
    OpenAI embeddings (384-dim) — no HuggingFace model download.
    Works reliably on Render.
    """
    _maybe_disable_ssl_verify()
    return OpenAIEmbeddings(
        model=os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small"),
        dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "384")),
    )


# Backwards-compatible alias used by older scripts
def download_hugging_face_embeddings():
    return get_embeddings()
