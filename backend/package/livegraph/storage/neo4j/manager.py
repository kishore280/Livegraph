import threading
from collections.abc import Callable
from typing import Any

from neo4j import GraphDatabase as GD

_shared_neo4j_connection: "Neo4jConnectionManager | None" = None
_shared_neo4j_connection_lock = threading.Lock()


def neo4j_write(driver, query: Callable) -> Any:
    with driver.session() as session:
        return session.execute_write(query)


def neo4j_read(driver, cypher: str, **kwargs) -> list[dict[str, Any]]:
    with driver.session() as session:
        result = session.run(cypher, **kwargs)
        return [record.data() for record in result]


class Neo4jConnectionManager:
    def __init__(self):
        self.driver = None
        self.status = "closed"
        self._connect()

    def _connect(self):
        if self.driver and self._is_connected():
            return

        from livegraph.config import settings

        self.driver = GD.driver(settings.neo4j_uri, auth=(settings.neo4j_username, settings.neo4j_password))
        with self.driver.session() as session:
            session.run("RETURN 1")
        self.status = "open"

    def _is_connected(self) -> bool:
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception:
            return False

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver = None
            self.status = "closed"


def get_shared_neo4j_connection() -> Neo4jConnectionManager:
    global _shared_neo4j_connection
    if _shared_neo4j_connection is None or not _shared_neo4j_connection.driver:
        with _shared_neo4j_connection_lock:
            if _shared_neo4j_connection is None or not _shared_neo4j_connection.driver:
                _shared_neo4j_connection = Neo4jConnectionManager()
    return _shared_neo4j_connection
