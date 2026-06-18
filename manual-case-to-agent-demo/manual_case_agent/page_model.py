import json
from collections import deque
from pathlib import Path


class PageModel:
    def __init__(self, raw: dict):
        self.raw = raw
        self.pages = raw["pages"]
        self.aliases = raw.get("aliases", {})
        self.transitions = raw.get("transitions", [])
        self.back_map = raw.get("backMap", {})

    @classmethod
    def from_json(cls, path: str | Path) -> "PageModel":
        with Path(path).open("r", encoding="utf-8") as f:
            return cls(json.load(f))

    def default_start_page(self) -> str:
        return self.raw.get("defaultStartPage", "HomePage")

    def resolve_page(self, text: str) -> str | None:
        for alias, page in self.aliases.get("pages", {}).items():
            if alias in text:
                return page
        return None

    def page_assertion(self, page: str) -> dict:
        return self.pages.get(page, {}).get("assertion", {"page": page, "type": "visible"})

    def resolve_control(self, page: str, text: str) -> dict | None:
        controls = self.pages.get(page, {}).get("controls", {})
        candidates = []
        for control_id, control in controls.items():
            names = [control_id, control.get("name", "")]
            names.extend(control.get("aliases", []))
            if any(name and name in text for name in names):
                candidates.append((control_id, control))

        if not candidates:
            return None
        if len(candidates) > 1:
            return {
                "ambiguous": True,
                "candidates": [item[0] for item in candidates],
            }

        control_id, control = candidates[0]
        return {
            "ambiguous": False,
            "id": control_id,
            "name": control.get("name", control_id),
            "role": control.get("role", "unknown"),
            "locator": control.get("locator", {}),
        }

    def get_control(self, page: str, control_id: str) -> dict | None:
        control = self.pages.get(page, {}).get("controls", {}).get(control_id)
        if not control:
            return None
        return {
            "ambiguous": False,
            "id": control_id,
            "name": control.get("name", control_id),
            "role": control.get("role", "unknown"),
            "locator": control.get("locator", {}),
        }

    def shortest_path(self, start_page: str, target_page: str) -> list[dict] | None:
        if start_page == target_page:
            return []

        graph = {}
        for edge in self.transitions:
            graph.setdefault(edge["from"], []).append(edge)

        queue = deque([(start_page, [])])
        visited = {start_page}

        while queue:
            page, path = queue.popleft()
            for edge in graph.get(page, []):
                next_page = edge["to"]
                if next_page in visited:
                    continue
                next_path = path + [edge]
                if next_page == target_page:
                    return next_path
                visited.add(next_page)
                queue.append((next_page, next_path))
        return None

    def click_next_page(self, page: str, control_id: str) -> str | None:
        for edge in self.transitions:
            if edge["from"] == page and edge["via"] == control_id:
                return edge["to"]
        return None

    def back_page(self, current_page: str) -> str:
        return self.back_map.get(current_page, self.default_start_page())
