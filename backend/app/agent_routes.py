from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .agent_tools import AgentToolCatalogRead, ToolInvocationException, ToolInvocationRequest, ToolInvocationResponse, catalog, error_response, invoke
from .database import get_db
from .deps import get_current_user
from .models import User


router = APIRouter(prefix="/api/v1/agent", tags=["agent-tools"])


@router.get("/tools", response_model=AgentToolCatalogRead)
def list_agent_tools(db: Session = Depends(get_db)) -> AgentToolCatalogRead:
    get_current_user(db)
    return catalog()


@router.post("/tools/{tool_name}/invoke", response_model=ToolInvocationResponse)
def invoke_agent_tool(
    tool_name: str,
    payload: Any = Body(...),
    db: Session = Depends(get_db),
) -> ToolInvocationResponse | JSONResponse:
    user: User = get_current_user(db)
    try:
        request = ToolInvocationRequest.model_validate(payload)
    except ValidationError as error:
        response = error_response(
            tool_name,
            ToolInvocationException(
                422,
                "invalid_invocation",
                "The invocation envelope must contain valid arguments and confirmed fields.",
                [{"loc": list(item["loc"]), "msg": item["msg"], "type": item["type"]} for item in error.errors()],
            ),
        )
        return JSONResponse(status_code=422, content=response.model_dump(mode="json"))
    try:
        return invoke(db, user, tool_name, request)
    except ToolInvocationException as error:
        response = error_response(tool_name, error)
        return JSONResponse(status_code=error.status_code, content=response.model_dump(mode="json"))
