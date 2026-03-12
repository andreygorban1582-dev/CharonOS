"""Tests for charonos.cluster.ssh_manager."""

from charonos.cluster.ssh_manager import SSHClusterManager, SSHNode


def test_add_and_list_nodes():
    mgr = SSHClusterManager()
    mgr.add_node("10.0.0.1", label="node-a")
    mgr.add_node("10.0.0.2", label="node-b")

    assert mgr.node_count == 2
    hosts = [n.host for n in mgr.nodes]
    assert "10.0.0.1" in hosts
    assert "10.0.0.2" in hosts


def test_remove_node():
    mgr = SSHClusterManager()
    mgr.add_node("10.0.0.1")
    assert mgr.remove_node("10.0.0.1") is True
    assert mgr.node_count == 0


def test_remove_missing_node():
    mgr = SSHClusterManager()
    assert mgr.remove_node("nope") is False


def test_cluster_status_empty():
    mgr = SSHClusterManager()
    assert "0 nodes" in mgr.cluster_status()


def test_cluster_status_with_nodes():
    mgr = SSHClusterManager()
    mgr.add_node("10.0.0.1", label="alpha")
    status = mgr.cluster_status()
    assert "1 node" in status
    assert "alpha" in status


def test_ssh_node_display():
    node = SSHNode(host="h", port=22, username="u", label="lbl")
    assert node.display == "u@h:22 (lbl)"


def test_discover_keys_empty(tmp_path):
    mgr = SSHClusterManager(key_dir=str(tmp_path))
    assert mgr.discover_keys() == []


def test_discover_keys_finds_private(tmp_path):
    # Create a fake private key and its .pub companion
    (tmp_path / "id_rsa").write_text("PRIVATE")
    (tmp_path / "id_rsa.pub").write_text("PUBLIC")
    mgr = SSHClusterManager(key_dir=str(tmp_path))
    keys = mgr.discover_keys()
    assert len(keys) == 1
    assert "id_rsa" in keys[0]
    assert "pub" not in keys[0]
