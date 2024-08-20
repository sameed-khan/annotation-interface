import pytest
from litestar import Litestar
from litestar.status_codes import HTTP_200_OK
from litestar.testing import AsyncTestClient

from app.domain import urls

pytestmark = pytest.mark.anyio


async def test_sanity(client: AsyncTestClient[Litestar]):
    response = await client.get(urls.CHECK_HEALTH)
    assert response.status_code == HTTP_200_OK
