"""Mock-only MCP receipt tests. conftest uses a temporary empty vault."""
import pytest
from unittest.mock import AsyncMock
from mcp.types import CallToolResult
from mcp.server.fastmcp.exceptions import ToolError
from tools.grow.contract import GrowFailure

@pytest.mark.asyncio
async def test_grow_schema_exposes_content_range_and_required_fields():
    import server
    schema = next(t.inputSchema for t in await server.mcp.list_tools() if t.name == "grow")
    item = schema["$defs"]["GrowItem"]
    assert item["required"] == ["content"]
    assert item["additionalProperties"] is False
    number = item["properties"]["valence"]["anyOf"][0]
    assert number["minimum"] == 0 and number["maximum"] == 1

@pytest.mark.asyncio
@pytest.mark.parametrize("item", [{"content":"x","valence":-1}, {"content":2}, {"title":"x"}, {"content":"x","valence":True}])
async def test_invalid_items_fail_at_mcp_boundary_before_dispatch(monkeypatch, item):
    import server
    dispatch = AsyncMock()
    monkeypatch.setattr(server._t_grow, "dispatch", dispatch)
    with pytest.raises(ToolError):
        await server.mcp._tool_manager.get_tool("grow").run({"items":[item]})
    dispatch.assert_not_awaited()

@pytest.mark.asyncio
@pytest.mark.parametrize("kind,unknown", [("parameter_validation",False),("execution_failed",False),("execution_unknown",True)])
async def test_business_failure_is_error_with_explicit_category(monkeypatch, kind, unknown):
    import server
    monkeypatch.setattr(server._t_grow,"dispatch",AsyncMock(return_value=GrowFailure("fixed safe error",kind)))
    result = await server.mcp.call_tool("grow", {"items":[{"content":"x"}]})
    assert isinstance(result,CallToolResult) and result.isError
    assert result.structuredContent["failureClass"] == kind
    assert result.structuredContent["outcomeUnknown"] is unknown

@pytest.mark.asyncio
async def test_unexpected_execution_exception_is_unknown_not_success(monkeypatch):
    import server
    monkeypatch.setattr(server._t_grow,"dispatch",AsyncMock(side_effect=RuntimeError("private-provider-secret")))
    result = await server.grow(items=["x"])
    assert result.isError and result.structuredContent["outcomeUnknown"]
    assert "private-provider-secret" not in str(result)

@pytest.mark.asyncio
async def test_success_keeps_existing_receipt_and_content_verbatim(monkeypatch):
    import server
    dispatch=AsyncMock(return_value="1 item stored")
    monkeypatch.setattr(server._t_grow,"dispatch",dispatch)
    result=await server.mcp._tool_manager.get_tool("grow").run({"items":[{"content":" exact original ","valence":0.5}]})
    assert result == "1 item stored"
    assert dispatch.call_args.kwargs["items"] == [{"content":" exact original ","valence":0.5}]
