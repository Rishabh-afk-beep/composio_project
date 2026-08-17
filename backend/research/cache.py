from backend.db.sqlite import get_cached_request, set_cached_request
import json
from typing import Any, Optional

def get_cache(key: str) -> Optional[Any]:
    data = get_cached_request(key)
    if data:
        try:
            return json.loads(data)
        except:
            return data
    return None

def set_cache(key: str, data: Any):
    if not isinstance(data, str):
        data = json.dumps(data)
    set_cached_request(key, data)
