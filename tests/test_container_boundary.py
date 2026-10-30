import httpx
from fastapi.testclient import TestClient

from council.config import Settings
from council.main import create_app


def test_bridge_forwarding_requires_explicit_local_proxy_mode(tmp_path):
    import asyncio

    async def get(settings):
        transport = httpx.ASGITransport(app=create_app(settings), client=("172.18.0.1", 12345))
        async with httpx.AsyncClient(
            transport=transport, base_url="http://127.0.0.1:8090"
        ) as client:
            return await client.get("/v1/assessments")

    assert asyncio.run(get(Settings(data_dir=tmp_path))).status_code == 403
    assert (
        asyncio.run(get(Settings(data_dir=tmp_path, trust_loopback_proxy=True))).status_code == 200
    )
    with TestClient(create_app(Settings(data_dir=tmp_path, trust_loopback_proxy=True))) as client:
        assert (
            client.get("/v1/assessments", headers={"Host": "attacker.example"}).status_code == 400
        )
