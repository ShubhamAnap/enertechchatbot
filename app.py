import os

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from src.helper import get_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from src.prompt import *


app = Flask(__name__)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]
WIDGET_API_KEY = os.getenv("WIDGET_API_KEY", "").strip()
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "enertech-chatbot")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found.")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found.")

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ALLOWED_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-Widget-Key"],
        }
    },
)

embeddings = get_embeddings()

docsearch = PineconeVectorStore.from_existing_index(
    index_name=INDEX_NAME,
    embedding=embeddings,
)

retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})

chatModel = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(chatModel, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)


def _get_message_from_request():
    if request.is_json:
        data = request.get_json(silent=True) or {}
        return (data.get("message") or data.get("msg") or "").strip()
    return (request.form.get("msg") or request.args.get("msg") or "").strip()


def _authorize_widget_request():
    if not WIDGET_API_KEY:
        return True
    provided = (
        request.headers.get("X-Widget-Key")
        or (request.get_json(silent=True) or {}).get("api_key")
        or request.args.get("api_key")
        or ""
    ).strip()
    return provided == WIDGET_API_KEY


def _run_chat(msg: str):
    response = rag_chain.invoke({"input": msg})
    return str(response["answer"])


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/embed")
def embed():
    """Iframe-friendly chat page for embedding on any website."""
    return render_template("embed.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "enertech-chatbot"})


@app.route("/api/chat", methods=["POST", "OPTIONS"])
def api_chat():
    """JSON chat API for the embeddable widget and third-party sites."""
    if request.method == "OPTIONS":
        return ("", 204)

    if not _authorize_widget_request():
        return jsonify({"error": "Unauthorized. Invalid or missing widget API key."}), 401

    msg = _get_message_from_request()
    if not msg:
        return jsonify({"error": "Message is required. Send JSON: {\"message\": \"...\"}"}), 400

    try:
        answer = _run_chat(msg)
        return jsonify({"answer": answer, "message": msg})
    except Exception as exc:
        import traceback

        print("Chat error:", exc)
        traceback.print_exc()
        return jsonify({"error": "Sorry, something went wrong. Please try again."}), 500


@app.route("/get", methods=["GET", "POST"])
def chat():
    msg = request.form.get("msg") or request.args.get("msg") or ""
    if not msg.strip():
        return "Please type a message.", 400
    print(msg)
    answer = _run_chat(msg)
    print("Response : ", answer)
    return answer


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=debug)
