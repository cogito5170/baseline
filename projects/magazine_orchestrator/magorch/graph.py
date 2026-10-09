class PlanError(ValueError):
    pass

def topological_order(edges, allow_missing=False):
    visited = {}
    order = []
    path = []
    
    def visit(node):
        if visited.get(node) == 1:
            idx = path.index(node)
            cycle = path[idx:] + [node]
            raise PlanError(f"Cycle detected involving {' -> '.join(cycle)}")
        if visited.get(node) == 2:
            return
            
        visited[node] = 1
        path.append(node)
        
        deps = edges.get(node, [])
        for dep in sorted(deps):
            if dep not in edges:
                if not allow_missing:
                    raise PlanError(f"Unknown dependency {dep} for node {node}")
            else:
                visit(dep)
        
        path.pop()
        visited[node] = 2
        order.append(node)

    for node in sorted(edges.keys()):
        if node not in visited:
            visit(node)
            
    return order

def descendants(edges, node):
    rev = {}
    for n, deps in edges.items():
        for d in deps:
            rev.setdefault(d, []).append(n)
            
    desc = set()
    queue = [node]
    while queue:
        curr = queue.pop(0)
        for child in rev.get(curr, []):
            if child not in desc:
                desc.add(child)
                queue.append(child)
    return desc
