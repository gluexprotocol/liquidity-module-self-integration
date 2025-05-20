import pytest
from decimal import Decimal
from modules.yoprotocol_liquidity_module import YoProtocolLiquidityModule, Constant
from templates.liquidity_module import Token

@pytest.fixture
def sample_tokens():
    underlying = Token(
        address=Constant.OPTIMISM_WETH,
        symbol="WETH",
        decimals=18,
        reference_price=Decimal("1.0")
    )
    shares = Token(
        address="0xSHARES",
        symbol="yETH",
        decimals=18,
        reference_price=Decimal("1.0")
    )
    return underlying, shares

@pytest.fixture
def sample_pool_state():
    return {
        "totalAssets": 1000 * 10**18,
        "totalSupply": 500 * 10**18,
        "underlyingTokenAddress": Constant.OPTIMISM_WETH,
        "sharesTokenAddress": "0xSHARES",
        "currentSharePrice": str(2 * 10**18),
        "originSharePrice": str(1 * 10**18),  # changed key to match source
        "days": 10,  # changed key to match source
        "tvl": Decimal("1000.0")  # ensure tvl is present and Decimal
    }

@pytest.fixture
def sample_fixed_parameters():
    return {
        "decimals": 18,
        "underlyingTokenAddress": Constant.OPTIMISM_WETH,
        "sharesTokenAddress": "0xSHARES"
    }

def test_get_amount_out_underlying_to_shares(sample_tokens, sample_pool_state, sample_fixed_parameters):
    underlying, shares = sample_tokens
    module = YoProtocolLiquidityModule()
    input_amount = 10 * 10**18
    _, out = module.get_amount_out(sample_pool_state, sample_fixed_parameters, underlying, shares, input_amount)
    assert isinstance(out, int)
    assert out > 0

def test_get_amount_out_shares_to_underlying(sample_tokens, sample_pool_state, sample_fixed_parameters):
    underlying, shares = sample_tokens
    module = YoProtocolLiquidityModule()
    input_amount = 10 * 10**18
    _, out = module.get_amount_out(sample_pool_state, sample_fixed_parameters, shares, underlying, input_amount)
    assert isinstance(out, int)
    assert out > 0

def test_get_amount_out_invalid_token(sample_tokens, sample_pool_state, sample_fixed_parameters):
    underlying, shares = sample_tokens
    module = YoProtocolLiquidityModule()
    fake_token = Token(address="0xBAD", symbol="BAD", decimals=18, reference_price=Decimal("1.0"))
    with pytest.raises(ValueError):
        module.get_amount_out(sample_pool_state, sample_fixed_parameters, fake_token, shares, 1)

def test_get_amount_in_underlying_to_shares(sample_tokens, sample_pool_state, sample_fixed_parameters):
    underlying, shares = sample_tokens
    module = YoProtocolLiquidityModule()
    output_amount = 10 * 10**18
    _, out = module.get_amount_in(sample_pool_state, sample_fixed_parameters, underlying, shares, output_amount)
    assert isinstance(out, int)

def test_get_amount_in_shares_to_underlying(sample_tokens, sample_pool_state, sample_fixed_parameters):
    underlying, shares = sample_tokens
    module = YoProtocolLiquidityModule()
    output_amount = 10 * 10**18
    _, out = module.get_amount_in(sample_pool_state, sample_fixed_parameters, shares, underlying, output_amount)
    assert isinstance(out, int)

def test_get_amount_in_invalid_token(sample_tokens, sample_pool_state, sample_fixed_parameters):
    underlying, shares = sample_tokens
    module = YoProtocolLiquidityModule()
    fake_token = Token(address="0xBAD", symbol="BAD", decimals=18, reference_price=Decimal("1.0"))
    with pytest.raises(ValueError):
        module.get_amount_in(sample_pool_state, sample_fixed_parameters, fake_token, shares, 1)

def test_get_apy(sample_pool_state):
    module = YoProtocolLiquidityModule()
    apy = module.get_apy(sample_pool_state)
    assert isinstance(apy, Decimal)
    assert apy > 0

def test_get_tvl(sample_tokens, sample_pool_state):
    underlying, _ = sample_tokens
    module = YoProtocolLiquidityModule()
    tvl = module.get_tvl(sample_pool_state, underlying)
    assert isinstance(tvl, Decimal)
    assert tvl > 0