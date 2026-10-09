import copy
from datetime import datetime, timezone
from magorch import contracts

PHASES = ("intake", "brief_normalization", "editorial_planning", "style_specification", 
          "design_system", "content_and_asset_production", "layout_assembly", "qa", 
          "revision", "final_render", "published", "failed", "cancelled")

class TransitionError(ValueError):
    pass

def advance(project, to, *, reason=""):
    if to not in PHASES:
        raise TransitionError(f"Unknown phase {to}")

    current = project.get("status", "intake")
    
    if current in ("published", "failed", "cancelled"):
        raise TransitionError(f"Cannot transition from terminal phase {current}")

    if to in ("failed", "cancelled"):
        # always allowed from non-terminal
        pass
    elif to == "brief_normalization":
        if current != "intake":
            raise TransitionError()
    elif to == "editorial_planning":
        if current != "brief_normalization":
            raise TransitionError()
        if project.get("creative_brief", {}).get("approval_status") != "approved":
            raise TransitionError()
    elif to == "style_specification":
        if current != "editorial_planning":
            raise TransitionError()
        if project.get("creative_brief", {}).get("approval_status") != "approved":
            raise TransitionError()
    elif to == "design_system":
        if current != "style_specification":
            raise TransitionError()
        if project.get("style_specification", {}).get("approval_status") != "approved":
            raise TransitionError()
    elif to == "content_and_asset_production":
        if current not in ("design_system", "revision"):
            raise TransitionError()
        if current == "design_system":
            if project.get("editorial_plan", {}).get("approval_status") != "approved":
                raise TransitionError()
            if project.get("design_system", {}).get("status") != "produced":
                raise TransitionError()
    elif to == "layout_assembly":
        if current not in ("content_and_asset_production", "revision"):
            raise TransitionError()
        if project.get("design_system", {}).get("status") != "produced":
            raise TransitionError()
    elif to == "qa":
        if current != "layout_assembly":
            raise TransitionError()
        if project.get("layout", {}).get("status") != "produced":
            raise TransitionError()
    elif to == "revision":
        if current != "qa":
            raise TransitionError()
        q = project.get("quality", {})
        if q.get("blocking_issues", 0) <= 0:
            raise TransitionError()
        revs = project.get("revision_cycles", {})
        if revs.get("count", 0) >= revs.get("max", 0):
            raise TransitionError()
    elif to == "final_render":
        if current != "qa":
            raise TransitionError()
        q = project.get("quality", {})
        if q.get("blocking_issues", -1) != 0 or not q.get("last_report_id"):
            raise TransitionError()
    elif to == "published":
        if current != "final_render":
            raise TransitionError()
        if project.get("publication", {}).get("status") != "rendered":
            raise TransitionError()
        q = project.get("quality", {})
        if not q.get("publication_approved", False):
            raise TransitionError()
        if q.get("blocking_issues", -1) != 0:
            raise TransitionError()
    else:
        raise TransitionError(f"Invalid transition from {current} to {to}")

    new_proj = copy.deepcopy(project)
    
    if to == "revision":
        revs = new_proj.setdefault("revision_cycles", {"count": 0, "max": project.get("revision_cycles", {}).get("max", 1)})
        revs["count"] += 1
        
    new_proj["status"] = to
    new_proj["revision"] = new_proj.get("revision", 0) + 1
    
    hist = new_proj.setdefault("history", [])
    hist.append({
        "at": datetime.now(timezone.utc).isoformat(),
        "from": current,
        "to": to,
        "reason": reason
    })
    
    contracts.validate(new_proj, "magazine_project/1")
    return new_proj
