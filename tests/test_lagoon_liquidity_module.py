import pytest
from decimal import Decimal
from modules.lagoon_liquidity_module import LagoonLiquidityModule
from templates.liquidity_module import Token

@pytest.fixture
def lagoon_module():
    return LagoonLiquidityModule()

@pytest.fixture(params=[
    # Normal case
    {
        "totalAssets": 10_000 * 10**18,
        "totalSupply": 5_000 * 10**18,
        "days": 100,
        "vaultContractAddress": "0x1",
        "underlyingTokenAddress": "0x0",
        "totalAssetsBefore": 9_000 * 10**18,
        "totalSupplyBefore": 4_500 * 10**18,
        "underlyingTokenDecimals": 18,
    },
    # Edge: zero supply/assets
    {
        "totalAssets": 0,
        "totalSupply": 0,
        "days": 1,
        "vaultContractAddress": "0x1",
        "underlyingTokenAddress": "0x0",
        "totalAssetsBefore": 0,
        "totalSupplyBefore": 0,
        "underlyingTokenDecimals": 18,
    },
    # Edge: large values
    {
        "totalAssets": 10**30,
        "totalSupply": 10**30,
        "days": 365,
        "vaultContractAddress": "0x1",
        "underlyingTokenAddress": "0x0",
        "totalAssetsBefore": 10**29,
        "totalSupplyBefore": 10**29,
        "underlyingTokenDecimals": 18,
    },
    # Edge: days = 0 (should handle division by zero)
    {
        "totalAssets": 10_000 * 10**18,
        "totalSupply": 5_000 * 10**18,
        "days": 0,
        "vaultContractAddress": "0x1",
        "underlyingTokenAddress": "0x0",
        "totalAssetsBefore": 9_000 * 10**18,
        "totalSupplyBefore": 4_500 * 10**18,
        "underlyingTokenDecimals": 18,
    },
])
def pool_state(request):
    return request.param

@pytest.fixture(params=[
    {"shareTokenDecimals": 18, "vaultContractAddress": "0x1", "underlyingTokenAddress": "0x0"},
    {"shareTokenDecimals": 6, "vaultContractAddress": "0x3", "underlyingTokenAddress": "0x2"},
])
def fixed_parameters(request):
    return request.param

@pytest.fixture(params=[
    Token(symbol="ETH", address="0x0", decimals=18, reference_price=1.0),
    Token(symbol="USDC", address="0x2", decimals=6, reference_price=0.0003),
])
def asset_token(request):
    return request.param

@pytest.fixture(params=[
    Token(symbol="LAG", address="0x1", decimals=18, reference_price=0.5),
    Token(symbol="ALT", address="0x3", decimals=8, reference_price=0.01),
])
def share_token(request):
    return request.param

@pytest.mark.parametrize("input_amount", [1 * 10**18, 0, -1 * 10**18, 10**30])
def test_get_deposit_amount(lagoon_module, pool_state, fixed_parameters, asset_token, share_token, input_amount):
    valid_input = asset_token.address == fixed_parameters["underlyingTokenAddress"]
    should_raise = (
        pool_state["totalAssets"] == 0 or
        pool_state["totalSupply"] == 0 or
        pool_state["days"] == 0 or
        input_amount < 0 or
        not valid_input
    )
    if should_raise:
        with pytest.raises(Exception):
            lagoon_module.get_amount_out(pool_state, fixed_parameters, asset_token, share_token, input_amount)
    else:
        fee, shares = lagoon_module.get_amount_out(pool_state, fixed_parameters, asset_token, share_token, input_amount)
        assert fee is None
        assert isinstance(shares, int)
        assert shares >= 0

@pytest.mark.parametrize("input_amount", [1 * 10**18, 0, -1 * 10**18, 10**30])
def test_get_redeem_amount(lagoon_module, pool_state, fixed_parameters, share_token, asset_token, input_amount):
    valid_input = share_token.address == fixed_parameters["vaultContractAddress"]
    should_raise = (
        pool_state["totalAssets"] == 0 or
        pool_state["totalSupply"] == 0 or
        pool_state["days"] == 0 or
        input_amount < 0 or
        not valid_input
    )
    if should_raise:
        with pytest.raises(Exception):
            lagoon_module.get_amount_in(pool_state, fixed_parameters, share_token, asset_token, input_amount)
    else:
        fee, assets = lagoon_module.get_amount_in(pool_state, fixed_parameters, share_token, asset_token, input_amount)
        assert fee is None
        assert isinstance(assets, int)
        assert assets >= 0

def test_get_apy(lagoon_module, pool_state):
    apy = lagoon_module.get_apy(pool_state)
    assert isinstance(apy, Decimal)
    if pool_state["days"] == 0:
        assert apy == Decimal(0)
    else:
        assert apy >= 0

def test_get_tvl(lagoon_module, pool_state, asset_token):
    tvl = lagoon_module.get_tvl(pool_state, asset_token)
    assert isinstance(tvl, Decimal)
    assert tvl >= 0

def test_get_tvl_various_decimals(lagoon_module, pool_state):
    # Token with decimals less than 18
    token_6 = Token(symbol="USDC6", address="0x6", decimals=6, reference_price=0.0003)
    tvl_6 = lagoon_module.get_tvl(pool_state, token_6)
    # Should scale down by 10**12
    expected_6 = Decimal(pool_state.get("totalAssets", 0)) / Decimal(10) ** 12
    assert tvl_6 == expected_6

    # Token with decimals exactly 18
    token_18 = Token(symbol="ETH18", address="0x18", decimals=18, reference_price=1.0)
    tvl_18 = lagoon_module.get_tvl(pool_state, token_18)
    # Should be unchanged
    expected_18 = Decimal(pool_state.get("totalAssets", 0))
    assert tvl_18 == expected_18

    # Token with decimals more than 18
    token_24 = Token(symbol="BIG24", address="0x24", decimals=24, reference_price=0.000001)
    tvl_24 = lagoon_module.get_tvl(pool_state, token_24)
    # Should scale up by 10**6
    expected_24 = Decimal(pool_state.get("totalAssets", 0)) * Decimal(10) ** 6
    assert tvl_24 == expected_24
