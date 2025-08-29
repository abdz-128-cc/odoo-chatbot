# schemas/state_schema.py

from typing import TypedDict, List, Optional, Any

class BaseChatState(TypedDict):
    input: Optional[str]
    output: Optional[str]
    source_documents: Optional[List[Any]]
