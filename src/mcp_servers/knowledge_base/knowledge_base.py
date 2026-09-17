"""
Knowledge Base — LightRAG adapter
=================================

archaeocode's knowledge-management layer. It turns the artifacts a workflow run
produces (file catalog, AST entities, dependency graph, user stories) into a
persistent knowledge base that can be queried by humans and agents.

The heavy lifting is delegated to `LightRAG <https://github.com/HKUDS/LightRAG>`_,
a graph-augmented retrieval engine (GraphRAG) that stores a knowledge graph plus
vector indexes for entities, relations and text chunks. archaeocode contributes:

* **Deterministic knowledge** — files, classes, functions, dependency edges and
  user stories are written straight into the graph with ``insert_custom_kg``.
  No LLM call is needed; static analysis already produced exact facts.
* **Optional LLM enrichment** — with an API key, raw documents can additionally
  go through LightRAG's entity/relation extraction to surface *business*
  concepts (customers, invoices, tariffs, ...) that live inside the code.
* **Pluggable storage** — the same adapter runs on local files (NetworkX +
  nano-vectordb, zero infrastructure) or on Neo4j / PostgreSQL+pgvector /
  Qdrant / Milvus / Redis / MongoDB for large systems, selected purely through
  configuration.
* **Wiki projection** — the graph can be exported as an Obsidian-compatible
  Markdown wiki (one page per entity, ``[[wikilinks]]``) for humans.

LightRAG is an optional dependency: everything in here degrades to a clear
``KnowledgeBaseError`` when it is not installed.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
import threading
from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_WORKING_DIR = "data/knowledge_base"

# Storage back-ends understood by LightRAG (see lightrag.kg.STORAGE_IMPLEMENTATIONS).
GRAPH_STORAGES = ["NetworkXStorage", "Neo4JStorage", "PGGraphStorage", "MemgraphStorage", "MongoGraphStorage"]
VECTOR_STORAGES = [
    "NanoVectorDBStorage",
    "FaissVectorDBStorage",
    "PGVectorStorage",
    "QdrantVectorDBStorage",
    "MilvusVectorDBStorage",
    "MongoVectorDBStorage",
]
KV_STORAGES = ["JsonKVStorage", "PGKVStorage", "RedisKVStorage", "MongoKVStorage"]
DOC_STATUS_STORAGES = ["JsonDocStatusStorage", "PGDocStatusStorage", "RedisDocStatusStorage", "MongoDocStatusStorage"]

EMBEDDING_PROVIDERS = ["sentence-transformers", "openai", "ollama", "hashing"]
LLM_PROVIDERS = ["auto", "anthropic", "openai", "ollama", "none"]
QUERY_MODES = ["local", "global", "hybrid", "naive", "mix"]

HASHING_EMBEDDING_DIM = 256


class KnowledgeBaseError(RuntimeError):
    """Raised for configuration or availability problems of the knowledge base."""


def is_available() -> bool:
    """Return True when the LightRAG library can be imported."""
    try:
        import lightrag  # noqa: F401

        return True
    except Exception:  # pragma: no cover - depends on the environment
        return False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class KnowledgeBaseConfig:
    """
    Configuration of the knowledge base.

    Every field can be set from ``config/langgraph_config.yaml`` (section
    ``knowledge_base``), from the CLI, or from ``KB_*`` environment variables.
    """

    # Where LightRAG keeps its local files (also used by the file back-ends).
    working_dir: str = DEFAULT_WORKING_DIR
    # Logical partition inside shared back-ends (Neo4j, Postgres, ...): one
    # workspace per analyzed system keeps knowledge bases apart.
    workspace: str = ""

    # Storage back-ends — file-based defaults need no infrastructure.
    graph_storage: str = "NetworkXStorage"
    vector_storage: str = "NanoVectorDBStorage"
    kv_storage: str = "JsonKVStorage"
    doc_status_storage: str = "JsonDocStatusStorage"

    # Embeddings: local sentence-transformers by default (no API key needed).
    embedding_provider: str = "sentence-transformers"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: Optional[int] = None
    # Minimum cosine similarity for vector hits (None = LightRAG default).
    similarity_threshold: Optional[float] = None

    # LLM used for answer synthesis, keyword extraction and (optional) entity
    # extraction. "auto" picks Anthropic, then OpenAI, then nothing, based on
    # the API keys that are present.
    llm_provider: str = "auto"
    llm_model: Optional[str] = None
    llm_max_async: int = 4
    enable_llm_cache: bool = True

    # Chunking of source files (in tokens of the active tokenizer).
    chunk_token_size: int = 1200
    chunk_overlap_token_size: int = 100
    # "tiktoken" needs a one-time download of the encoding; "bytes" works offline.
    tokenizer: str = "tiktoken"

    # LLM-based entity/relation extraction over raw documents (costs tokens).
    extract_entities: bool = False
    # Cap the number of files sent through LLM extraction (0 = all).
    max_extract_files: int = 0

    # Retrieval defaults.
    default_query_mode: str = "mix"
    top_k: int = 40
    chunk_top_k: int = 20

    # Graph export limits.
    max_graph_nodes: int = 5000

    verbose: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "KnowledgeBaseConfig":
        """Build a config from a plain dict (unknown keys go to ``extra``)."""
        data = dict(data or {})
        known = {f.name for f in fields(cls)}
        kwargs = {k: v for k, v in data.items() if k in known and k != "extra"}
        extra = {k: v for k, v in data.items() if k not in known}
        extra.update(data.get("extra") or {})
        return cls(**kwargs, extra=extra)

    @classmethod
    def from_env(cls, **overrides: Any) -> "KnowledgeBaseConfig":
        """Build a config from ``KB_*`` environment variables plus overrides."""
        env = {
            "working_dir": os.getenv("KB_WORKING_DIR"),
            "workspace": os.getenv("KB_WORKSPACE"),
            "graph_storage": os.getenv("KB_GRAPH_STORAGE"),
            "vector_storage": os.getenv("KB_VECTOR_STORAGE"),
            "kv_storage": os.getenv("KB_KV_STORAGE"),
            "doc_status_storage": os.getenv("KB_DOC_STATUS_STORAGE"),
            "embedding_provider": os.getenv("KB_EMBEDDING_PROVIDER"),
            "embedding_model": os.getenv("KB_EMBEDDING_MODEL"),
            "embedding_dim": os.getenv("KB_EMBEDDING_DIM"),
            "llm_provider": os.getenv("KB_LLM_PROVIDER"),
            "llm_model": os.getenv("KB_LLM_MODEL"),
            "tokenizer": os.getenv("KB_TOKENIZER"),
            "default_query_mode": os.getenv("KB_QUERY_MODE"),
            "chunk_token_size": os.getenv("KB_CHUNK_TOKEN_SIZE"),
            "chunk_overlap_token_size": os.getenv("KB_CHUNK_OVERLAP_TOKEN_SIZE"),
        }
        data: Dict[str, Any] = {k: v for k, v in env.items() if v not in (None, "")}
        for int_key in ("embedding_dim", "chunk_token_size", "chunk_overlap_token_size"):
            if int_key in data:
                data[int_key] = int(data[int_key])
        if os.getenv("KB_EXTRACT_ENTITIES") is not None:
            data["extract_entities"] = _env_bool("KB_EXTRACT_ENTITIES", False)
        data.update({k: v for k, v in overrides.items() if v is not None})
        return cls.from_dict(data)

    def validate(self) -> None:
        if self.graph_storage not in GRAPH_STORAGES:
            raise KnowledgeBaseError(f"Unknown graph_storage '{self.graph_storage}'. Options: {GRAPH_STORAGES}")
        if self.vector_storage not in VECTOR_STORAGES:
            raise KnowledgeBaseError(f"Unknown vector_storage '{self.vector_storage}'. Options: {VECTOR_STORAGES}")
        if self.kv_storage not in KV_STORAGES:
            raise KnowledgeBaseError(f"Unknown kv_storage '{self.kv_storage}'. Options: {KV_STORAGES}")
        if self.embedding_provider not in EMBEDDING_PROVIDERS:
            raise KnowledgeBaseError(
                f"Unknown embedding_provider '{self.embedding_provider}'. Options: {EMBEDDING_PROVIDERS}"
            )
        if self.llm_provider not in LLM_PROVIDERS:
            raise KnowledgeBaseError(f"Unknown llm_provider '{self.llm_provider}'. Options: {LLM_PROVIDERS}")
        if self.default_query_mode not in QUERY_MODES:
            raise KnowledgeBaseError(f"Unknown query mode '{self.default_query_mode}'. Options: {QUERY_MODES}")

    def to_dict(self) -> Dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def run_sync(coro_factory: Callable[[], Awaitable[T]]) -> T:
    """
    Run an async knowledge-base operation from synchronous code.

    LightRAG binds its storages to the event loop that initialized them, so a
    whole unit of work (initialize → operate → close) must run on one loop. When
    no loop is running we use ``asyncio.run``; inside a running loop (async
    tests, MCP servers) we hop to a worker thread with its own loop.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro_factory())

    result: Dict[str, Any] = {}

    def _target() -> None:
        try:
            result["value"] = asyncio.run(coro_factory())
        except BaseException as exc:  # pragma: no cover - re-raised below
            result["error"] = exc

    thread = threading.Thread(target=_target, name="archaeocode-kb", daemon=True)
    thread.start()
    thread.join()
    if "error" in result:
        raise result["error"]
    return result["value"]


class ByteTokenizer:
    """
    Offline tokenizer: one token per UTF-8 byte.

    Used when tiktoken's encoding files cannot be downloaded. Token counts are
    roughly 4x tiktoken's, so chunk sizes are scaled accordingly by the adapter.
    Stateless, therefore thread-safe and deep-copyable (LightRAG requires both).
    """

    SCALE = 4

    def encode(self, content: str) -> List[int]:
        return list(content.encode("utf-8"))

    def decode(self, tokens: List[int]) -> str:
        return bytes(tokens).decode("utf-8", errors="ignore")


def _hash_embedding(text: str, dim: int = HASHING_EMBEDDING_DIM):
    """Deterministic bag-of-identifiers embedding (tests / offline smoke runs)."""
    import numpy as np

    vec = np.zeros(dim, dtype=np.float32)
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text.lower()):
        bucket = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dim
        vec[bucket] += 1.0
    norm = float(np.linalg.norm(vec))
    return vec / norm if norm else vec


def _slugify(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-.")
    slug = re.sub(r"-{2,}", "-", slug)
    if not slug:
        slug = "entity"
    if len(slug) > 80:
        slug = slug[:72] + "-" + hashlib.md5(name.encode("utf-8")).hexdigest()[:7]
    return slug


def _relative_path(path: str, root: Optional[str]) -> str:
    if not root:
        return path
    try:
        rel = os.path.relpath(path, root)
    except ValueError:  # different drives on Windows
        return path
    return path if rel.startswith("..") else rel.replace(os.sep, "/")


def keywords_from_question(question: str, limit: int = 12) -> List[str]:
    """Cheap keyword extraction used when no LLM is available for it."""
    seen: List[str] = []
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_.-]{2,}", question):
        if token.lower() in _STOPWORDS:
            continue
        if token not in seen:
            seen.append(token)
        if len(seen) >= limit:
            break
    return seen


_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "what", "which", "where", "when", "how", "does", "did",
    "are", "was", "were", "from", "into", "about", "there", "their", "they", "them", "than", "then",
    "have", "has", "had", "not", "but", "can", "could", "should", "would", "will", "who", "whom", "why",
    "all", "any", "some", "each", "every", "one", "two", "use", "used", "uses", "using", "show", "list",
}


# ---------------------------------------------------------------------------
# Building the deterministic knowledge graph from workflow state
# ---------------------------------------------------------------------------


def _chunk_lines(
    lines: List[str], max_chars: int, overlap_chars: int
) -> List[Tuple[int, int]]:
    """Split ``lines`` into (start, end) line windows bounded by ``max_chars``."""
    windows: List[Tuple[int, int]] = []
    n = len(lines)
    start = 0
    while start < n:
        size = 0
        end = start
        while end < n and (size + len(lines[end]) + 1 <= max_chars or end == start):
            size += len(lines[end]) + 1
            end += 1
        windows.append((start, end))
        if end >= n:
            break
        # Walk back for the overlap, but always make progress.
        back = end
        overlap = 0
        while back > start + 1 and overlap + len(lines[back - 1]) + 1 <= overlap_chars:
            back -= 1
            overlap += len(lines[back]) + 1
        start = max(back, start + 1)
    return windows


def _story_markdown(story: Dict[str, Any]) -> str:
    md = [f"# User Story: {story.get('title', 'Untitled')}", ""]
    md.append(
        f"Priority: {story.get('priority', 'Medium')} | Complexity: {story.get('complexity', '?')} points"
        f" | Confidence: {story.get('confidence', 0.0)}"
    )
    md.append("")
    md.append(f"As a **{story.get('user_role', 'user')}**, I want to **{story.get('capability', '')}**, "
              f"so that **{story.get('benefit', '')}**.")
    criteria = story.get("acceptance_criteria") or []
    if criteria:
        md.append("")
        md.append("Acceptance criteria:")
        for i, criterion in enumerate(criteria, 1):
            md.append(f"{i}. {criterion}")
    files = story.get("code_files") or []
    if files:
        md.append("")
        md.append("Code: " + ", ".join(files))
    return "\n".join(md)


def build_custom_kg(
    state: Dict[str, Any],
    config: Optional[KnowledgeBaseConfig] = None,
    chars_per_token: int = 4,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Translate a workflow state into LightRAG's custom-KG format.

    The result contains ``chunks`` (embedded source windows and user stories),
    ``entities`` (files, classes, functions, methods, external dependencies,
    user stories) and ``relationships`` (contains / imports / derived-from).
    Everything is derived from static analysis — no LLM involved — so the
    graph is exact and cheap to rebuild.

    Returns:
        (custom_kg, stats)
    """
    config = config or KnowledgeBaseConfig()
    root = state.get("source_path")
    max_chars = max(400, config.chunk_token_size * chars_per_token)
    overlap_chars = max(0, config.chunk_overlap_token_size * chars_per_token)

    chunks: List[Dict[str, Any]] = []
    entities: Dict[str, Dict[str, Any]] = {}
    relationships: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def add_entity(name: str, **data: Any) -> None:
        entities[name] = {"entity_name": name, **data}

    def add_relationship(src: str, tgt: str, **data: Any) -> None:
        if src == tgt:
            return
        key = tuple(sorted((src, tgt)))
        if key in relationships:
            # Merge keyword sets of parallel edges.
            existing = relationships[key]
            kws = set(existing.get("keywords", "").split(", ")) | set(data.get("keywords", "").split(", "))
            existing["keywords"] = ", ".join(sorted(k for k in kws if k))
            return
        relationships[key] = {"src_id": src, "tgt_id": tgt, **data}

    # --- files and their text chunks ------------------------------------
    artifacts = state.get("code_artifacts") or []
    rel_by_path: Dict[str, str] = {}
    first_chunk_of_file: Dict[str, str] = {}
    chunk_ranges_of_file: Dict[str, List[Tuple[int, int, str]]] = {}

    for artifact in artifacts:
        path = artifact.get("path") or artifact.get("id") or "unknown"
        rel = _relative_path(path, root)
        rel_by_path[path] = rel
        rel_by_path[rel] = rel
        language = artifact.get("language", "unknown")
        content = artifact.get("content") or ""
        lines = content.splitlines()
        metadata = artifact.get("metadata") or {}

        ranges: List[Tuple[int, int, str]] = []
        for index, (start, end) in enumerate(_chunk_lines(lines, max_chars, overlap_chars) or [(0, 0)]):
            alias = f"{rel}#chunk{index}"
            body = "\n".join(lines[start:end])
            header = f"File: {rel} (lines {start + 1}-{end}, {language})\n"
            chunks.append(
                {
                    "content": header + body,
                    "source_id": alias,
                    "file_path": rel,
                    "chunk_order_index": index,
                }
            )
            ranges.append((start + 1, end, alias))
        first_chunk_of_file[rel] = ranges[0][2]
        chunk_ranges_of_file[rel] = ranges

        description = f"{language} source file {rel}"
        details = []
        if metadata.get("line_count") is not None:
            details.append(f"{metadata['line_count']} lines")
        if artifact.get("complexity_score") is not None:
            details.append(f"complexity {artifact['complexity_score']}")
        if details:
            description += " (" + ", ".join(details) + ")"
        add_entity(
            rel,
            entity_type="file",
            description=description,
            source_id=first_chunk_of_file[rel],
            file_path=rel,
        )

    def chunk_alias_for(rel: str, line: Optional[int]) -> str:
        ranges = chunk_ranges_of_file.get(rel) or []
        if line is not None:
            for start, end, alias in ranges:
                if start <= line <= end:
                    return alias
        return first_chunk_of_file.get(rel, ranges[0][2] if ranges else "")

    # --- AST entities -----------------------------------------------------
    members_of_file: Dict[str, List[str]] = {}
    parsed = state.get("parsed_entities") or {}
    for kind in ("classes", "functions", "methods"):
        for item in parsed.get(kind, []) or []:
            name = item.get("name")
            file_path = item.get("file_path")
            if not name or not file_path:
                continue
            rel = rel_by_path.get(file_path) or _relative_path(file_path, root)
            if rel not in first_chunk_of_file:
                continue
            entity_type = item.get("type") or kind.rstrip("s")
            qualified = f"{rel}::{name}"
            line_start = item.get("line_start")
            span = f"lines {line_start}-{item.get('line_end')}" if line_start else "unknown position"
            add_entity(
                qualified,
                entity_type=entity_type,
                description=f"{entity_type} {name} defined in {rel} ({span})",
                source_id=chunk_alias_for(rel, line_start),
                file_path=rel,
            )
            add_relationship(
                rel,
                qualified,
                description=f"{rel} contains {entity_type} {name}",
                keywords="contains",
                weight=1.0,
                source_id=chunk_alias_for(rel, line_start),
                file_path=rel,
            )
            members_of_file.setdefault(rel, []).append(f"{entity_type} {name}")

    for rel, members in members_of_file.items():
        entity = entities.get(rel)
        if entity:
            shown = ", ".join(members[:25])
            more = f" and {len(members) - 25} more" if len(members) > 25 else ""
            entity["description"] += f". Defines: {shown}{more}"

    # --- dependency graph -------------------------------------------------
    cyclic_edges = set()
    for cycle in state.get("circular_dependencies") or []:
        for a, b in zip(cycle, cycle[1:]):
            cyclic_edges.add((a, b))

    known_basenames: Dict[str, str] = {}
    for rel in first_chunk_of_file:
        base = os.path.basename(rel)
        known_basenames.setdefault(base.lower(), rel)
        known_basenames.setdefault(os.path.splitext(base)[0].lower(), rel)

    def resolve_target(target: str) -> Tuple[str, bool]:
        """Map a dependency target to a file entity if possible."""
        if target in rel_by_path:
            return rel_by_path[target], True
        rel = _relative_path(target, root)
        if rel in first_chunk_of_file:
            return rel, True
        hit = known_basenames.get(target.lower())
        if hit:
            return hit, True
        return target, False

    external_count = 0
    for edge in state.get("dependency_graph") or []:
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue
        src_rel = rel_by_path.get(source) or _relative_path(source, root)
        if src_rel not in first_chunk_of_file:
            continue
        tgt_name, is_file = resolve_target(target)
        rel_type = edge.get("relationship_type") or "depends_on"
        if not is_file and tgt_name not in entities:
            language = (edge.get("metadata") or {}).get("language", "")
            add_entity(
                tgt_name,
                entity_type="external_dependency",
                description=f"External {language} dependency {tgt_name} (referenced by {src_rel}, not part of the analyzed sources)",
                source_id=first_chunk_of_file[src_rel],
                file_path=src_rel,
            )
            external_count += 1
        keywords = rel_type
        if (source, target) in cyclic_edges or (src_rel, tgt_name) in cyclic_edges:
            keywords += ", circular-dependency"
        add_relationship(
            src_rel,
            tgt_name,
            description=f"{src_rel} {rel_type} {tgt_name}",
            keywords=keywords,
            weight=1.0,
            source_id=first_chunk_of_file[src_rel],
            file_path=src_rel,
        )

    # --- user stories -----------------------------------------------------
    story_count = 0
    for index, story in enumerate(state.get("user_stories") or []):
        title = story.get("title") or f"Story {index + 1}"
        alias = f"story#{index}"
        markdown = _story_markdown(story)
        story_files = [rel_by_path.get(f) or _relative_path(f, root) for f in story.get("code_files") or []]
        file_path = story_files[0] if story_files else "user_stories"
        chunks.append({"content": markdown, "source_id": alias, "file_path": file_path, "chunk_order_index": 0})
        entity_name = f"Story: {title}"
        criteria = "; ".join(story.get("acceptance_criteria") or [])
        add_entity(
            entity_name,
            entity_type="user_story",
            description=(
                f"User story '{title}': as a {story.get('user_role', 'user')}, I want to "
                f"{story.get('capability', '')}, so that {story.get('benefit', '')}. "
                f"Priority {story.get('priority', 'Medium')}, complexity {story.get('complexity', '?')}, "
                f"confidence {story.get('confidence', 0.0)}."
                + (f" Acceptance criteria: {criteria}" if criteria else "")
            ),
            source_id=alias,
            file_path=file_path,
        )
        for rel in story_files:
            if rel in first_chunk_of_file:
                add_relationship(
                    entity_name,
                    rel,
                    description=f"User story '{title}' was derived from {rel}",
                    keywords="derived_from, user_story",
                    weight=1.0,
                    source_id=alias,
                    file_path=rel,
                )
        story_count += 1

    custom_kg = {
        "chunks": chunks,
        "entities": list(entities.values()),
        "relationships": list(relationships.values()),
    }
    stats = {
        "files": len(first_chunk_of_file),
        "chunks": len(chunks),
        "entities": len(entities),
        "relationships": len(relationships),
        "external_dependencies": external_count,
        "user_stories": story_count,
    }
    return custom_kg, stats


# ---------------------------------------------------------------------------
# The knowledge base
# ---------------------------------------------------------------------------


class KnowledgeBase:
    """
    Thin, opinionated wrapper around a LightRAG instance.

    Usage (async)::

        kb = KnowledgeBase(KnowledgeBaseConfig(working_dir="data/knowledge_base"))
        await kb.initialize()
        await kb.index_state(workflow_state)
        answer = await kb.query("Which programs update the customer master file?")
        await kb.close()

    Synchronous callers can use :func:`run_sync` around a coroutine that does
    all three steps, or the convenience class method :meth:`run_with`.
    """

    def __init__(self, config: Optional[KnowledgeBaseConfig] = None):
        self.config = config or KnowledgeBaseConfig.from_env()
        self.config.validate()
        self.rag = None
        self.llm_available = False
        self.llm_description = "none"
        self.embedding_description = ""
        self.tokenizer_description = ""
        self._token_scale = 1

    # -- lifecycle --------------------------------------------------------

    async def initialize(self) -> "KnowledgeBase":
        """Create the LightRAG instance and open its storages."""
        if self.rag is not None:
            return self
        if not is_available():
            raise KnowledgeBaseError(
                "LightRAG is not installed. Run `pip install lightrag-hku` (it is listed in requirements.txt)."
            )

        from lightrag import LightRAG
        from lightrag.kg.shared_storage import initialize_pipeline_status

        if not self.config.verbose:
            logging.getLogger("lightrag").setLevel(logging.WARNING)

        self._apply_backend_env()
        Path(self.config.working_dir).mkdir(parents=True, exist_ok=True)

        embedding_func = self._make_embedding_func()
        llm_func, llm_name, llm_kwargs = self._make_llm_func()
        tokenizer = self._make_tokenizer()

        kwargs: Dict[str, Any] = dict(
            working_dir=self.config.working_dir,
            workspace=self.config.workspace,
            kv_storage=self.config.kv_storage,
            vector_storage=self.config.vector_storage,
            graph_storage=self.config.graph_storage,
            doc_status_storage=self.config.doc_status_storage,
            embedding_func=embedding_func,
            llm_model_func=llm_func,
            llm_model_name=llm_name,
            llm_model_kwargs=llm_kwargs,
            llm_model_max_async=self.config.llm_max_async,
            enable_llm_cache=self.config.enable_llm_cache,
            chunk_token_size=self.config.chunk_token_size * self._token_scale,
            chunk_overlap_token_size=self.config.chunk_overlap_token_size * self._token_scale,
            max_graph_nodes=self.config.max_graph_nodes,
        )
        if tokenizer is not None:
            kwargs["tokenizer"] = tokenizer
        threshold = self.config.similarity_threshold
        if threshold is None and self.config.embedding_provider == "hashing":
            threshold = 0.05
        if threshold is not None:
            kwargs["cosine_better_than_threshold"] = threshold
            kwargs["vector_db_storage_cls_kwargs"] = {"cosine_better_than_threshold": threshold}

        self.rag = LightRAG(**kwargs)
        await self.rag.initialize_storages()
        await initialize_pipeline_status(self.config.workspace or None)
        logger.info(
            "Knowledge base ready (graph=%s, vectors=%s, embeddings=%s, llm=%s, tokenizer=%s)",
            self.config.graph_storage,
            self.config.vector_storage,
            self.embedding_description,
            self.llm_description,
            self.tokenizer_description,
        )
        return self

    async def close(self) -> None:
        """Flush and close all storages."""
        if self.rag is not None:
            await self.rag.finalize_storages()
            self.rag = None

    async def __aenter__(self) -> "KnowledgeBase":
        return await self.initialize()

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    @classmethod
    def run_with(
        cls,
        operation: Callable[["KnowledgeBase"], Awaitable[T]],
        config: Optional[KnowledgeBaseConfig] = None,
    ) -> T:
        """Open a knowledge base, run ``operation`` on it, close it — from sync code."""

        async def _job() -> T:
            async with cls(config) as kb:
                return await operation(kb)

        return run_sync(_job)

    # -- factories --------------------------------------------------------

    def _apply_backend_env(self) -> None:
        """Bridge archaeocode's environment names to LightRAG's."""
        if self.config.graph_storage == "Neo4JStorage":
            if os.getenv("NEO4J_USER") and not os.getenv("NEO4J_USERNAME"):
                os.environ["NEO4J_USERNAME"] = os.environ["NEO4J_USER"]
            if self.config.workspace and not os.getenv("NEO4J_WORKSPACE"):
                os.environ["NEO4J_WORKSPACE"] = self.config.workspace
        for key, value in (self.config.extra.get("env") or {}).items():
            os.environ.setdefault(str(key), str(value))

    def _make_tokenizer(self):
        from lightrag.utils import Tokenizer

        choice = (self.config.tokenizer or "tiktoken").lower()
        if choice == "tiktoken":
            try:
                import tiktoken

                encoding = tiktoken.encoding_for_model("gpt-4o-mini")
                self.tokenizer_description = "tiktoken/o200k_base"
                return Tokenizer(model_name="gpt-4o-mini", tokenizer=encoding)
            except Exception as exc:  # network blocked, encoding not cached, ...
                logger.warning("tiktoken unavailable (%s); falling back to the offline byte tokenizer", exc)
        self._token_scale = ByteTokenizer.SCALE
        self.tokenizer_description = "bytes (offline)"
        return Tokenizer(model_name="bytes", tokenizer=ByteTokenizer())

    def _make_embedding_func(self):
        from lightrag.utils import EmbeddingFunc

        provider = self.config.embedding_provider
        model = self.config.embedding_model

        if provider == "sentence-transformers":
            try:
                from sentence_transformers import SentenceTransformer

                st_model = SentenceTransformer(model)
                dim = st_model.get_sentence_embedding_dimension()
            except Exception as exc:
                logger.warning(
                    "sentence-transformers model '%s' unavailable (%s); using hashing embeddings", model, exc
                )
                provider = "sentence-transformers-fallback"
            else:
                lock = threading.Lock()

                async def st_embed(texts: List[str], **_: Any):
                    def _encode():
                        with lock:
                            return st_model.encode(list(texts), convert_to_numpy=True, normalize_embeddings=True)

                    return await asyncio.to_thread(_encode)

                self.embedding_description = f"sentence-transformers/{model} ({dim}d)"
                return EmbeddingFunc(embedding_dim=dim, max_token_size=8192, func=st_embed, model_name=model)

        if provider == "openai":
            from functools import partial

            from lightrag.llm.openai import openai_embed

            dim = self.config.embedding_dim or (3072 if "large" in model else 1536)
            self.embedding_description = f"openai/{model} ({dim}d)"
            return EmbeddingFunc(
                embedding_dim=dim,
                max_token_size=8191,
                func=partial(openai_embed.func, model=model),
                model_name=model,
            )

        if provider == "ollama":
            from functools import partial

            from lightrag.llm.ollama import ollama_embed

            dim = self.config.embedding_dim or 1024
            host = self.config.extra.get("ollama_host") or os.getenv("OLLAMA_HOST", "http://localhost:11434")
            self.embedding_description = f"ollama/{model} ({dim}d)"
            return EmbeddingFunc(
                embedding_dim=dim,
                max_token_size=8192,
                func=partial(ollama_embed.func, embed_model=model, host=host),
                model_name=model,
            )

        # "hashing" — deterministic, dependency-free (tests, offline smoke runs).
        import numpy as np

        dim = self.config.embedding_dim or HASHING_EMBEDDING_DIM

        async def hash_embed(texts: List[str], **_: Any):
            return np.stack([_hash_embedding(t, dim) for t in texts])

        self.embedding_description = f"hashing ({dim}d)"
        if provider == "sentence-transformers-fallback":
            self.embedding_description += f", fallback because sentence-transformers/{model} is unavailable"
        return EmbeddingFunc(embedding_dim=dim, max_token_size=1_000_000, func=hash_embed, model_name="hashing")

    def _make_llm_func(self):
        """Pick the LLM adapter; returns (func, model_name, kwargs)."""
        provider = self.config.llm_provider
        if provider == "auto":
            if os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-ant-") and "your-api-key" not in os.getenv(
                "ANTHROPIC_API_KEY", ""
            ):
                provider = "anthropic"
            elif os.getenv("OPENAI_API_KEY", "").startswith("sk-"):
                provider = "openai"
            elif os.getenv("OLLAMA_HOST"):
                provider = "ollama"
            else:
                provider = "none"

        if provider == "anthropic":
            from lightrag.llm.anthropic import anthropic_complete

            model = self.config.llm_model or os.getenv("MODEL_NAME", "claude-sonnet-5")
            self.llm_available = True
            self.llm_description = f"anthropic/{model}"
            return anthropic_complete, model, {}

        if provider == "openai":
            from lightrag.llm.openai import openai_complete

            model = self.config.llm_model or os.getenv("MODEL_NAME", "gpt-4o-mini")
            if not model.startswith(("gpt", "o1", "o3", "o4")):
                model = "gpt-4o-mini"
            self.llm_available = True
            self.llm_description = f"openai/{model}"
            return openai_complete, model, {}

        if provider == "ollama":
            from lightrag.llm.ollama import ollama_model_complete

            model = self.config.llm_model or os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
            host = self.config.extra.get("ollama_host") or os.getenv("OLLAMA_HOST", "http://localhost:11434")
            self.llm_available = True
            self.llm_description = f"ollama/{model}"
            return ollama_model_complete, model, {"host": host, "options": {"num_ctx": 32768}}

        async def no_llm(prompt: str, *args: Any, **kwargs: Any) -> str:
            # Returning an empty string makes LightRAG fall back to the raw
            # query for keyword extraction; answer synthesis is guarded in query().
            return ""

        self.llm_available = False
        self.llm_description = "none"
        return no_llm, "none", {}

    # -- indexing ---------------------------------------------------------

    def _require(self):
        if self.rag is None:
            raise KnowledgeBaseError("KnowledgeBase.initialize() must be awaited first")
        return self.rag

    async def insert_custom_kg(self, custom_kg: Dict[str, Any], batch_files: int = 200) -> None:
        """Insert a custom KG, batching the chunks so huge codebases stream in."""
        rag = self._require()
        chunks = custom_kg.get("chunks") or []
        entities = custom_kg.get("entities") or []
        relationships = custom_kg.get("relationships") or []

        if len(chunks) <= batch_files * 4:
            await rag.ainsert_custom_kg(custom_kg)
            return

        # Group chunks by file so an entity always lands in the same batch as
        # the chunk its source_id refers to.
        by_file: Dict[str, List[Dict[str, Any]]] = {}
        for chunk in chunks:
            by_file.setdefault(chunk.get("file_path", ""), []).append(chunk)
        alias_to_file = {c["source_id"]: c.get("file_path", "") for c in chunks}
        files = list(by_file)
        for i in range(0, len(files), batch_files):
            batch_paths = set(files[i : i + batch_files])
            batch_chunks = [c for f in batch_paths for c in by_file[f]]
            batch_entities = [e for e in entities if alias_to_file.get(e.get("source_id", "")) in batch_paths]
            batch_rels = [r for r in relationships if alias_to_file.get(r.get("source_id", "")) in batch_paths]
            await rag.ainsert_custom_kg(
                {"chunks": batch_chunks, "entities": batch_entities, "relationships": batch_rels}
            )

    async def index_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Index a workflow state: deterministic graph first, LLM extraction second.

        Returns statistics about what was written.
        """
        rag = self._require()
        custom_kg, stats = build_custom_kg(state, self.config, chars_per_token=4)
        started = datetime.now()
        await self.insert_custom_kg(custom_kg)
        stats["extraction"] = "skipped"

        if self.config.extract_entities:
            if not self.llm_available:
                stats["extraction"] = "skipped (no LLM configured)"
            else:
                artifacts = state.get("code_artifacts") or []
                limit = self.config.max_extract_files or len(artifacts)
                docs = []
                ids = []
                paths = []
                for artifact in artifacts[:limit]:
                    content = artifact.get("content") or ""
                    if not content.strip():
                        continue
                    rel = _relative_path(artifact.get("path", ""), state.get("source_path"))
                    docs.append(content)
                    ids.append("doc-" + hashlib.md5(rel.encode("utf-8")).hexdigest())
                    paths.append(rel)
                if docs:
                    await rag.ainsert(docs, ids=ids, file_paths=paths)
                    stats["extraction"] = f"{len(docs)} documents"
                else:
                    stats["extraction"] = "no documents"

        stats["seconds"] = round((datetime.now() - started).total_seconds(), 2)
        stats["working_dir"] = self.config.working_dir
        stats["workspace"] = self.config.workspace
        stats["graph_storage"] = self.config.graph_storage
        stats["vector_storage"] = self.config.vector_storage
        stats["embeddings"] = self.embedding_description
        stats["llm"] = self.llm_description
        return stats

    async def add_documents(
        self, documents: List[Dict[str, Any]], extract: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Add free-form documents (design docs, tickets, runbooks, interview notes).

        With ``extract`` (default: config.extract_entities) and an LLM, the
        documents go through LightRAG's entity extraction; otherwise they are
        only chunked and embedded, which still makes them searchable.
        """
        rag = self._require()
        extract = self.config.extract_entities if extract is None else extract
        texts, ids, paths = [], [], []
        for index, doc in enumerate(documents):
            content = (doc.get("content") or "").strip()
            if not content:
                continue
            path = doc.get("path") or doc.get("id") or f"document-{index}"
            texts.append(content)
            ids.append(doc.get("id") or "doc-" + hashlib.md5(path.encode("utf-8")).hexdigest())
            paths.append(path)
        if not texts:
            return {"documents": 0, "mode": "none"}

        if extract and self.llm_available:
            track_id = await rag.ainsert(texts, ids=ids, file_paths=paths)
            return {"documents": len(texts), "mode": "llm-extraction", "track_id": track_id}

        custom_kg = {"chunks": [], "entities": [], "relationships": []}
        for text, doc_id, path in zip(texts, ids, paths):
            lines = text.splitlines()
            windows = _chunk_lines(lines, self.config.chunk_token_size * 4, self.config.chunk_overlap_token_size * 4)
            for index, (start, end) in enumerate(windows):
                custom_kg["chunks"].append(
                    {
                        "content": "\n".join(lines[start:end]),
                        "source_id": f"{doc_id}#chunk{index}",
                        "file_path": path,
                        "chunk_order_index": index,
                    }
                )
            custom_kg["entities"].append(
                {
                    "entity_name": path,
                    "entity_type": "document",
                    "description": f"Document {path}: " + " ".join(lines[:3])[:300],
                    "source_id": f"{doc_id}#chunk0",
                    "file_path": path,
                }
            )
        await rag.ainsert_custom_kg(custom_kg)
        return {"documents": len(texts), "mode": "chunks-only", "chunks": len(custom_kg["chunks"])}

    # -- retrieval --------------------------------------------------------

    def _query_param(self, mode: Optional[str], **overrides: Any):
        from lightrag import QueryParam

        mode = mode or self.config.default_query_mode
        if mode not in QUERY_MODES:
            raise KnowledgeBaseError(f"Unknown query mode '{mode}'. Options: {QUERY_MODES}")
        params: Dict[str, Any] = dict(
            mode=mode,
            top_k=self.config.top_k,
            chunk_top_k=self.config.chunk_top_k,
            enable_rerank=False,
        )
        params.update({k: v for k, v in overrides.items() if v is not None})
        return QueryParam(**params)

    async def retrieve(
        self,
        question: str,
        mode: Optional[str] = None,
        top_k: Optional[int] = None,
        chunk_top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Structured retrieval without answer synthesis.

        Returns LightRAG's ``query_data`` payload: matching entities, relations,
        chunks and references. Works without any LLM (keywords are then derived
        from the question directly).
        """
        rag = self._require()
        overrides: Dict[str, Any] = {"top_k": top_k, "chunk_top_k": chunk_top_k}
        if not self.llm_available:
            keywords = keywords_from_question(question) or [question]
            overrides["ll_keywords"] = keywords
            overrides["hl_keywords"] = keywords
        param = self._query_param(mode, **overrides)
        result = await rag.aquery_data(question, param)
        data = result.get("data") or {}
        return {
            "question": question,
            "mode": param.mode,
            "entities": data.get("entities", []),
            "relationships": data.get("relationships", []),
            "chunks": data.get("chunks", []),
            "references": data.get("references", []),
            "metadata": result.get("metadata", {}),
        }

    async def context(self, question: str, mode: Optional[str] = None) -> str:
        """The exact context block LightRAG would hand to the LLM (prompt-ready)."""
        rag = self._require()
        overrides: Dict[str, Any] = {"only_need_context": True}
        if not self.llm_available:
            keywords = keywords_from_question(question) or [question]
            overrides["ll_keywords"] = keywords
            overrides["hl_keywords"] = keywords
        result = await rag.aquery(question, self._query_param(mode, **overrides))
        return result if isinstance(result, str) else str(result)

    async def query(
        self,
        question: str,
        mode: Optional[str] = None,
        response_type: str = "Multiple Paragraphs",
        system_prompt: Optional[str] = None,
    ) -> str:
        """Ask a question and get an LLM-synthesized answer with citations."""
        rag = self._require()
        if not self.llm_available:
            raise KnowledgeBaseError(
                "No LLM configured for answer synthesis. Set ANTHROPIC_API_KEY / OPENAI_API_KEY "
                "(or KB_LLM_PROVIDER=ollama), or use retrieve()/context() which need no LLM."
            )
        param = self._query_param(mode, response_type=response_type)
        result = await rag.aquery(question, param, system_prompt=system_prompt)
        return result if isinstance(result, str) else "".join([chunk async for chunk in result])

    # -- graph access -----------------------------------------------------

    async def graph(self, label: str = "*", max_depth: int = 2, max_nodes: Optional[int] = None) -> Dict[str, Any]:
        """Neighbourhood of an entity (or the whole graph with ``*``) as plain dicts."""
        rag = self._require()
        kg = await rag.get_knowledge_graph(label, max_depth=max_depth, max_nodes=max_nodes)
        return {
            "label": label,
            "is_truncated": bool(getattr(kg, "is_truncated", False)),
            "nodes": [
                {"id": n.id, "labels": list(n.labels), **(n.properties or {})} for n in kg.nodes
            ],
            "edges": [
                {"source": e.source, "target": e.target, **(e.properties or {})} for e in kg.edges
            ],
        }

    async def labels(self) -> List[str]:
        rag = self._require()
        return list(await rag.get_graph_labels())

    async def stats(self) -> Dict[str, Any]:
        """Size of the knowledge base and how it is configured."""
        rag = self._require()
        labels = await rag.get_graph_labels()
        kg = await rag.get_knowledge_graph("*", max_depth=1, max_nodes=self.config.max_graph_nodes)
        types: Dict[str, int] = {}
        for node in kg.nodes:
            entity_type = (node.properties or {}).get("entity_type", "UNKNOWN")
            types[entity_type] = types.get(entity_type, 0) + 1
        try:
            processing = await rag.get_processing_status()
        except Exception:
            processing = {}
        return {
            "entities": len(labels),
            "edges_sampled": len(kg.edges),
            "sample_truncated": bool(getattr(kg, "is_truncated", False)),
            "entity_types": dict(sorted(types.items(), key=lambda kv: -kv[1])),
            "documents": processing,
            "working_dir": self.config.working_dir,
            "workspace": self.config.workspace,
            "graph_storage": self.config.graph_storage,
            "vector_storage": self.config.vector_storage,
            "kv_storage": self.config.kv_storage,
            "embeddings": self.embedding_description,
            "llm": self.llm_description,
            "tokenizer": self.tokenizer_description,
        }

    # -- wiki export ------------------------------------------------------

    async def export_wiki(self, output_dir: str, max_nodes: Optional[int] = None) -> Dict[str, Any]:
        """
        Project the knowledge graph onto an Obsidian-compatible Markdown wiki.

        One page per entity (``[[wikilinks]]`` for relations), grouped index
        page, and LightRAG's own tabular export next to it. This is the
        human-facing "LLM wiki" view; the graph stays the source of truth.
        """
        rag = self._require()
        graph = await self.graph("*", max_depth=1, max_nodes=max_nodes or self.config.max_graph_nodes)
        out = Path(output_dir)
        pages_dir = out / "entities"
        pages_dir.mkdir(parents=True, exist_ok=True)

        nodes = {n["id"]: n for n in graph["nodes"]}
        slugs: Dict[str, str] = {}
        used: set = set()
        for node_id in sorted(nodes):
            slug = _slugify(node_id)
            if slug in used:
                slug = f"{slug}-{hashlib.md5(node_id.encode('utf-8')).hexdigest()[:6]}"
            used.add(slug)
            slugs[node_id] = slug

        neighbours: Dict[str, List[Dict[str, Any]]] = {}
        for edge in graph["edges"]:
            neighbours.setdefault(edge["source"], []).append({"other": edge["target"], **edge})
            neighbours.setdefault(edge["target"], []).append({"other": edge["source"], **edge})

        by_type: Dict[str, List[str]] = {}
        for node_id, node in nodes.items():
            entity_type = node.get("entity_type", "UNKNOWN")
            by_type.setdefault(entity_type, []).append(node_id)
            lines = [
                f"# {node_id}",
                "",
                f"- **Type**: {entity_type}",
                f"- **Source**: `{node.get('file_path', 'n/a')}`",
                "",
                "## Description",
                "",
                str(node.get("description", "")).replace("<SEP>", "\n\n"),
                "",
            ]
            links = neighbours.get(node_id, [])
            if links:
                lines += ["## Relations", ""]
                for link in sorted(links, key=lambda l: l["other"]):
                    other = link["other"]
                    target = slugs.get(other, _slugify(other))
                    keywords = link.get("keywords", "")
                    description = link.get("description", "")
                    lines.append(f"- [[{target}|{other}]] — {keywords}: {description}")
                lines.append("")
            (pages_dir / f"{slugs[node_id]}.md").write_text("\n".join(lines), encoding="utf-8")

        index = [
            "# Knowledge Base",
            "",
            f"Generated {datetime.now().isoformat(timespec='seconds')} from LightRAG "
            f"({self.config.graph_storage}, workspace '{self.config.workspace or 'default'}').",
            "",
            f"{len(nodes)} entities, {len(graph['edges'])} relations"
            + (" (truncated view)" if graph["is_truncated"] else "")
            + ".",
            "",
        ]
        for entity_type in sorted(by_type):
            index += [f"## {entity_type} ({len(by_type[entity_type])})", ""]
            for node_id in sorted(by_type[entity_type]):
                index.append(f"- [[entities/{slugs[node_id]}|{node_id}]]")
            index.append("")
        (out / "index.md").write_text("\n".join(index), encoding="utf-8")

        try:
            await rag.aexport_data(str(out / "graph_export.md"), file_format="md")
        except Exception as exc:  # pragma: no cover - export formats vary by version
            logger.warning("LightRAG tabular export failed: %s", exc)

        return {
            "output_dir": str(out),
            "pages": len(nodes),
            "relations": len(graph["edges"]),
            "truncated": graph["is_truncated"],
            "index": str(out / "index.md"),
        }
