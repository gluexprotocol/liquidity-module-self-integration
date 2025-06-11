import pytest
from decimal import Decimal
from modules.clipper_liquidity_module import MyProtocolLiquidityModule
from templates.liquidity_module import Token

@pytest.fixture
def clipper_module():
    return MyProtocolLiquidityModule()

@pytest.fixture
def pool_state():
    # Example pool state for Clipper with previousAllTokensBalance and days for APY
    return {
        "allTokensBalance": {
            "balances": [2000 * 1e18, 8000 * 1e6, 700 * 1e8],
            "tokens": [
                Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18")),
                Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14")),
                Token(address="0x2", symbol="ALT", decimals=8, reference_price=Decimal("1e16")),
            ],
            "totalSupply": 10000 * 1e18,
        },
        "previousAllTokensBalance": {
            "balances": [900 * 1e18, 4000 * 1e6, 100 * 1e8],
            "tokens": [
                Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18")),
                Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14")),
                Token(address="0x2", symbol="ALT", decimals=8, reference_price=Decimal("1e16")),
            ],
            "totalSupply": 9000 * 1e18,
        },
        "days": 30,
    }

# Normal case
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
            "balances": [123456789 * 1e6],
            "tokens": [
                Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14")),
            ],
            "totalSupply": 123456789 * 1e6,
        }
    }
    tvl = clipper_module.get_tvl(pool_state)
    expected = Decimal(123456789 * 1e6) * Decimal("3e14") / Decimal("1e6")
    assert tvl == expected

# Normal case
def test_get_apy_returns_decimal(clipper_module, pool_state):
    apy = clipper_module.get_apy(pool_state)
    expected = Decimal('239.7628757493876735584056342')
    assert isinstance(apy, Decimal)
    assert apy == expected

# Edge case: empty pool state
def test_get_apy_empty_pool(clipper_module):
    apy = clipper_module.get_apy({
        "allTokensBalance": {"balances": [], "tokens": [], "totalSupply": 0},
        "previousAllTokensBalance": {"balances": [], "tokens": [], "totalSupply": 0},
        "days": 0,
    })
    assert isinstance(apy, Decimal)
    assert apy == Decimal(0)

# Edge case: negative balances (should still return Decimal)
def test_get_apy_negative_balances(clipper_module):
    pool_state = {
        "allTokensBalance": {
            "balances": [-1000 * 1e18],
            "tokens": [Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))],
            "totalSupply": 0,
        },
        "previousAllTokensBalance": {
            "balances": [-1000 * 1e18],
            "tokens": [Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))],
            "totalSupply": 0,
        },
        "days": 0,
    }
    apy = clipper_module.get_apy(pool_state)
    assert isinstance(apy, Decimal)
    assert apy == Decimal(0)
