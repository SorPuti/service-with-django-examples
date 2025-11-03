from typing import Dict, Tuple, Any, List
from django.db.models import Q


def build_filters_from_params(params: Dict[str, Any], allowmap: Dict[str, str]) -> Tuple[Q, Dict[str, Any]]:
    q = Q()
    kwargs: Dict[str, Any] = {}

    for key, val in params.items():
        if key in ("ordering", "page", "limit", "offset", "q"):
            continue

        # detecta negacao
        if key.endswith("_not"):
            base_key = key[:-4]
            if base_key not in allowmap:
                continue
            lookup = allowmap[base_key]
            q &= ~Q(**{lookup: val})
            continue

        # chave normal
        if key not in allowmap:
            continue

        lookup = allowmap[key]

        # suporte CSV
        if isinstance(val, str) and "," in val:
            kwargs[f"{lookup}__in"] = [v.strip() for v in val.split(",") if v.strip()]
        else:
            # suporte booleano
            if isinstance(val, str) and val.lower() in ("1", "0", "true", "false", "yes", "no"):
                kwargs[lookup] = val.lower() in ("1", "true", "yes")
            else:
                kwargs[lookup] = val

    return q, kwargs



def build_search_q(text: str, fields: List[str]) -> Q:
    """Build a Q object that ORs icontains lookups over the provided fields."""
    q = Q()
    if not text:
        return q
    for f in fields:
        q |= Q(**{f + "__icontains": text})
    return q


def sanitize_ordering(ordering_param: str, allowed: List[str]):
    """Return ordering string if allowed, else None. Supports leading '-'"""
    if not ordering_param:
        return None
    field = ordering_param
    desc = False
    if ordering_param.startswith("-"):
        desc = True
        field = ordering_param[1:]
    if field not in allowed:
        return None
    return f"-{field}" if desc else field
