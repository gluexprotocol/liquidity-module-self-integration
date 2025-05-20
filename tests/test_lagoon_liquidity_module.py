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
        "currentSharePrice": 2 * 10**18,
        "originSharePrice": 1 * 10**18,
        "days": 100,
        "vaultContractAddress": "0x1",
        "underlyingTokenAddress": "0x0",
        "tvl": Decimal("100000.0"),
    },
    # Edge: zero supply/assets
    {
        "totalAssets": 0,
        "totalSupply": 0,
        "currentSharePrice": 0,
        "originSharePrice": 0,
        "days": 1,
        "vaultContractAddress": "0x1",
        "underlyingTokenAddress": "0x0",
        "tvl": Decimal("0.0"),
    },
    # Edge: large values
    {
        "totalAssets": 10**30,
        "totalSupply": 10**30,
        "currentSharePrice": 10**30,
        "originSharePrice": 10**29,
        "days": 365,
        "vaultContractAddress": "0x1",
        "underlyingTokenAddress": "0x0",
        "tvl": Decimal("1e30"),
    },
    # Edge: days = 0 (should handle division by zero)
    {
        "totalAssets": 10_000 * 10**18,
        "totalSupply": 5_000 * 10**18,
        "currentSharePrice": 2 * 10**18,
        "originSharePrice": 1 * 10**18,
        "days": 0,
        "vaultContractAddress": "0x1",
        "underlyingTokenAddress": "0x0",
        "tvl": Decimal("100000.0"),
    },
])
def pool_state(request):
    return request.param

@pytest.fixture(params=[
    {"decimals": 18, "vaultContractAddress": "0x1", "underlyingTokenAddress": "0x0"},
    {"decimals": 6, "vaultContractAddress": "0x3", "underlyingTokenAddress": "0x2"},
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
        assert isinstance(shares, Decimal)
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
        assert isinstance(assets, Decimal)
        assert assets >= 0

def test_get_apy(lagoon_module, pool_state):
    should_raise = pool_state["days"] == 0
    if should_raise:
        with pytest.raises(Exception):
            lagoon_module.get_apy(pool_state)
    else:
        apy = lagoon_module.get_apy(pool_state)
        assert isinstance(apy, Decimal)
        assert apy >= 0

def test_get_tvl(lagoon_module, pool_state):
    tvl = lagoon_module.get_tvl(pool_state)
    assert isinstance(tvl, (Decimal, int, float))
    assert tvl >= 0
