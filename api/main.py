"""FastAPI application — recipe service."""
import os
from contextlib import asynccontextmanager

import spacy
import weaviate
from neo4j import GraphDatabase
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel

from .deps import get_embedder, get_generator, get_nlp, get_session, get_weaviate
from .kg import wrap_kg_query, SUPPORTED_PATTERNS
from .kg import UnsupportedQueryError
from .m8_rag import load_generator
from .models import (
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    KGRequest,
    KGResponse,
    RAGRequest,
    RAGResponse,
    ReadyDetail,
    UnsupportedQueryDetail,
)
from .nlp import extract_entities
from .rag import compose_rag
from .auth import (
    authenticate_user,
    create_access_token,
    verify_api_key_or_jwt,
    verify_jwt_only,
)


class LoginRequest(BaseModel):
    username: str
    password: str


WEB_ORIGIN = os.environ.get("WEB_ORIGIN", "http://localhost:3000")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@asynccontextmanager
async def lifespan(app: FastAPI):
    neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "password")
    weaviate_url = os.environ.get("WEAVIATE_URL", "http://localhost:8080")

    app.state.neo4j_driver = GraphDatabase.driver(
        neo4j_uri, auth=(neo4j_user, neo4j_password)
    )
    app.state.weaviate_client = weaviate.Client(weaviate_url)
    app.state.nlp = spacy.load("en_core_web_sm")
    app.state.generator = load_generator()
    app.state.embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

    yield

    app.state.neo4j_driver.close()


app = FastAPI(title="M10 Recipe Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[WEB_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/auth/login")
def login(req: LoginRequest):
    if not authenticate_user(req.username, req.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(subject=req.username)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/admin/echo")
def admin_echo(payload: dict = Depends(verify_jwt_only)):
    return payload


@app.post("/extract", response_model=ExtractResponse)
def extract(
    req: ExtractRequest,
    nlp=Depends(get_nlp),
    _auth=Depends(verify_api_key_or_jwt),
) -> ExtractResponse:
    entities = extract_entities(req.text, nlp)
    return ExtractResponse(entities=entities)


@app.post("/kg/query", response_model=KGResponse)
def kg_query(
    req: KGRequest,
    session=Depends(get_session),
    _auth=Depends(verify_api_key_or_jwt),
) -> KGResponse:
    try:
        cypher, params = wrap_kg_query(req.question)
    except UnsupportedQueryError as exc:
        patterns = (
            getattr(exc, "supported_patterns", None)
            or getattr(exc, "patterns", None)
            or SUPPORTED_PATTERNS
        )
        detail = UnsupportedQueryDetail(
            reason="unsupported_question",
            supported_patterns=list(patterns),
        )
        raise HTTPException(status_code=422, detail=detail.model_dump())

    result = session.run(cypher, **params)
    rows = [record.data() for record in result]
    return KGResponse(cypher=cypher, rows=rows, count=len(rows))


@app.post("/rag/answer", response_model=RAGResponse)
def rag_answer(
    req: RAGRequest,
    weaviate_client=Depends(get_weaviate),
    generator=Depends(get_generator),
    embedder=Depends(get_embedder),
    _auth=Depends(verify_api_key_or_jwt),
) -> RAGResponse:
    result = compose_rag(
        question=req.question,
        embedder=embedder,
        weaviate_client=weaviate_client,
        generator=generator,
        k=req.k,
    )
    return RAGResponse(**result)


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/readyz", response_model=ReadyDetail)
def readyz(
    session=Depends(get_session),
    weaviate_client=Depends(get_weaviate),
) -> ReadyDetail:
    neo4j_status = "ok"
    weaviate_status = "ok"

    try:
        session.run("RETURN 1 AS ok").single()
    except Exception:
        neo4j_status = "unavailable"

    try:
        if not weaviate_client.is_ready():
            weaviate_status = "unavailable"
    except Exception:
        weaviate_status = "unavailable"

    detail = ReadyDetail(neo4j=neo4j_status, weaviate=weaviate_status)

    if neo4j_status != "ok" or weaviate_status != "ok":
        raise HTTPException(status_code=503, detail=detail.model_dump())

    return detail