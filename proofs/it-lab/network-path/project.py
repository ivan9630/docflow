"""Offline dependency graph diagnosis. No scans, credentials or network calls."""
from ipaddress import ip_address
from common import unique

def analyze(data):
    nodes = data["nodes"]
    ids = unique(nodes, "id")
    by_id = {n["id"]: n for n in nodes}
    for node in nodes:
        ip_address(node["ip"])
        if type(node["up"]) is not bool or not isinstance(node["depends_on"], list):
            raise ValueError("invalid node")
        if any(dep not in ids for dep in node["depends_on"]):
            raise ValueError("unknown dependency")
    visiting, visited, order = set(), set(), []
    def visit(node_id):
        if node_id in visiting:
            raise ValueError("dependency cycle")
        if node_id in visited:
            return
        visiting.add(node_id)
        for dep in by_id[node_id]["depends_on"]:
            visit(dep)
        visiting.remove(node_id)
        visited.add(node_id)
        order.append(node_id)
    for node_id in sorted(ids):
        visit(node_id)
    down = [node_id for node_id in order if not by_id[node_id]["up"]]
    return {"check_order": down, "observed_down": len(down),
            "warning": "Snapshot correlation only; root cause unproven"}

