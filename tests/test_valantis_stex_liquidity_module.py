import sys
from os import path
from typing import Dict
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from modules.utils.math import SafeMath
import pytest
from modules.valantis_stex_liquidity_module import ValantisSTEXLiquidityModule, FeeParams
from templates.liquidity_module import Token
from decimal import Decimal

@pytest.fixture
def liquidity_module():
    """Fixture that provides a configured liquidity module instance."""
    return ValantisSTEXLiquidityModule()

TOKEN_0 = Token(
    address="0xe2FbC9cB335A65201FcDE55323aE0F4E8A96A616",
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

def test_get_amount_out_zero_reserves_token_1(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_out throws an exception when reserves_token_1 is 0.
    """
    amount_in = 400000  # 0.4 token0 (assuming 6 decimals)
    pool_state = {
        'reserves_token_0': 1000000,  # 1 token0
        'reserves_token_1': 0,  # 0 token1
        'fee_params': FeeParams(
            min_threshold_ratio_bips=3000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=1,
            fee_max_bips=30
        ),
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    
    with pytest.raises(Exception) as exc_info:
        liquidity_module.get_amount_out(
            pool_state=pool_state,
            fixed_parameters=fixed_parameters,
            input_token=TOKEN_0,
            output_token=TOKEN_1,
            input_amount=amount_in
        )
    
    assert str(exc_info.value) == 'STEXRatioSwapFeeModule__getSwapFeeInBips_ZeroReserveToken1'

def test_get_amount_out_zero_reserves_token_0(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_out returns the correct amount of token1 when reserves of token0 are 0. This makes the ratio fee very small such that it's clipped to fee_min_bips.
    """
    fee_min_bips = 1
    amount_in = 0.4 * (10 ** 18)  # 0.4 token0 
    pool_state = {
        'reserves_token_0': 0,  # 0 token0
        'reserves_token_1': (30 * 10**18),  # 30 token1
        'fee_params': FeeParams(
            min_threshold_ratio_bips=3000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=fee_min_bips,
            fee_max_bips=30
        ),
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    expected_amount_out = SafeMath.muldiv(amount_in, 10_000, 10_000 + fee_min_bips)
    
    fee = liquidity_module.get_swap_fee_in_bips(TOKEN_0, amount_in, pool_state, fixed_parameters)
    assert fee == fee_min_bips
    
    fee_amount, amount_out = liquidity_module.get_amount_out(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_0,
        output_token=TOKEN_1,
        input_amount=amount_in
    )
    assert amount_out == expected_amount_out
    assert fee_amount == amount_in - expected_amount_out

def test_get_amount_out_linear_region(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_out returns the correct amount of token1 when there is some token0 that gets added to the pool. This means the fee is in the linear region.
    """
    amount_in = 5 * (10 ** 18)  # 5 token0 
    pool_state = {
        'reserves_token_0': 0,  # 0 token0
        'reserves_token_1': (30 * 10**18),  # 30 token1
        'fee_params': FeeParams(
            min_threshold_ratio_bips=1000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=1,
            fee_max_bips=30
        ),
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    fee_in_bips = liquidity_module.get_swap_fee_in_bips(TOKEN_0, amount_in, pool_state, fixed_parameters)
    assert fee_in_bips > 1
    assert fee_in_bips < 30
    fee_amount, amount_out = liquidity_module.get_amount_out(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_0,
        output_token=TOKEN_1,
        input_amount=amount_in
    )
    assert fee_amount == amount_in - amount_out
    assert amount_out == SafeMath.muldiv(amount_in, 10_000, 10_000 + fee_in_bips)

def test_get_amount_out_max_fee(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_out returns the correct amount of token1 when the fee is at the max. This happens when the ratio between token0 and token1 is anywhere above 50%
    """
    amount_in = 30 * (10 ** 18)  # 30 token0 
    fee_max_bips = 30
    pool_state = {
        'reserves_token_0': 0,  # 0 token0
        'reserves_token_1': (30 * 10**18),  # 30 token1
        'fee_params': FeeParams(
            min_threshold_ratio_bips=1000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=1,
            fee_max_bips=fee_max_bips
        ),
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    fee_in_bips = liquidity_module.get_swap_fee_in_bips(TOKEN_0, amount_in, pool_state, fixed_parameters)
    assert fee_in_bips == fee_max_bips
    fee_amount, amount_out = liquidity_module.get_amount_out(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_0,
        output_token=TOKEN_1,
        input_amount=amount_in
    )
    assert fee_amount == amount_in - amount_out
    assert amount_out == SafeMath.muldiv(amount_in, 10_000, 10_000 + fee_in_bips)

def test_get_amount_out_no_fee(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_out returns the correct amount of token1 when there is no fee. This happens for any token1 -> token0 swap
    """
    amount_in = 1 * (10 ** 18)  # 1 token1 
    pool_state = {
        'reserves_token_0': (30 * 10**18),  # 30 token0
        'reserves_token_1': (30 * 10**18),  # 30 token1
        'fee_params': FeeParams(
            min_threshold_ratio_bips=1000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=1,
            fee_max_bips=30
        ),
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }   
    fee_in_bips = liquidity_module.get_swap_fee_in_bips(TOKEN_1, amount_in, pool_state, fixed_parameters)
    assert fee_in_bips == 0
    fee_amount, amount_out = liquidity_module.get_amount_out(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_1,
        output_token=TOKEN_0,
        input_amount=amount_in
    )
    assert fee_amount == 0
    assert amount_out == amount_in

def test_get_amount_out_larger_than_reserves(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that makes sure we throw an exception when the amount out is larger than the given token reserves
    """
    amount_in = 5 * (10 ** 18)  # 1 token1 
    pool_state_low_token_0 = {
        'reserves_token_0': 3 * (10 ** 18),  # 3 token0
        'reserves_token_1': (30 * 10**18),  # 30 token1
        'fee_params': FeeParams(
            min_threshold_ratio_bips=1000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=1,
            fee_max_bips=30
        ),
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    with pytest.raises(Exception) as exc_info:
        liquidity_module.get_amount_out(
            pool_state=pool_state_low_token_0,
            fixed_parameters=fixed_parameters,
            input_token=TOKEN_1,
            output_token=TOKEN_0,
            input_amount=amount_in
        )
    assert str(exc_info.value) == 'SovereignPool__swap_invalidLiquidityQuote'

    pool_state_low_token_1 = {
        'reserves_token_0': (30 * 10**18),  # 30 token0
        'reserves_token_1': 3 * (10 ** 18),  # 3 token1
        'fee_params': FeeParams(
            min_threshold_ratio_bips=1000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=1,
            fee_max_bips=30
        ),  
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    with pytest.raises(Exception) as exc_info:
        liquidity_module.get_amount_out(
            pool_state=pool_state_low_token_1,
            fixed_parameters=fixed_parameters,
            input_token=TOKEN_0,
            output_token=TOKEN_1,
            input_amount=amount_in
        )
    assert str(exc_info.value) == 'SovereignPool__swap_invalidLiquidityQuote'

def test_get_amount_in_linear_region(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_in returns the correct amount of token0 when there is some token1 that gets added to the pool. This means the fee is in the linear region.
    """
    amount_out = 5 * (10 ** 18)  # 5 token1 
    pool_state = {
        'reserves_token_0': 0,  # 0 token0
        'reserves_token_1': (30 * 10**18),  # 30 token1
        'fee_params': FeeParams(
            min_threshold_ratio_bips=1000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=1,
            fee_max_bips=30
        ),
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    fee, amount_in = liquidity_module.get_amount_in(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_0,
        output_token=TOKEN_1,
        output_amount=amount_out
    )
    print(f"fee: {fee}, amount_in: {amount_in}")
    assert fee == amount_in - amount_out 
    fee_in_bips = liquidity_module.get_swap_fee_in_bips(TOKEN_0, amount_in, pool_state, fixed_parameters)
    assert fee_in_bips > 1
    assert fee_in_bips < 30
    _, actual_amount_out = liquidity_module.get_amount_out(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_0,
        output_token=TOKEN_1,
        input_amount=amount_in
    )
    assert actual_amount_out >= amount_out

def test_get_amount_in_linear_region_with_larger_amounts(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_in returns the correct amount of token0 when there is some token1 that gets added to the pool. This means the fee is in the linear region.
    """
    amount_out = 50_000 * (10 ** 18)  # 50_000 token1 
    pool_state = {
        'reserves_token_0': 20_000 * (10 ** 18),  # 20_000 token0
        'reserves_token_1': 300_000 * (10 ** 18),  # 300_000 token1
        'fee_params': FeeParams(
            min_threshold_ratio_bips=1000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=1,
            fee_max_bips=30
        ),
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    fee, amount_in = liquidity_module.get_amount_in(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_0,
        output_token=TOKEN_1,
        output_amount=amount_out
    )
    print(f"fee: {fee}, amount_in: {amount_in}")
    assert fee == amount_in - amount_out 
    fee_in_bips = liquidity_module.get_swap_fee_in_bips(TOKEN_0, amount_in, pool_state, fixed_parameters)
    assert fee_in_bips > 1
    assert fee_in_bips < 30
    _, actual_amount_out = liquidity_module.get_amount_out(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_0,
        output_token=TOKEN_1,
        input_amount=amount_in
    )
    assert actual_amount_out >= amount_out


def test_get_amount_in_linear_region_pathological_case(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    amount_out = 10_000 * (10 ** 18)  # 10_000 token1 
    pool_state = {
        'reserves_token_0': 1 * (10 ** 18),  # 1 token0
        'reserves_token_1': 10_200 * (10 ** 18),  # 10_200 token1
        'fee_params': FeeParams(
            min_threshold_ratio_bips=1,
            max_threshold_ratio_bips=12_000,
            fee_min_bips=1,
            fee_max_bips=500
        ),
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }   
    fee, amount_in = liquidity_module.get_amount_in(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_0,
        output_token=TOKEN_1,
        output_amount=amount_out
    )
    print(f"fee: {fee}, amount_in: {amount_in}")
    assert fee == amount_in - amount_out 
    fee_in_bips = liquidity_module.get_swap_fee_in_bips(TOKEN_0, amount_in, pool_state, fixed_parameters)
    assert fee_in_bips > 1
    assert fee_in_bips < 500
    _, actual_amount_out = liquidity_module.get_amount_out(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_0,
        output_token=TOKEN_1,
        input_amount=amount_in
    )
    assert actual_amount_out >= amount_out


def test_get_amount_in_max_fee(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_in returns the correct amount of token0 when the fee is at the max. This happens when the ratio between token0 and token1 is anywhere above 50%
    """
    amount_out = 30 * (10 ** 18)  # 30 token1 
    fee_max_bips = 30
    pool_state = {
        'reserves_token_0': 0,  # 0 token0
        'reserves_token_1': (40 * 10**18),  # 40 token1
        'fee_params': FeeParams(
            min_threshold_ratio_bips=1000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=1,
            fee_max_bips=fee_max_bips
        ),
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    fee, amount_in = liquidity_module.get_amount_in(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_0,
        output_token=TOKEN_1,
        output_amount=amount_out
    )
    assert fee == amount_in - amount_out 
    fee_in_bips = liquidity_module.get_swap_fee_in_bips(TOKEN_0, amount_in, pool_state, fixed_parameters)
    assert fee_in_bips == fee_max_bips
    assert fee_in_bips == SafeMath.muldiv(amount_in, 10_000, amount_out) - 10_000
    _, actual_amount_out = liquidity_module.get_amount_out(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_0,
        output_token=TOKEN_1,
        input_amount=amount_in
    )
    assert actual_amount_out >= amount_out

def test_get_amount_in_min_fee(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_in returns the correct amount of token0 when the fee is at the min. This happens when the ratio between token0 and token1 is anywhere below 10%
    """
    amount_out = 0.4 * (10 ** 18)  # 0.4 token1 
    fee_min_bips = 1
    pool_state = {
        'reserves_token_0': 0,  # 0 token0
        'reserves_token_1': (30 * 10**18),  # 30 token1
        'fee_params': FeeParams(
            min_threshold_ratio_bips=1000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=fee_min_bips,
            fee_max_bips=30
        ),
        'amount_0_pending_unstaking': 0,
        'amount_1_pending_lp_withdrawal': 0,
        'amount_1_lending_pool': 0
    }
    fee, amount_in = liquidity_module.get_amount_in(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_0,
        output_token=TOKEN_1,
        output_amount=amount_out
    )
    assert fee == amount_in - amount_out 
    fee_in_bips = liquidity_module.get_swap_fee_in_bips(TOKEN_0, amount_in, pool_state, fixed_parameters)
    assert fee_in_bips == fee_min_bips
    assert fee_in_bips == SafeMath.muldiv(amount_in, 10_000, amount_out) - 10_000
    _, actual_amount_out = liquidity_module.get_amount_out(
        pool_state=pool_state,
        fixed_parameters=fixed_parameters,
        input_token=TOKEN_0,
        output_token=TOKEN_1,
        input_amount=amount_in
    )   
    assert actual_amount_out >= amount_out

def test_get_amount_in_not_enough_reserves(liquidity_module: ValantisSTEXLiquidityModule, fixed_parameters: Dict):
    """
    Test that get_amount_in returns an error when there is not enough reserves.
    """
    amount_out = 5 * (10 ** 18)  # 5 token1 
    pool_state = {
        'reserves_token_0': 0,  # 0 token0
        'reserves_token_1': 4 * (10 ** 18),  # 4 token1
        'fee_params': FeeParams(
            min_threshold_ratio_bips=1000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=1,
            fee_max_bips=30
        ),
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
        'fee_params': FeeParams(
            min_threshold_ratio_bips=1000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=1,
            fee_max_bips=30
        ),
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
        'fee_params': FeeParams(
            min_threshold_ratio_bips=1000,
            max_threshold_ratio_bips=5000,
            fee_min_bips=1,
            fee_max_bips=1
        ),
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
