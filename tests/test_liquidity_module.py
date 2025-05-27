import pytest
from unittest.mock import Mock, patch

from decimal import Decimal
from typing import Any
from httpx import Response, Headers
from templates.liquidity_module import Token
from modules.renegade_liquidity_module import RenegadeLiquidityModule

from renegade import ExternalMatchClient
from renegade.http import RelayerHttpClient

import time

# =============================================================================
# Constants
# =============================================================================

API_KEY = "test_api_key"
QUOTE_ENDPOINT: str = "/v0/matching-engine/quote"
ASSEMBLE_ENDPOINT: str = "/v0/matching-engine/assemble-external-match"

WETH_ADDRESS = "0x82af49447d8a07e3bd95bd0d56f35241523fbab1"
USDC_ADDRESS = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"

BASE_AMOUNT = 1_000_000_000_000_000_000
QUOTE_AMOUNT = 2_000_000_000

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def weth_token():
    """Fixture that provides a WETH token."""
    return Token(
        address=WETH_ADDRESS,
        symbol="WETH",
        decimals=18,
        reference_price=Decimal("2000")
    )

@pytest.fixture
def usdc_token():
    """Fixture that provides a USDC token."""
    return Token(
        address=USDC_ADDRESS,
        symbol="USDC",
        decimals=6,
        reference_price=Decimal("1")
    )

@pytest.fixture
def make_quote_response():
    """Factory fixture that creates quote responses for a given side."""
    def _make_quote_response(side: str):
        api_quote = {
            "order": {
                "quote_mint": USDC_ADDRESS,
                "base_mint": WETH_ADDRESS,
                "side": side,
                "base_amount": BASE_AMOUNT if side == "Sell" else None,
                "quote_amount": QUOTE_AMOUNT if side == "Buy" else None
            },
            "match_result": {
                "quote_mint": USDC_ADDRESS,
                "base_mint": WETH_ADDRESS,
                "quote_amount": QUOTE_AMOUNT,
                "base_amount": BASE_AMOUNT,
                "direction": side
            },
            "fees": {
                "relayer_fee": 0,
                "protocol_fee": 0
            },
            "send": {
                "mint": USDC_ADDRESS if side == "Buy" else WETH_ADDRESS,
                "amount": QUOTE_AMOUNT if side == "Buy" else BASE_AMOUNT
            },
            "receive": {
                "mint": WETH_ADDRESS if side == "Buy" else USDC_ADDRESS,
                "amount": BASE_AMOUNT if side == "Buy" else QUOTE_AMOUNT
            },
            "price": {
                "price": "2000.0",
                "timestamp": int(time.time() * 1000)
            },
            "timestamp": int(time.time() * 1000)
        }

        signed_quote = {
            "quote": api_quote,
            "signature": "0x123"
        }

        return { "signed_quote": signed_quote }
    return _make_quote_response

@pytest.fixture
def make_assemble_response():
    """Factory fixture that creates assemble responses for a given side."""
    def _make_assemble_response(side: str):
        bundle = {
            "match_result": {
                "quote_mint": USDC_ADDRESS,
                "base_mint": WETH_ADDRESS,
                "quote_amount": QUOTE_AMOUNT,
                "base_amount": BASE_AMOUNT,
                "direction": side
            },
            "fees": {
                "relayer_fee": 0,
                "protocol_fee": 0
            },
            "send": {
                "mint": USDC_ADDRESS if side == "Buy" else WETH_ADDRESS,
                "amount": QUOTE_AMOUNT if side == "Buy" else BASE_AMOUNT
            },
            "receive": {
                "mint": WETH_ADDRESS if side == "Buy" else USDC_ADDRESS,
                "amount": BASE_AMOUNT if side == "Buy" else QUOTE_AMOUNT
            },
            "settlement_tx": {
                "data": "0x123456789abcdef",
                "to": "0xdef0123456789abcdef0123456789abcdef0123",
                "value": "0",
            }
        }

        return { "match_bundle": bundle }
    return _make_assemble_response

@pytest.fixture
def mock_http_client(make_quote_response, make_assemble_response):
    """Fixture that provides a mocked RelayerHttpClient with endpoint-specific responses."""
    def _make_client(side: str, return_none: bool = False):
        with patch('renegade.http.RelayerHttpClient') as mock_client:
            mock_instance = Mock(spec=RelayerHttpClient)
            mock_client.return_value = mock_instance
            
            def post_with_headers(path: str, _body: Any, _headers: Headers) -> Response:
                response = Mock(spec=Response)
                response.status_code = 200

                # Return 204 if return_none is True
                if return_none:
                    response.status_code = 204
                    response.json = {}
                    return response

                # Return a quote or assemble response
                if path.startswith(QUOTE_ENDPOINT):
                    response.json.return_value = make_quote_response(side)
                elif path.startswith(ASSEMBLE_ENDPOINT):
                    response.json.return_value = make_assemble_response(side)
                else:
                    raise ValueError(f"Unexpected endpoint: {path}")
                
                return response
            
            mock_instance.post_with_headers.side_effect = post_with_headers
            return mock_instance
    return _make_client

@pytest.fixture
def make_external_match_client(mock_http_client):
    """Factory fixture that creates ExternalMatchClient with configured mocks."""
    def _make_client(side: str, return_none: bool = False):
        client = ExternalMatchClient.__new__(ExternalMatchClient)
        client.http_client = mock_http_client(side, return_none)
        client.api_key = API_KEY
        return client
    return _make_client

@pytest.fixture
def make_renegade_liquidity_module(make_external_match_client):
    """Factory fixture that creates RenegadeLiquidityModule with configured mocks."""
    def _make_module(side: str, return_none: bool = False):
        renegade_module = RenegadeLiquidityModule.__new__(RenegadeLiquidityModule)
        renegade_module._get_client = lambda _params: make_external_match_client(side, return_none)
        return renegade_module
    return _make_module

# =============================================================================
# Tests
# =============================================================================

@pytest.mark.asyncio
async def test_get_amount_out__buy_side(usdc_token, weth_token, make_renegade_liquidity_module):
    """Test the get_sell_quote method of the RenegadeLiquidityModule."""
    renegade_liquidity_module = make_renegade_liquidity_module("Buy")
    fixed_parameters = {}

    input_token, output_token, input_amount = usdc_token, weth_token, QUOTE_AMOUNT
    fee, amount_out, _quote = await renegade_liquidity_module.get_sell_quote(fixed_parameters, input_token, output_token, input_amount)

    assert fee == 0
    assert amount_out == BASE_AMOUNT

@pytest.mark.asyncio
async def test_get_amount_out__sell_side(usdc_token, weth_token, make_renegade_liquidity_module):
    """Test the get_sell_quote method of the RenegadeLiquidityModule."""
    renegade_liquidity_module = make_renegade_liquidity_module("Sell")
    fixed_parameters = {}

    input_token, output_token, input_amount = weth_token, usdc_token, BASE_AMOUNT
    fee, amount_out, _quote = await renegade_liquidity_module.get_sell_quote(fixed_parameters, input_token, output_token, input_amount)

    assert fee == 0
    assert amount_out == QUOTE_AMOUNT

@pytest.mark.asyncio
async def test_get_amount_in__buy_side(usdc_token, weth_token, make_renegade_liquidity_module):
    """Test the get_buy_quote method of the RenegadeLiquidityModule."""
    renegade_liquidity_module = make_renegade_liquidity_module("Buy")
    fixed_parameters = {}

    input_token, output_token, output_amount = usdc_token, weth_token, BASE_AMOUNT
    fee, amount_in, _quote = await renegade_liquidity_module.get_buy_quote(fixed_parameters, input_token, output_token, output_amount)

    assert fee == 0
    assert amount_in == QUOTE_AMOUNT

@pytest.mark.asyncio
async def test_get_amount_in__sell_side(usdc_token, weth_token, make_renegade_liquidity_module):
    """Test the get_buy_quote method of the RenegadeLiquidityModule."""
    renegade_liquidity_module = make_renegade_liquidity_module("Sell")
    fixed_parameters = {}

    input_token, output_token, output_amount = weth_token, usdc_token, QUOTE_AMOUNT
    fee, amount_in, _quote = await renegade_liquidity_module.get_buy_quote(fixed_parameters, input_token, output_token, output_amount)

    assert fee == 0
    assert amount_in == BASE_AMOUNT

@pytest.mark.asyncio
async def test_non_usdc_pair(weth_token, make_renegade_liquidity_module):
    """Test the get_sell_quote method of the RenegadeLiquidityModule."""
    renegade_liquidity_module = make_renegade_liquidity_module("Buy")
    fixed_parameters = {}


    input_token, input_amount = weth_token, BASE_AMOUNT
    output_token = Token(address="0x123", symbol="TEST", decimals=18, reference_price=Decimal("1"))
    fee, amount_out, _quote = await renegade_liquidity_module.get_sell_quote(fixed_parameters, input_token, output_token, input_amount)

    assert fee is None
    assert amount_out is None
    
@pytest.mark.asyncio
async def test_no_quote_available(usdc_token, weth_token, make_renegade_liquidity_module):
    """Test the get_buy_quote method of the RenegadeLiquidityModule."""
    renegade_liquidity_module = make_renegade_liquidity_module("Buy", return_none=True)
    fixed_parameters = {}

    input_token, output_token, input_amount = weth_token, usdc_token, BASE_AMOUNT
    fee, amount_out, _quote = await renegade_liquidity_module.get_sell_quote(fixed_parameters, input_token, output_token, input_amount)

    assert fee is None
    assert amount_out is None

@pytest.mark.asyncio
async def test_assemble_quote(usdc_token, weth_token, make_renegade_liquidity_module):
    """Test the assemble_quote method of the RenegadeLiquidityModule."""
    # Create the module with Buy side
    renegade_liquidity_module = make_renegade_liquidity_module("Buy")
    fixed_parameters = {}

    # First get a quote
    input_token, output_token, input_amount = usdc_token, weth_token, QUOTE_AMOUNT
    fee, amount_out, quote = await renegade_liquidity_module.get_sell_quote(
        fixed_parameters, input_token, output_token, input_amount
    )
    assert amount_out == BASE_AMOUNT
    
    # Assemble the quote into calldata
    fee, amount, bundle = await renegade_liquidity_module.assemble_quote(fixed_parameters, quote)
    assert fee == 0
    assert amount == BASE_AMOUNT
    assert bundle is not None

