from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional, Tuple
from decimal import Decimal
from modules.utils.math import SafeMath
import requests
import os

BIPS = 10000
MAX_SWAP_FEE_BIPS = 10000

class ValantisSTEXLiquidityModule(LiquidityModule):
    def get_amount_out(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        # Implement logic to calculate output amount given input amount
        fee, amount_out = self.swap(input_token, input_amount, pool_state, fixed_parameters)
        return fee, amount_out

    def get_amount_in(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:
        # Implement logic to calculate required input amount given output amount
        isZeroToOne: bool = input_token.address == fixed_parameters['token_0'].address
        if isZeroToOne:
            if output_amount > pool_state['reserves_token_1']:
                raise Exception('SovereignPool__swap_invalidLiquidityQuote')
        else:
            if output_amount > pool_state['reserves_token_0']:
                raise Exception('SovereignPool__swap_invalidLiquidityQuote')

        # Get pool parameters
        reserves_token_1: int = pool_state['reserves_token_1']
        amount_1_lending_pool: int = pool_state['amount_1_lending_pool']
        reserves_1_total: int = SafeMath.add(reserves_token_1, amount_1_lending_pool)        

        # For token0 -> token1 swap
        if isZeroToOne:
            expected_amount_token_1_after_swap = max(0, reserves_1_total - output_amount)
            fee_in_bips = self.get_swap_fee_given_expected_amount_token_1_after_swap(expected_amount_token_1_after_swap, pool_state)
            amount_in_without_fee = ValantisSTEXLiquidityModule.convert_to_token_0(output_amount)
            fee = amount_in_without_fee * fee_in_bips // BIPS
            amount_in = amount_in_without_fee + fee
            return fee, amount_in
        
        # For token1 -> token0 swap
        else:
            return 0, ValantisSTEXLiquidityModule.convert_to_token_1(output_amount)
            

    def get_apy(self, pool_state: Dict) -> Decimal:
        """
        Fetches APY from Valantis's analytics API
        """
        try:
            api_token = os.getenv('VALANTIS_API_TOKEN')
            if not api_token:
                raise ValueError("VALANTIS_API_TOKEN environment variable is not set")
            gluex_header = os.getenv('GLUEX_HEADER')
            if not gluex_header:
                raise ValueError("GLUEX_HEADER environment variable is not set")

            response = requests.post(
                'https://analytics-v3.valantis-analytics.xyz/pool_info',
                json={
                    "chainId": 999,
                    "addresses": ["0x39694eFF3b02248929120c73F90347013Aec834d"]
                },
                headers={
                    'Authorization': f'Bearer {api_token}',
                    'Content-Type': 'application/json',
                    gluex_header: 'true'
                }
            )
            response.raise_for_status()
            data = response.json()
            
            apy = data[0]["lpTokenReturns"]["apy"]
            return Decimal(apy)
            
        except Exception as e:
            # Log the error and return 0 as fallback
            print(f"Error fetching APY from Valantis analytics: {str(e)}")
            return Decimal('0')

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        """
        This calculates the TVL of the pool in terms of HYPE and stHYPE (which is 1:1 with HYPE)
        """
        reserves_token_0 = pool_state['reserves_token_0']
        reserves_token_1 = pool_state['reserves_token_1']
        amount_0_pending_unstaking = pool_state['amount_0_pending_unstaking']
        amount_1_pending_lp_withdrawal = pool_state['amount_1_pending_lp_withdrawal']
        amount_0_pending_lp_withdrawal: int = self.convert_to_token_0(amount_1_pending_lp_withdrawal)
        amount_0_total = SafeMath.sub(SafeMath.add(reserves_token_0, amount_0_pending_unstaking), amount_0_pending_lp_withdrawal)
        amount_1_lending_pool = pool_state['amount_1_lending_pool']
        reserves_1_total = SafeMath.add(reserves_token_1, amount_1_lending_pool)

        return amount_0_total + reserves_1_total

    def swap(self, input_token: Token, amount_in: int, pool_state: Dict, fixed_parameters: Dict) -> Tuple[int, int]:
        isZeroToOne: bool = input_token.address == fixed_parameters['token_0'].address
        swap_fee_in_bips = self.get_swap_fee_in_bips(input_token, amount_in, pool_state, fixed_parameters)
        swap_fee_in_bips_transform = self.get_swap_fee_in_bips_transform(swap_fee_in_bips)
        amount_in_without_fee = SafeMath.muldiv(amount_in, MAX_SWAP_FEE_BIPS, SafeMath.add(MAX_SWAP_FEE_BIPS, swap_fee_in_bips_transform))
        fee_amount = SafeMath.sub(amount_in, amount_in_without_fee)
        amount_out = ValantisSTEXLiquidityModule.convert_to_token_1(amount_in_without_fee) if isZeroToOne else ValantisSTEXLiquidityModule.convert_to_token_0(amount_in_without_fee)
        if isZeroToOne:
            if amount_out > pool_state['reserves_token_1']:
                raise Exception('SovereignPool__swap_invalidLiquidityQuote')
        else:
            if amount_out > pool_state['reserves_token_0']:
                raise Exception('SovereignPool__swap_invalidLiquidityQuote')
        return fee_amount, amount_out

    """
    Swap fee is a function of pool state and tokenIn amount
    """
    def get_swap_fee_in_bips(self, token_in: Token, amount_in: int, pool_state: Dict, fixed_parameters: Dict) -> int:
        token_1: Token = fixed_parameters['token_1']

        # Fee is only applied on token0 -> token1 swaps
        if (token_in.address == token_1.address):
            return 0

        # Get reserve information
        reserves_token_1: int = pool_state['reserves_token_1']
        amount_1_lending_pool: int = pool_state['amount_1_lending_pool']
        reserves_1_total: int = SafeMath.add(reserves_token_1, amount_1_lending_pool)
        expected_amount_token_1_out = ValantisSTEXLiquidityModule.convert_to_token_1(amount_in)
        if reserves_1_total > expected_amount_token_1_out:
            expected_amount_token_1_after_swap = reserves_1_total - expected_amount_token_1_out
        else:
            expected_amount_token_1_after_swap = 0

        return self.get_swap_fee_given_expected_amount_token_1_after_swap(expected_amount_token_1_after_swap, pool_state)
    
    def get_swap_fee_given_expected_amount_token_1_after_swap(self, expected_amount_token_1_after_swap: int, pool_state: Dict) -> int:
        stepwise_fee_array = pool_state['fee_stepwise_in_bips']
        min_threshold_token_1 = pool_state['min_threshold_token_1']
        max_threshold_token_1 = pool_state['max_threshold_token_1']
        num_steps_token_0_fee_curve = pool_state['num_steps_token_0_fee_curve']
        if expected_amount_token_1_after_swap > max_threshold_token_1:
            fee_in_bips = stepwise_fee_array[0]
        else:
            tickNumberNumerator = (max_threshold_token_1 - expected_amount_token_1_after_swap) * num_steps_token_0_fee_curve
            tickNumberDenominator = max_threshold_token_1 - min_threshold_token_1
            tickNumber = tickNumberNumerator // tickNumberDenominator
            if tickNumber >= num_steps_token_0_fee_curve:
                fee_in_bips = stepwise_fee_array[num_steps_token_0_fee_curve - 1]
            else:
                fee_in_bips = stepwise_fee_array[tickNumber]
        return fee_in_bips

    def get_swap_fee_in_bips_transform(self, fee_in_bips: int) -> int:
        return SafeMath.muldiv(BIPS, fee_in_bips, SafeMath.sub(BIPS, fee_in_bips))

    ## Will change this once we have more pools ;)
    @staticmethod
    def convert_to_token_0(amount_token_1: int) -> int:
        return amount_token_1
    
    @staticmethod
    def convert_to_token_1(amount_token_0: int) -> int:
        return amount_token_0    

