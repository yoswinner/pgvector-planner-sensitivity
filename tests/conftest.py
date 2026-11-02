import os
import sys
import urllib.request

# CRITICAL TEST SUITE ISOLATION:
# Force DB_NAME to compression_aware_rag_test BEFORE any project modules read config
os.environ["DB_NAME"] = "compression_aware_rag_test"

import pytest
import psycopg
from src.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, get_db_name, get_db_connection_string
from src.database import get_connection, initialize_schema, clear_database, assert_test_database, TEST_DB_NAME

_OLLAMA_AVAILABLE = None
_POSTGRES_AVAILABLE = None

def is_ollama_available() -> bool:
    """Check if the local Ollama daemon is reachable within 500ms."""
    global _OLLAMA_AVAILABLE
    if _OLLAMA_AVAILABLE is not None:
        return _OLLAMA_AVAILABLE
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=0.5):
            _OLLAMA_AVAILABLE = True
    except Exception:
        _OLLAMA_AVAILABLE = False
    return _OLLAMA_AVAILABLE


def is_postgres_available() -> bool:
    """Check if the local PostgreSQL instance is reachable with configured credentials."""
    global _POSTGRES_AVAILABLE
    if _POSTGRES_AVAILABLE is not None:
        return _POSTGRES_AVAILABLE
    try:
        admin_conn_str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
        with psycopg.connect(admin_conn_str, autocommit=True, connect_timeout=1) as admin_conn:
            _POSTGRES_AVAILABLE = True
    except Exception:
        _POSTGRES_AVAILABLE = False
    return _POSTGRES_AVAILABLE


def pytest_runtest_setup(item):
    """
    Skip tests requiring live external services if those services are not reachable.
    Prevents tests from hanging or failing on socket timeouts.
    """
    if "external_service" in item.keywords or "ollama" in item.name.lower():
        if not is_ollama_available():
            pytest.skip("External Ollama daemon is offline (http://127.0.0.1:11434)")

    # Legacy prototype and exploratory tests requiring live Ollama daemon
    OLLAMA_DEPENDENT_TESTS = {
        # test_basic.py
        "test_embedding_dimension",
        "test_document_and_chunk_insertion_in_test_db",
        "test_exact_search_with_and_without_connection",
        "test_hnsw_index_creation_and_search",
        "test_execution_plan_verification",
        "test_benchmark_result_structure",
        # test_hnsw_experiment.py
        "test_hnsw_index_creation_and_sizing",
        "test_forced_plan_verification_asserts_index_scan",
        "test_run_hnsw_benchmark_mini",
        # test_ingestion_cache.py
        "test_ingest_dataset_into_test_database",
        # test_representations.py
        "test_populate_and_validate_representations",
        "test_exact_search_fp32_and_halfvec",
        "test_storage_metrics_structure",
        "test_query_plans_use_sequential_scan",
        "test_run_representation_benchmark_mini",
        # test_scale_experiment.py
        "test_exact_search_plan_verification_enforces_seq_scan",
    }

    if item.name in OLLAMA_DEPENDENT_TESTS:
        if not is_ollama_available():
            pytest.skip("Test requires live Ollama embedding daemon (offline)")


@pytest.fixture(scope="session", autouse=True)
def ensure_test_database_ready():
    """
    Session-level fixture:
    1. Verifies that DB_NAME is strictly compression_aware_rag_test.
    2. Ensures compression_aware_rag_test database exists in PostgreSQL if reachable.
    3. Initializes the required schema within compression_aware_rag_test.
    Never touches or falls back to compression_aware_rag.
    """
    if get_db_name() != TEST_DB_NAME:
        raise RuntimeError(
            f"FATAL: get_db_name() is '{get_db_name()}', expected '{TEST_DB_NAME}'. "
            f"Test execution aborted to prevent accidental production database mutation."
        )

    if not is_postgres_available():
        # Research unit tests run offline without requiring live PostgreSQL daemon
        yield
        return

    # Check if database exists, create if missing
    admin_conn_str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
    with psycopg.connect(admin_conn_str, autocommit=True) as admin_conn:
        with admin_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (TEST_DB_NAME,))
            if not cur.fetchone():
                cur.execute(f"CREATE DATABASE {TEST_DB_NAME};")

    # Connect to test DB and ensure schema is initialized
    conn = get_connection()
    try:
        assert_test_database(conn)
        initialize_schema(conn=conn)
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def fail_closed_test_db_guard(request):
    """
    Autouse fixture executed before each test:
    Fail-closed guard ensuring the active database is strictly compression_aware_rag_test.
    Aborts test execution immediately if targeting any other database.
    """
    active_env_db = os.environ.get("DB_NAME")
    if active_env_db != TEST_DB_NAME:
        pytest.fail(
            f"FAIL-CLOSED SAFETY GUARD TRIGGERED: os.environ['DB_NAME'] is '{active_env_db}', "
            f"not '{TEST_DB_NAME}'. Aborting to prevent production database mutation."
        )

    if not is_postgres_available():
        if "clean_test_db" in request.fixturenames:
            pytest.skip("Test requires live PostgreSQL test database (offline or unauthenticated)")
        return

    conn = get_connection()
    try:
        assert_test_database(conn)
    finally:
        conn.close()


@pytest.fixture
def clean_test_db():
    """
    Fixture providing a clean test database.
    Confines truncation strictly to compression_aware_rag_test.
    """
    if not is_postgres_available():
        pytest.skip("Test requires live PostgreSQL test database (offline or unauthenticated)")
    assert_test_database()
    clear_database()
    yield
    assert_test_database()
    clear_database()
