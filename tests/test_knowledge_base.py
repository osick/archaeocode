"""
Knowledge Base Tests
====================

Exercises the LightRAG-backed knowledge base end to end without any network
access or API key: hashing embeddings, the offline byte tokenizer, file-based
storages, and no LLM (retrieval-only paths).
"""

import json
import os
import sys

import pytest

project_root = os.path.join(os.path.dirname(__file__), "..")
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.orchestration.state.graph_state import create_initial_state  # noqa: E402
from src.orchestration.nodes.discovery_node import CodeDiscoveryNode  # noqa: E402
from src.mcp_servers.knowledge_base.knowledge_base import (  # noqa: E402
    KnowledgeBase,
    KnowledgeBaseConfig,
    KnowledgeBaseError,
    build_custom_kg,
    is_available,
    keywords_from_question,
)

requires_lightrag = pytest.mark.skipif(not is_available(), reason="lightrag-hku not installed")

COBOL_SAMPLE = os.path.join(project_root, "sample_data", "cobol")


@pytest.fixture(autouse=True)
def _no_llm_keys(monkeypatch):
    """Make sure tests never pick up a real API key from the developer's .env."""
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OLLAMA_HOST"):
        monkeypatch.delenv(key, raising=False)
    for key in list(os.environ):
        if key.startswith("KB_"):
            monkeypatch.delenv(key, raising=False)


def offline_config(tmp_path, **overrides) -> KnowledgeBaseConfig:
    settings = dict(
        working_dir=str(tmp_path / "kb"),
        embedding_provider="hashing",
        tokenizer="bytes",
        llm_provider="none",
        chunk_token_size=300,
        chunk_overlap_token_size=30,
    )
    settings.update(overrides)
    return KnowledgeBaseConfig(**settings)


def sample_state():
    """Discovery over the COBOL sample plus hand-made downstream results."""
    state = create_initial_state("cobol", "java", COBOL_SAMPLE)
    state = CodeDiscoveryNode({})(state)
    assert len(state["code_artifacts"]) >= 2
    paths = sorted(a["path"] for a in state["code_artifacts"])
    custmgmt = next(p for p in paths if p.endswith("CUSTMGMT.cob"))
    payment = next(p for p in paths if p.endswith("PAYMENT.cob"))

    state["parsed_entities"] = {
        "classes": [],
        "functions": [
            {"name": "PROCESS-PAYMENT", "type": "function", "line_start": 5, "line_end": 40, "file_path": payment},
        ],
        "methods": [],
        "imports": [],
        "variables": [],
    }
    state["dependency_graph"] = [
        {"source": payment, "target": custmgmt, "relationship_type": "calls", "metadata": {"language": "cobol"}},
        {"source": payment, "target": "SQLCA", "relationship_type": "imports", "metadata": {"language": "cobol"}},
        {"source": custmgmt, "target": payment, "relationship_type": "calls", "metadata": {"language": "cobol"}},
    ]
    state["circular_dependencies"] = [[payment, custmgmt, payment]]
    state["user_stories"] = [
        {
            "title": "Record a customer payment",
            "user_role": "accounts clerk",
            "capability": "post an incoming payment against a customer account",
            "benefit": "outstanding balances stay accurate",
            "acceptance_criteria": ["Given a valid customer, when a payment is posted, then the balance is reduced"],
            "code_files": [payment],
            "complexity": 5,
            "priority": "High",
            "confidence": 0.8,
        }
    ]
    return state


# ---------------------------------------------------------------------------
# Pure functions (no LightRAG needed)
# ---------------------------------------------------------------------------


def test_build_custom_kg_from_state():
    state = sample_state()
    kg, stats = build_custom_kg(state, KnowledgeBaseConfig(chunk_token_size=300, chunk_overlap_token_size=30))

    names = {e["entity_name"] for e in kg["entities"]}
    assert {"PAYMENT.cob", "CUSTMGMT.cob", "PAYMENT.cob::PROCESS-PAYMENT", "SQLCA", "Story: Record a customer payment"} <= names

    types = {e["entity_name"]: e["entity_type"] for e in kg["entities"]}
    assert types["SQLCA"] == "external_dependency"
    assert types["Story: Record a customer payment"] == "user_story"
    assert types["PAYMENT.cob::PROCESS-PAYMENT"] == "function"

    rels = {(r["src_id"], r["tgt_id"]): r for r in kg["relationships"]}
    assert ("PAYMENT.cob", "PAYMENT.cob::PROCESS-PAYMENT") in rels
    assert ("PAYMENT.cob", "SQLCA") in rels
    # The two-way call between the files collapses into one undirected edge flagged as circular.
    circular = [r for r in kg["relationships"] if "circular-dependency" in r["keywords"]]
    assert len(circular) == 1 and "calls" in circular[0]["keywords"]
    # Story is linked back to its source file.
    assert ("Story: Record a customer payment", "PAYMENT.cob") in rels

    # Every entity/relationship source_id refers to a chunk alias in the same payload.
    aliases = {c["source_id"] for c in kg["chunks"]}
    assert all(e["source_id"] in aliases for e in kg["entities"])
    assert all(r["source_id"] in aliases for r in kg["relationships"])
    # Files are chunked into several windows at this small chunk size.
    assert stats["chunks"] > stats["files"]
    assert stats == {**stats, "files": 2, "user_stories": 1, "external_dependencies": 1}


def test_config_from_dict_and_env(monkeypatch):
    monkeypatch.setenv("KB_GRAPH_STORAGE", "Neo4JStorage")
    monkeypatch.setenv("KB_EXTRACT_ENTITIES", "true")
    monkeypatch.setenv("KB_CHUNK_TOKEN_SIZE", "800")
    config = KnowledgeBaseConfig.from_env(working_dir="/tmp/x", embedding_provider="hashing")
    assert config.graph_storage == "Neo4JStorage"
    assert config.extract_entities is True
    assert config.chunk_token_size == 800
    assert config.working_dir == "/tmp/x"
    config.validate()

    with pytest.raises(KnowledgeBaseError):
        KnowledgeBaseConfig(vector_storage="PineconeStorage").validate()

    loaded = KnowledgeBaseConfig.from_dict({"working_dir": "kb", "unknown_key": 1, "extra": {"env": {"A": "1"}}})
    assert loaded.extra == {"unknown_key": 1, "env": {"A": "1"}}


def test_keywords_from_question():
    assert keywords_from_question("Which programs update the CUSTOMER-MASTER file?") == [
        "programs", "update", "CUSTOMER-MASTER", "file"
    ]


# ---------------------------------------------------------------------------
# LightRAG-backed behaviour (offline: hashing embeddings, byte tokenizer, no LLM)
# ---------------------------------------------------------------------------


@requires_lightrag
def test_index_retrieve_graph_and_wiki(tmp_path):
    state = sample_state()
    config = offline_config(tmp_path)

    async def job(kb: KnowledgeBase):
        assert kb.llm_available is False
        stats = await kb.index_state(state)
        naive = await kb.retrieve("customer payment balance", mode="naive")
        local = await kb.retrieve("PROCESS-PAYMENT", mode="local")
        hybrid = await kb.retrieve("payment", mode="hybrid")
        context = await kb.context("SQLCA", mode="mix")
        graph = await kb.graph("SQLCA", max_depth=1)
        summary = await kb.stats()
        wiki = await kb.export_wiki(str(tmp_path / "wiki"))
        with pytest.raises(KnowledgeBaseError):
            await kb.query("needs an llm")
        return stats, naive, local, hybrid, context, graph, summary, wiki

    stats, naive, local, hybrid, context, graph, summary, wiki = KnowledgeBase.run_with(job, config)

    assert stats["files"] == 2 and stats["entities"] >= 5 and stats["extraction"] == "skipped"
    assert stats["embeddings"].startswith("hashing")

    assert naive["chunks"], "vector search over chunks returned nothing"
    assert {c["file_path"] for c in naive["chunks"]} <= {"PAYMENT.cob", "CUSTMGMT.cob"}

    local_names = [e["entity_name"] for e in local["entities"]]
    assert "PAYMENT.cob::PROCESS-PAYMENT" in local_names
    assert local["relationships"], "graph neighbourhood of the function is empty"

    assert any(e["entity_name"] == "PAYMENT.cob" for e in hybrid["entities"])
    assert "SQLCA" in context

    assert {n["id"] for n in graph["nodes"]} == {"SQLCA", "PAYMENT.cob"}
    assert graph["edges"][0]["keywords"] == "imports"

    assert summary["entities"] >= 5
    assert summary["entity_types"]["file"] == 2
    assert summary["entity_types"]["user_story"] == 1

    assert wiki["pages"] == summary["entities"]
    index = (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8")
    assert "## user_story (1)" in index and "[[entities/" in index
    story_page = next((tmp_path / "wiki" / "entities").glob("Story-*.md")).read_text(encoding="utf-8")
    assert "[[PAYMENT.cob|PAYMENT.cob]]" in story_page

    # Reopening the same directory sees the persisted graph (second event loop).
    async def reopen(kb: KnowledgeBase):
        return await kb.labels()

    assert "SQLCA" in KnowledgeBase.run_with(reopen, config)


@requires_lightrag
def test_add_documents_without_llm(tmp_path):
    config = offline_config(tmp_path)

    async def job(kb: KnowledgeBase):
        added = await kb.add_documents(
            [{"path": "docs/runbook.md", "content": "Nightly batch runs PAYMENT after CUSTMGMT.\nRestart the job via OPC."}]
        )
        hits = await kb.retrieve("nightly batch restart", mode="naive")
        return added, hits

    added, hits = KnowledgeBase.run_with(job, config)
    assert added["mode"] == "chunks-only" and added["documents"] == 1
    assert hits["chunks"] and hits["chunks"][0]["file_path"] == "runbook.md"


@requires_lightrag
def test_mcp_server_tools(tmp_path):
    from src.mcp_servers.knowledge_base import knowledge_mcp_server as mcp

    state = sample_state()
    config = offline_config(tmp_path)
    KnowledgeBase.run_with(lambda kb: kb.index_state(state), config)

    async def call_tools():
        # The MCP server builds its config from KB_* variables + explicit args.
        os.environ["KB_EMBEDDING_PROVIDER"] = "hashing"
        os.environ["KB_TOKENIZER"] = "bytes"
        os.environ["KB_LLM_PROVIDER"] = "none"
        try:
            stats = json.loads((await mcp.kb_stats(working_dir=config.working_dir))[0].text)
            retrieved = json.loads(
                (await mcp.kb_retrieve("PROCESS-PAYMENT", mode="local", working_dir=config.working_dir))[0].text
            )
            graph = json.loads((await mcp.kb_graph("PAYMENT.cob", max_depth=1, working_dir=config.working_dir))[0].text)
            query = json.loads((await mcp.kb_query("anything", working_dir=config.working_dir))[0].text)
            wiki = json.loads(
                (await mcp.kb_export_wiki(str(tmp_path / "mcp-wiki"), working_dir=config.working_dir))[0].text
            )
            for kb in list(mcp._instances.values()):
                await kb.close()
            mcp._instances.clear()
        finally:
            for key in ("KB_EMBEDDING_PROVIDER", "KB_TOKENIZER", "KB_LLM_PROVIDER"):
                os.environ.pop(key, None)
        return stats, retrieved, graph, query, wiki

    import asyncio

    stats, retrieved, graph, query, wiki = asyncio.run(call_tools())
    assert stats["success"] and stats["entities"] >= 5
    assert retrieved["success"] and any(e["entity_name"] == "PAYMENT.cob::PROCESS-PAYMENT" for e in retrieved["entities"])
    assert graph["success"] and len(graph["nodes"]) >= 3
    assert query["success"] is False and "No LLM configured" in query["error"]
    assert wiki["success"] and wiki["pages"] == stats["entities"]


@requires_lightrag
def test_workflow_with_knowledge_base_node(tmp_path):
    """Full LangGraph run on the Python sample with the knowledge-base step enabled."""
    from src.orchestration.graph import create_graph

    config = {
        "checkpoints": {"enabled": False},
        "hitl": {"enabled": False},
        "knowledge_base": {
            "enabled": True,
            "working_dir": str(tmp_path / "kb"),
            "wiki_dir": str(tmp_path / "wiki"),
            "embedding_provider": "hashing",
            "tokenizer": "bytes",
            "llm_provider": "none",
        },
    }
    graph = create_graph(config)
    assert "knowledge_base" in graph.graph.get_graph().nodes

    result = graph.run(
        source_language="python",
        target_language="java",
        source_path=os.path.join(project_root, "sample_data", "python"),
    )
    assert not result["errors"], result["errors"]
    kb = result["knowledge_base"]
    assert kb["files"] == result["total_files"]
    assert kb["entities"] > kb["files"], "AST entities should have been indexed alongside files"
    assert kb["wiki"]["pages"] == kb["entities"]
    assert (tmp_path / "wiki" / "index.md").exists()

    # Every AST entity now carries the file it came from (needed for the graph).
    for kind in ("classes", "functions"):
        for entity in result["parsed_entities"].get(kind, []):
            assert entity["file_path"].endswith("sample.py")

    # Without the flag the node is not part of the graph.
    plain = create_graph({"checkpoints": {"enabled": False}, "hitl": {"enabled": False}})
    assert "knowledge_base" not in plain.graph.get_graph().nodes


@requires_lightrag
def test_kb_cli_retrieve_and_stats(tmp_path, capsys):
    from src.orchestration.kb_cli import main as kb_main

    state = sample_state()
    config = offline_config(tmp_path)
    KnowledgeBase.run_with(lambda kb: kb.index_state(state), config)

    common = ["--dir", config.working_dir, "--embeddings", "hashing", "--llm", "none"]
    os.environ["KB_TOKENIZER"] = "bytes"
    try:
        assert kb_main(common + ["stats"]) == 0
        out = capsys.readouterr().out
        assert "Knowledge base" in out and "hashing" in out

        assert kb_main(common + ["--json", "retrieve", "PROCESS-PAYMENT", "--mode", "local"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert any(e["entity_name"] == "PAYMENT.cob::PROCESS-PAYMENT" for e in payload["entities"])

        assert kb_main(common + ["query", "needs an llm"]) == 1
        assert "No LLM configured" in capsys.readouterr().err
    finally:
        os.environ.pop("KB_TOKENIZER", None)
