import sys
from os import path
from typing import Dict
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from modules.utils.math import SafeMath
import pytest
from modules.valantis_stex_liquidity_module import ValantisSTEXLiquidityModule
from templates.liquidity_module import Token
from decimal import Decimal

@pytest.fixture
def liquidity_module():
    """Fixture that provides a configured liquidity module instance."""
    return ValantisSTEXLiquidityModule()

TOKEN_0 = Token(
    address="0xfFaa4a3D97fE9107Cef8a3F48c069F577Ff76cC1",
    symbol="stHYPE",
    decimals=18,
    reference_price=Decimal("18.0")
)

TOKEN_1 = Token(
    address="0x2222222222222222222222222222222222222222",
    symbol="HYPE",
    decimals=18,
    reference_price=Decimal("18.0")
)

@pytest.fixture
def fixed_parameters():
    """Fixture for fixed parameters."""
    return {
        'token_0': TOKEN_0,
        'token_1': TOKEN_1
    }

def test_get_amount_out_token0_to_token1(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_out returns the correct amount of token1 given an amount of token0
    """

    pool_state = {
        'reserves_token_0': 0,
        'reserves_token_1': 50 * (10 ** 18),
        'fee_stepwise_in_bips': [5, 10],
        'min_threshold_token_1': 10 * (10 ** 18),
        'max_threshold_token_1': 50 * (10 ** 18),
        'num_steps_token_0_fee_curve': 2,
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }

    # small amount in
    amount_in = int(0.4 * (10 ** 18))
    fee, amount_out = liquidity_module.get_amount_out(pool_state, fixed_parameters, TOKEN_0, TOKEN_1, amount_in)
    feeInBips = (fee * 10000) / amount_in
    assert fee_in_bips_is_close_enough(feeInBips, 5)
    assert amount_out == liquidity_module.convert_to_token_1(amount_in - fee)

    # larger amount in
    amount_in = int(19.9999 * (10 ** 18))
    fee, amount_out = liquidity_module.get_amount_out(pool_state, fixed_parameters, TOKEN_0, TOKEN_1, amount_in)
    feeInBips = (fee * 10000) / amount_in
    assert fee_in_bips_is_close_enough(feeInBips, 5)
    assert amount_out == liquidity_module.convert_to_token_1(amount_in - fee)

    # larger amount in
    amount_in = int(30 * (10 ** 18))
    fee, amount_out = liquidity_module.get_amount_out(pool_state, fixed_parameters, TOKEN_0, TOKEN_1, amount_in)
    feeInBips = (fee * 10000) / amount_in
    assert fee_in_bips_is_close_enough(feeInBips, 10)
    assert amount_out == liquidity_module.convert_to_token_1(amount_in - fee)

    # even larger amount in
    amount_in = int(50 * (10 ** 18))
    fee, amount_out = liquidity_module.get_amount_out(pool_state, fixed_parameters, TOKEN_0, TOKEN_1, amount_in)
    feeInBips = (fee * 10000) / amount_in
    assert fee_in_bips_is_close_enough(feeInBips, 10)
    assert amount_out == liquidity_module.convert_to_token_1(amount_in - fee)

def test_get_amount_in_token0_to_token1(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_in returns the correct amount of token0 needed for a given amount of token1.
    """
    pool_state = {
        'reserves_token_0': 0,
        'reserves_token_1': 50 * (10 ** 18),
        'fee_stepwise_in_bips': [5, 10],
        'min_threshold_token_1': 10 * (10 ** 18),
        'max_threshold_token_1': 50 * (10 ** 18),
        'num_steps_token_0_fee_curve': 2,
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }

    # small amount out
    amount_out = int(0.4 * (10 ** 18))
    fee, amount_in = liquidity_module.get_amount_in(pool_state, fixed_parameters, TOKEN_0, TOKEN_1, amount_out)
    feeInBips = (fee * 10000) / amount_in
    assert fee_in_bips_is_close_enough(feeInBips, 5)
    assert amount_in == liquidity_module.convert_to_token_0(amount_out) + fee

    # larger amount out
    amount_out = int(19.9999 * (10 ** 18))
    fee, amount_in = liquidity_module.get_amount_in(pool_state, fixed_parameters, TOKEN_0, TOKEN_1, amount_out)
    feeInBips = (fee * 10000) / amount_in
    assert fee_in_bips_is_close_enough(feeInBips, 5)
    assert amount_in == liquidity_module.convert_to_token_0(amount_out) + fee
    
    # even larger amount out
    amount_out = int(30 * (10 ** 18))
    fee, amount_in = liquidity_module.get_amount_in(pool_state, fixed_parameters, TOKEN_0, TOKEN_1, amount_out)
    feeInBips = (fee * 10000) / amount_in
    assert fee_in_bips_is_close_enough(feeInBips, 10)
    assert amount_in == liquidity_module.convert_to_token_0(amount_out) + fee
    
    # even larger amount out
    amount_out = int(50 * (10 ** 18))
    fee, amount_in = liquidity_module.get_amount_in(pool_state, fixed_parameters, TOKEN_0, TOKEN_1, amount_out)
    feeInBips = (fee * 10000) / amount_in
    assert fee_in_bips_is_close_enough(feeInBips, 10)
    assert amount_in == liquidity_module.convert_to_token_0(amount_out) + fee
    
def test_get_amount_out_token1_to_token0(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_out returns the correct amount of token0 given an amount of token1. There's no fee for these swaps.
    """
    amount_in = 1 * (10 ** 18)
    pool_state = {
        'reserves_token_0': 50 * (10 ** 18),
        'reserves_token_1': 0,
        'fee_stepwise_in_bips': [0, 0],
        'min_threshold_token_1': 0,
        'max_threshold_token_1': 0,
        'num_steps_token_0_fee_curve': 0,
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    fee, amount_out = liquidity_module.get_amount_out(pool_state, fixed_parameters, TOKEN_1, TOKEN_0, amount_in)
    assert fee == 0
    assert amount_out == liquidity_module.convert_to_token_0(amount_in)

def test_get_amount_in_token1_to_token0(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_in returns the correct amount of token1 given an amount of token0. There's no fee for these swaps.
    """
    amount_in = 1 * (10 ** 18)
    pool_state = {
        'reserves_token_0': 50 * (10 ** 18),
        'reserves_token_1': 0,
        'fee_stepwise_in_bips': [0, 0],
        'min_threshold_token_1': 0,
        'max_threshold_token_1': 0,
        'num_steps_token_0_fee_curve': 0,
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    fee, amount_out = liquidity_module.get_amount_in(pool_state, fixed_parameters, TOKEN_1, TOKEN_0, amount_in)
    assert fee == 0
    assert amount_out == liquidity_module.convert_to_token_1(amount_in)

def test_get_amount_in_not_enough_reserves(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_in returns an error when there is not enough reserves.
    """
    amount_out = 5 * (10 ** 18)  # 5 token1 
    pool_state = {
        'reserves_token_0': 0,  # 0 token0
        'reserves_token_1': 4 * (10 ** 18),  # 4 token1
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    with pytest.raises(Exception) as exc_info:
        liquidity_module.get_amount_in(
            pool_state=pool_state,
            fixed_parameters=fixed_parameters,
            input_token=TOKEN_0,
            output_token=TOKEN_1,
            output_amount=amount_out
        )
    assert str(exc_info.value) == 'SovereignPool__swap_invalidLiquidityQuote'

    pool_state = {
        'reserves_token_0': 4 * (10 ** 18),  # 4 token0
        'reserves_token_1': 0,  # 0 token1
        'fee_stepwise_in_bips': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'min_threshold_token_1': 1000,
        'max_threshold_token_1': 5000,
        'num_steps_token_0_fee_curve': 11,
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    with pytest.raises(Exception) as exc_info:
        liquidity_module.get_amount_in(
            pool_state=pool_state,
            fixed_parameters=fixed_parameters,
            input_token=TOKEN_1,
            output_token=TOKEN_0,
            output_amount=amount_out
        )
    assert str(exc_info.value) == 'SovereignPool__swap_invalidLiquidityQuote'

def test_get_amount_in_no_fee(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_in returns the correct amount of token0 when there is no fee. This happens for any token1 -> token0 swap
    """
    amount_out = 1 * (10 ** 18)  # 1 token1 
    pool_state = {
        'reserves_token_0': (30 * 10**18),  # 30 token0
        'reserves_token_1': (30 * 10**18),  # 30 token1
        'fee_stepwise_in_bips': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'min_threshold_token_1': 1000,
        'max_threshold_token_1': 5000,
        'num_steps_token_0_fee_curve': 11,
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    fee, amount_in = liquidity_module.get_amount_in(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_1,
        output_token=TOKEN_0,
        output_amount=amount_out
    )
    assert fee == 0
    assert amount_in == amount_out

def test_get_tvl(liquidity_module: ValantisSTEXLiquidityModule):
    reserves_token_0 = 100 * (10 ** 18)
    reserves_token_1 = 80 * (10 ** 18)
    amount_0_pending_unstaking = 20 * (10 ** 18)
    amount_1_pending_lp_withdrawal = 30 * (10 ** 18)
    amount_1_lending_pool = 60 * (10 ** 18)
    pool_state = {
        'reserves_token_0': reserves_token_0,
        'reserves_token_1': reserves_token_1,
        'amount_0_pending_unstaking': amount_0_pending_unstaking,
        'amount_1_pending_lp_withdrawal': amount_1_pending_lp_withdrawal,
        'amount_1_lending_pool': amount_1_lending_pool
    }
    amount_0_pending_lp_withdrawal = liquidity_module.convert_to_token_0(amount_1_pending_lp_withdrawal)
    tvl = liquidity_module.get_tvl(pool_state)
    assert tvl == reserves_token_0 + reserves_token_1 + amount_0_pending_unstaking - amount_0_pending_lp_withdrawal + amount_1_lending_pool

def test_get_apy(liquidity_module: ValantisSTEXLiquidityModule):
    """
    Test that get_apy returns the correct APY.
    """
    pool_state = {}
    apy = liquidity_module.get_apy(pool_state)
    assert apy > 0

def fee_in_bips_is_close_enough(actual_fee: float, expected_fee: float, tolerance: float = 0.01) -> bool:
    return abs(actual_fee - expected_fee) / expected_fee <= tolerance