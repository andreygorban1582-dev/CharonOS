"""SSH cluster manager for CharonOS.

Manages SSH connections to remote codespace / compute nodes.  Supports
adding hosts at runtime so the agent's cluster can grow dynamically.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import paramiko

logger = logging.getLogger(__name__)


@dataclass
class SSHNode:
    """Represents one node in the compute cluster."""

    host: str
    port: int = 22
    username: str = "root"
    key_path: Optional[str] = None
    label: Optional[str] = None

    @property
    def display(self) -> str:
        lbl = f" ({self.label})" if self.label else ""
        return f"{self.username}@{self.host}:{self.port}{lbl}"


class SSHClusterManager:
    """Manage a dynamic cluster of SSH-accessible compute nodes."""

    def __init__(self, key_dir: str = "~/.ssh") -> None:
        self._nodes: dict[str, SSHNode] = {}
        self._key_dir = os.path.expanduser(key_dir)

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------

    def add_node(
        self,
        host: str,
        *,
        port: int = 22,
        username: str = "root",
        key_path: Optional[str] = None,
        label: Optional[str] = None,
    ) -> SSHNode:
        """Register a new node.  Returns the SSHNode."""
        node = SSHNode(
            host=host,
            port=port,
            username=username,
            key_path=key_path,
            label=label,
        )
        self._nodes[host] = node
        logger.info("Cluster: added node %s", node.display)
        return node

    def remove_node(self, host: str) -> bool:
        if host in self._nodes:
            del self._nodes[host]
            logger.info("Cluster: removed node %s", host)
            return True
        return False

    @property
    def nodes(self) -> list[SSHNode]:
        return list(self._nodes.values())

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run_command(self, host: str, command: str, timeout: int = 30) -> str:
        """Execute a command on a single node and return stdout."""
        node = self._nodes.get(host)
        if node is None:
            raise ValueError(f"Unknown host: {host}")

        client = paramiko.SSHClient()
        client.load_system_host_keys()
        # Accept unknown hosts but log a warning (cluster nodes are
        # typically ephemeral codespace instances without pre-seeded
        # known_hosts entries).
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        connect_kwargs: dict = {
            "hostname": node.host,
            "port": node.port,
            "username": node.username,
            "timeout": timeout,
        }
        if node.key_path:
            connect_kwargs["key_filename"] = node.key_path

        try:
            client.connect(**connect_kwargs)
            _, stdout, stderr = client.exec_command(command, timeout=timeout)
            out = stdout.read().decode()
            err = stderr.read().decode()
            if err:
                logger.warning("stderr on %s: %s", host, err[:200])
            return out
        finally:
            client.close()

    def run_on_all(self, command: str, timeout: int = 30) -> dict[str, str]:
        """Run a command across every node.  Returns {host: stdout}."""
        results: dict[str, str] = {}
        for host in list(self._nodes):
            try:
                results[host] = self.run_command(host, command, timeout)
            except Exception as exc:
                logger.error("Command failed on %s: %s", host, exc)
                results[host] = f"ERROR: {exc}"
        return results

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------

    def discover_keys(self) -> list[str]:
        """List SSH key files found in the configured key directory."""
        key_dir = Path(self._key_dir)
        if not key_dir.is_dir():
            return []
        return [
            str(p)
            for p in key_dir.iterdir()
            if p.is_file() and not p.name.endswith(".pub")
        ]

    def cluster_status(self) -> str:
        """Return a human-readable cluster summary."""
        if not self._nodes:
            return "Cluster: 0 nodes registered."
        lines = [f"Cluster: {len(self._nodes)} node(s)"]
        for node in self._nodes.values():
            lines.append(f"  • {node.display}")
        return "\n".join(lines)
