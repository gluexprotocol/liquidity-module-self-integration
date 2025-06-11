import pytest
from decimal import Decimal
from modules.clipper_liquidity_module import MyProtocolLiquidityModule
from templates.liquidity_module import Token

@pytest.fixture
def clipper_module():
    return MyProtocolLiquidityModule()

@pytest.fixture
def pool_state():
    # Example pool state for Clipper
    return {
        "allTokensBalance": {
            "balances": [1000 * 10**18, 5000 * 10**6, 200 * 10**8],
            "tokens": [
                Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18")),
                Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14")),
                Token(address="0x2", symbol="ALT", decimals=8, reference_price=Decimal("1e16")),
            ],
            "totalSupply": 10000 * 10**18,
        }
    }

def test_get_tvl(clipper_module, pool_state):
    tvl = clipper_module.get_tvl(pool_state)
    expected = Decimal(0)
    for i, token in enumerate(pool_state["allTokensBalance"]["tokens"]):
        balance = pool_state["allTokensBalance"]["balances"][i]
        balance = Decimal(balance) * token.reference_price / Decimal(10 ** token.decimals)
        expected += balance
    assert tvl == expected, f"tvl={tvl}, expected={expected}"

# Edge case: zero balances
def test_get_tvl_zero_balances(clipper_module):
    pool_state = {
        "allTokensBalance": {
            "balances": [0, 0, 0],
            "tokens": [
                Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18")),
                Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14")),
                Token(address="0x2", symbol="ALT", decimals=8, reference_price=Decimal("1e16")),
            ],
            "totalSupply": 0,
        }
    }
    tvl = clipper_module.get_tvl(pool_state)
    assert tvl == 0

# Edge case: single token
def test_get_tvl_single_token(clipper_module):
    pool_state = {
        "allTokensBalance": {
            "balances": [123456789 * 10**6],
            "tokens": [
                Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14")),
            ],
            "totalSupply": 123456789 * 10**6,
        }
    }
    tvl = clipper_module.get_tvl(pool_state)
    expected = Decimal(123456789 * 10**6) * Decimal("3e14") / Decimal(10**6)
    assert tvl == expected
