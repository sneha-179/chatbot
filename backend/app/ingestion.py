import os
import json
import PyPDF2
import requests
from chromadb import PersistentClient
from dotenv import load_dotenv
import pytesseract
from pdf2image import convert_from_path

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

FAQ_PATH = os.path.join(os.path.dirname(__file__), "faqs.json")
KB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base")
CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_store")


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\path\to\poppler\bin"


def get_collection():
    """Open the persistent Chroma collection used by ingestion and retrieval."""
    client = PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(name="company_docs")


def embed_text(text, task_type="RETRIEVAL_DOCUMENT"):
    """Create a Gemini embedding for either a document or a user query."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-embedding-001:embedContent?key={GOOGLE_API_KEY}"
    )
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": text}]},
        "taskType": task_type
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["embedding"]["values"]


def _recursive_split(text: str, max_size: int, separators: list[str]) -> list[str]:
    """Split oversized text using progressively smaller separators."""
    if len(text) <= max_size:
        return [text] if text.strip() else []

    if not separators:
        return [text[i:i + max_size] for i in range(0, len(text), max_size)]

    separator = separators[0]
    remaining_separators = separators[1:]

    pieces = text.split(separator) if separator else list(text)

    chunks = []
    current = ""

    for piece in pieces:
        candidate = current + separator + piece if current else piece

        if len(candidate) <= max_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(piece) > max_size:
                chunks.extend(_recursive_split(piece, max_size, remaining_separators))
                current = ""
            else:
                current = piece

    if current:
        chunks.append(current)

    return chunks


def chunk_text(text, source=""):
    """Create overlapping chunks so retrieval keeps context across boundaries."""
    separators = ["\n\n", "\n", ". ", " "]
    raw_chunks = _recursive_split(text, CHUNK_SIZE, separators)

    chunks = []
    for i, chunk in enumerate(raw_chunks):
        chunk = chunk.strip()
        if not chunk:
            continue
        if i > 0 and CHUNK_OVERLAP > 0:
            prev_tail = raw_chunks[i - 1][-CHUNK_OVERLAP:]
            chunk = prev_tail.strip() + " " + chunk
        chunks.append(chunk)

    ids = [f"{source}_chunk_{i}" for i in range(len(chunks))]
    return chunks, ids



def is_scanned_pdf(text: str, min_chars_per_page: int = 20) -> bool:
    """Treat nearly empty extracted text as a signal that the PDF needs OCR."""
    return len(text.strip()) < min_chars_per_page


def extract_text_with_ocr(filepath: str) -> str:
    """Extract text from image-only PDF pages using Tesseract and Poppler."""
    print(f"[OCR] Running OCR on {filepath} (no text layer found)")
    images = convert_from_path(filepath, poppler_path=POPPLER_PATH)

    full_text = ""
    for i, image in enumerate(images):
        page_text = pytesseract.image_to_string(image)
        full_text += page_text + "\n"
        print(f"[OCR] Page {i+1}/{len(images)} processed")

    return full_text.strip()


def extract_pdf_text(filepath):
    """Read a PDF text layer and fall back to OCR when it is not available."""
    text = ""
    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    text = text.strip()

    if is_scanned_pdf(text):
        text = extract_text_with_ocr(filepath)

    return text

def extract_text_generic(filepath):
    """Choose the PDF extractor or the UTF-8 text reader based on file type."""
    if filepath.endswith(".pdf"):
        return extract_pdf_text(filepath)
    else:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()

        
def index_pdf(filepath, role_required="general", category="general"):
    """Embed and store one knowledge-base file unless it is already indexed."""
    collection = get_collection()
    filename = os.path.basename(filepath)
    existing = collection.get(where={"source": filename})
    if existing["ids"]:
        print(f"[Ingestion] Already indexed: {filename}, skipping")
        return
    text = extract_text_generic(filepath)
    if not text:
        print(f"[Ingestion] No text found in {filename}")
        return
    chunks, ids = chunk_text(text, source=filename)
    vectors = [embed_text(c) for c in chunks]
    metadatas = [
        {"source": filename, "chunk_index": i, "role_required": role_required, "category": category}
        for i in range(len(chunks))
    ]
    collection.add(documents=chunks, embeddings=vectors, ids=ids, metadatas=metadatas)
    print(f"[Ingestion] Indexed {len(chunks)} chunks from {filename} (role: {role_required}, category: {category})")

FILENAME_CATEGORY_MAP = {
    "login_issues": "login",
    "vpn_troubleshooting": "network",
    "payslip_download": "payroll",
    "software_access": "software"
}

def _guess_category(filename: str) -> str:
    """Infer a retrieval category from the conventional knowledge-base filename."""
    lower = filename.lower()
    for key, category in FILENAME_CATEGORY_MAP.items():
        if key in lower:
            return category
    return "general"

def index_faqs():
    """Embed FAQ records once and retain their role metadata for access control."""
    collection = get_collection()
    existing = collection.get(where={"source": "faqs.json"})
    if existing["ids"]:
        print("[Ingestion] FAQs already indexed, skipping")
        return
    with open(FAQ_PATH, "r") as f:
        faqs = json.load(f)
    docs, ids, vectors, metadatas = [], [], [], []
    for faq in faqs:
        text = f"Question: {faq['question']}\nAnswer: {faq['answer']}"
        docs.append(text)
        ids.append(faq["id"])
        vectors.append(embed_text(text))
        metadatas.append({
            "source": "faqs.json",
            "question": faq["question"],
            "role_required": faq.get("role_required", "general")
        })
    collection.add(documents=docs, embeddings=vectors, ids=ids, metadatas=metadatas)
    print(f"[Ingestion] Indexed {len(faqs)} FAQs")


def index_all_existing_pdfs():
    """Index supported files currently present in the knowledge-base directory."""
    if not os.path.exists(KB_PATH):
        return
    for filename in os.listdir(KB_PATH):
        if filename.endswith(".pdf") or filename.endswith(".md"):
            role = "hr" if filename.startswith("HR_") else "general"
            category = _guess_category(filename)
            index_pdf(os.path.join(KB_PATH, filename), role_required=role, category=category)


def run_startup_indexing():
    """Run the complete startup ingestion sequence."""
    print("[Ingestion] Starting knowledge base indexing...")
    index_faqs()
    index_all_existing_pdfs()
    print("[Ingestion] Done!")