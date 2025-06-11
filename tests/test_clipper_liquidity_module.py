import pytest
from decimal import Decimal
from modules.clipper_liquidity_module import ClipperLiquidityModule
from templates.liquidity_module import Token

@pytest.fixture
def clipper_module():
    return ClipperLiquidityModule()

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

def test_get_amount_out_basic(clipper_module):
    # Pool with swaps enabled, valid assets, and valid pair
    pool_states = {
        "pools": [
            {
                "pool": {"swaps_enabled": True},
                "assets": [
                    {"address": "0x0", "price_in_usd": "2000"},
                    {"address": "0x1", "price_in_usd": "1"}
                ],
                "pairs": [
                    {"assets": ["ETH", "USDC"], "fee_in_basis_points": 30}
                ]
            }
        ]
    }
    fixed_parameters = {}
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    input_amount = 10**18  # 1 ETH
    fee, output = clipper_module.get_amount_out(pool_states, fixed_parameters, input_token, output_token, input_amount)
    assert isinstance(fee, int)
    assert isinstance(output, int)
    assert output > 0

# Edge: swaps disabled
def test_get_amount_out_swaps_disabled(clipper_module):
    pool_states = {
        "pools": [
            {"pool": {"swaps_enabled": False}, "assets": [], "pairs": []}
        ]
    }
    fixed_parameters = {}
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    input_amount = 10**18
    fee, output = clipper_module.get_amount_out(pool_states, fixed_parameters, input_token, output_token, input_amount)
    assert fee is None and output is None

# Edge: no valid pair
def test_get_amount_out_no_valid_pair(clipper_module):
    pool_states = {
        "pools": [
            {
                "pool": {"swaps_enabled": True},
                "assets": [
                    {"address": "0x0", "price_in_usd": "2000"},
                    {"address": "0x1", "price_in_usd": "1"}
                ],
                "pairs": []
            }
        ]
    }
    fixed_parameters = {}
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    input_amount = 10**18
    fee, output = clipper_module.get_amount_out(pool_states, fixed_parameters, input_token, output_token, input_amount)
    assert fee is None and output is None

# Edge: quote is zero
def test_get_amount_out_zero_quote(clipper_module):
    pool_states = {
        "pools": [
            {
                "pool": {"swaps_enabled": True},
                "assets": [
                    {"address": "0x0", "price_in_usd": "0"},
                    {"address": "0x1", "price_in_usd": "1"}
                ],
                "pairs": [
                    {"assets": ["ETH", "USDC"], "fee_in_basis_points": 30}
                ]
            }
        ]
    }
    fixed_parameters = {}
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    input_amount = 10**18
    fee, output = clipper_module.get_amount_out(pool_states, fixed_parameters, input_token, output_token, input_amount)
    assert fee == 0 and output == 0

# Edge: no pools
def test_get_amount_out_no_pools(clipper_module):
    pool_states = {"pools": []}
    fixed_parameters = {}
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    input_amount = 10**18
    fee, output = clipper_module.get_amount_out(pool_states, fixed_parameters, input_token, output_token, input_amount)
    assert fee is None and output is None

def test_get_amount_out_precise_calculation_eth_to_usdc(clipper_module):
    """
    Tests a standard swap from a high-decimal token (ETH) to a low-decimal token (USDC),
    verifying the exact fee and output amount.
    """
    pool_states = {
        "pools": [
            {
                "pool": {"swaps_enabled": True},
                "assets": [
                    {"address": "0x0", "price_in_usd": "2000", "decimals": 18},
                    {"address": "0x1", "price_in_usd": "1", "decimals": 6}
                ],
                "pairs": [{"assets": ["ETH", "USDC"], "fee_in_basis_points": 30}] # 0.3% fee
            }
        ]
    }
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    input_amount = 10**18  # 1 ETH

    # Expected calculation:
    # Pre-fee output = 1e18 * (2000/1) * (10**(6-18)) = 2_000_000_000 (2000 USDC)
    # Fee = 2_000_000_000 * (30 / 10000) = 6_000_000
    # Final output = 2_000_000_000 - 6_000_000 = 1_994_000_000
    expected_fee = 6_000_000
    expected_output = 1_994_000_000

    fee, output = clipper_module.get_amount_out(pool_states, {}, input_token, output_token, input_amount)

    assert fee == expected_fee
    assert output == expected_output

def test_get_amount_out_precise_calculation_usdc_to_wbtc(clipper_module):
    """
    Tests a swap from a low-decimal token (USDC) to a high-decimal token (WBTC),
    verifying the exact fee and output amount.
    """
    pool_states = {
        "pools": [
            {
                "pool": {"swaps_enabled": True},
                "assets": [
                    {"address": "0x1", "price_in_usd": "1", "decimals": 6},
                    {"address": "0x3", "price_in_usd": "40000", "decimals": 8}
                ],
                "pairs": [{"assets": ["USDC", "WBTC"], "fee_in_basis_points": 50}] # 0.5% fee
            }
        ]
    }
    input_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    output_token = Token(address="0x3", symbol="WBTC", decimals=8, reference_price=Decimal("4e22"))
    input_amount = 1000 * 10**6  # 1000 USDC

    # Expected calculation:
    # Pre-fee output = 1000e6 * (1/40000) * (10**(8-6)) = 2_500_000 (0.025 WBTC)
    # Fee = 2_500_000 * (50 / 10000) = 12_500
    # Final output = 2_500_000 - 12_500 = 2_487_500
    expected_fee = 12_500
    expected_output = 2_487_500

    fee, output = clipper_module.get_amount_out(pool_states, {}, input_token, output_token, input_amount)

    assert fee == expected_fee
    assert output == expected_output

def test_get_amount_out_zero_fee(clipper_module):
    """Tests that a zero fee results in the full pre-fee output amount."""
    pool_states = {
        "pools": [
            {
                "pool": {"swaps_enabled": True},
                "assets": [
                    {"address": "0x0", "price_in_usd": "2000", "decimals": 18},
                    {"address": "0x1", "price_in_usd": "1", "decimals": 6}
                ],
                "pairs": [{"assets": ["ETH", "USDC"], "fee_in_basis_points": 0}] # 0% fee
            }
        ]
    }
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    input_amount = 10**18  # 1 ETH

    expected_output = 2_000_000_000 # 2000 USDC

    fee, output = clipper_module.get_amount_out(pool_states, {}, input_token, output_token, input_amount)

    assert fee == 0
    assert output == expected_output

def test_get_amount_out_zero_input(clipper_module):
    """Tests that an input of 0 results in an output of 0."""
    pool_states = {
        "pools": [
            {
                "pool": {"swaps_enabled": True},
                "assets": [
                    {"address": "0x0", "price_in_usd": "2000", "decimals": 18},
                    {"address": "0x1", "price_in_usd": "1", "decimals": 6}
                ],
                "pairs": [{"assets": ["ETH", "USDC"], "fee_in_basis_points": 30}]
            }
        ]
    }
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    input_amount = 0

    fee, output = clipper_module.get_amount_out(pool_states, {}, input_token, output_token, input_amount)

    assert fee == 0
    assert output == 0

def test_get_amount_out_case_insensitive_symbol_matching(clipper_module):
    """Tests that the pair is found even if the input token symbol's case doesn't match."""
    pool_states = {
        "pools": [
            {
                "pool": {"swaps_enabled": True},
                "assets": [
                    {"address": "0x0", "price_in_usd": "2000", "decimals": 18},
                    {"address": "0x1", "price_in_usd": "1", "decimals": 6}
                ],
                "pairs": [{"assets": ["ETH", "USDC"], "fee_in_basis_points": 30}]
            }
        ]
    }
    # Use lowercase 'eth' symbol
    input_token = Token(address="0x0", symbol="eth", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    input_amount = 10**18

    expected_output = 1_994_000_000

    fee, output = clipper_module.get_amount_out(pool_states, {}, input_token, output_token, input_amount)

    assert output == expected_output, "Should find the pair regardless of symbol case"

def test_get_amount_out_multiple_pools_uses_first_valid(clipper_module):
    """
    Tests that when multiple valid pools exist, the function uses the first one
    it encounters in the list.
    """
    pool_states = {
        "pools": [
            { # First pool with a 30 bps fee
                "pool": {"swaps_enabled": True},
                "assets": [{"address": "0x0", "price_in_usd": "2000", "decimals": 18}, {"address": "0x1", "price_in_usd": "1", "decimals": 6}],
                "pairs": [{"assets": ["ETH", "USDC"], "fee_in_basis_points": 30}]
            },
            { # Second pool with a better rate (10 bps fee)
                "pool": {"swaps_enabled": True},
                "assets": [{"address": "0x0", "price_in_usd": "2000", "decimals": 18}, {"address": "0x1", "price_in_usd": "1", "decimals": 6}],
                "pairs": [{"assets": ["ETH", "USDC"], "fee_in_basis_points": 10}]
            }
        ]
    }
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    input_amount = 10**18

    # The expected output should be based on the FIRST pool's fee (30 bps)
    expected_output = 1_994_000_000

    fee, output = clipper_module.get_amount_out(pool_states, {}, input_token, output_token, input_amount)

    assert output == expected_output, "The function should have returned the result from the first valid pool"

def test_get_amount_in_basic(clipper_module):
    """Test a basic get_amount_in calculation with a valid pool, assets, and pair."""
    pool_states = {
        "pools": [
            {
                "pool": {"swaps_enabled": True},
                "assets": [
                    {"address": "0x0", "price_in_usd": "2000", "decimals": 18},
                    {"address": "0x1", "price_in_usd": "1", "decimals": 6}
                ],
                "pairs": [
                    {"assets": ["ETH", "USDC"], "fee_in_basis_points": 30}
                ]
            }
        ]
    }
    fixed_parameters = {}
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    output_amount = 1_994_000_000  # 1994 USDC (after fee)
    # Should require slightly more than 1 ETH due to fee
    # Reverse calculation: input = output / (quote * (1 - fee))
    # For this test, just check types and positivity
    fee, input_amt = clipper_module.get_amount_in(pool_states, fixed_parameters, input_token, output_token, output_amount)
    assert isinstance(fee, int)
    assert isinstance(input_amt, int)
    assert input_amt > 0


def test_get_amount_in_swaps_disabled(clipper_module):
    pool_states = {
        "pools": [
            {"pool": {"swaps_enabled": False}, "assets": [], "pairs": []}
        ]
    }
    fixed_parameters = {}
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    output_amount = 1_000_000
    fee, input_amt = clipper_module.get_amount_in(pool_states, fixed_parameters, input_token, output_token, output_amount)
    assert fee is None and input_amt is None


def test_get_amount_in_no_valid_pair(clipper_module):
    pool_states = {
        "pools": [
            {
                "pool": {"swaps_enabled": True},
                "assets": [
                    {"address": "0x0", "price_in_usd": "2000", "decimals": 18},
                    {"address": "0x1", "price_in_usd": "1", "decimals": 6}
                ],
                "pairs": []
            }
        ]
    }
    fixed_parameters = {}
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    output_amount = 1_000_000
    fee, input_amt = clipper_module.get_amount_in(pool_states, fixed_parameters, input_token, output_token, output_amount)
    assert fee is None and input_amt is None


def test_get_amount_in_zero_quote(clipper_module):
    pool_states = {
        "pools": [
            {
                "pool": {"swaps_enabled": True},
                "assets": [
                    {"address": "0x0", "price_in_usd": "0", "decimals": 18},
                    {"address": "0x1", "price_in_usd": "1", "decimals": 6}
                ],
                "pairs": [
                    {"assets": ["ETH", "USDC"], "fee_in_basis_points": 30}
                ]
            }
        ]
    }
    fixed_parameters = {}
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    output_amount = 1_000_000
    fee, input_amt = clipper_module.get_amount_in(pool_states, fixed_parameters, input_token, output_token, output_amount)
    assert fee is None and input_amt is None


def test_get_amount_in_zero_output(clipper_module):
    pool_states = {
        "pools": [
            {
                "pool": {"swaps_enabled": True},
                "assets": [
                    {"address": "0x0", "price_in_usd": "2000", "decimals": 18},
                    {"address": "0x1", "price_in_usd": "1", "decimals": 6}
                ],
                "pairs": [
                    {"assets": ["ETH", "USDC"], "fee_in_basis_points": 30}
                ]
            }
        ]
    }
    fixed_parameters = {}
    input_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    output_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    output_amount = 0
    fee, input_amt = clipper_module.get_amount_in(pool_states, fixed_parameters, input_token, output_token, output_amount)
    assert fee == 0 and input_amt == 0


def test_get_amount_in_precise_calculation_usdc_to_eth(clipper_module):
    """
    Tests a swap from USDC to ETH, verifying the exact fee and input amount required for a given output.
    """
    pool_states = {
        "pools": [
            {
                "pool": {"swaps_enabled": True},
                "assets": [
                    # Input asset: USDC
                    {"address": "0x1", "price_in_usd": "1", "decimals": 6},
                    # Output asset: ETH
                    {"address": "0x0", "price_in_usd": "2000", "decimals": 18}
                ],
                "pairs": [{"assets": ["USDC", "ETH"], "fee_in_basis_points": 30}] # 0.3% fee
            }
        ]
    }
    input_token = Token(address="0x1", symbol="USDC", decimals=6, reference_price=Decimal("3e14"))
    output_token = Token(address="0x0", symbol="ETH", decimals=18, reference_price=Decimal("1e18"))
    # The desired output is 1 ETH
    output_amount = 1 * 10**18

    # --- Manual Calculation for Verification ---
    # 1. Quote to convert USDC (input) to ETH (output):
    #    quote = (price_in / price_out) * 10**(decimals_out - decimals_in)
    #    quote = (1 / 2000) * 10**(18 - 6) = 0.0005 * 1e12 = 5e8
    #
    # 2. Pre-fee output required:
    #    pre_fee_output = final_output / (1 - fee_percentage)
    #    pre_fee_output = 1e18 / (1 - 0.003) = 1e18 / 0.997
    #
    # 3. Total input required (in USDC lowest unit):
    #    total_input = pre_fee_output / quote
    #    total_input = (1e18 / 0.997) / 5e8 = 2006018054.162487...
    #
    # 4. Input required for the net amount (if no fee):
    #    input_for_net = output_amount / quote = 1e18 / 5e8 = 2_000_000_000
    #
    # 5. Fee portion in USDC:
    #    fee = total_input - input_for_net = 6018054.162487...

    expected_input = 2006018054  # Truncated to int
    expected_fee = 6018054       # Truncated to int

    # Execute the function
    fee, input_amt = clipper_module.get_amount_in(pool_states, {}, input_token, output_token, output_amount)

    # Assert the exact integer values
    assert isinstance(fee, int)
    assert isinstance(input_amt, int)
    assert fee == expected_fee
    assert input_amt == expected_input