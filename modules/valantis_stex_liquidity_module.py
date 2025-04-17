from dataclasses import dataclass
from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional, Tuple
from decimal import Decimal
from modules.utils.math import SafeMath
import requests
import os

BIPS = 10000
MAX_SWAP_FEE_BIPS = 10000

@dataclass
class FeeParams():
    min_threshold_ratio_bips: int
    max_threshold_ratio_bips: int
    fee_min_bips: int
    fee_max_bips: int


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
        amount_0_pending_lp_withdrawal: int = self.convert_to_token_0(pool_state['amount_1_pending_lp_withdrawal'])
        reserves_token_0: int = SafeMath.sub(SafeMath.add(pool_state['reserves_token_0'], pool_state['amount_0_pending_unstaking']), amount_0_pending_lp_withdrawal)
        reserves_token_1: int = SafeMath.add(pool_state['reserves_token_1'], pool_state['amount_1_lending_pool'])
        fee_params: FeeParams = pool_state['fee_params']

        # For token0 -> token1 swap
        if isZeroToOne:
            # We need to solve for amount_in in the equation:
            # output_amount = amount_in * (BIPS / (BIPS + transformed_fee(amount_in)))
            # where transformed_fee(amount_in) = BIPS * fee(amount_in) / (BIPS - fee(amount_in))
            # and fee(amount_in) is a function of the new reserves after the swap

            # Let's express this mathematically:
            # Let x = amount_in
            # Let f(x) = fee(x) = fee based on new reserves (reserves_token_0 + x)
            # Let t(x) = transformed_fee(x) = BIPS * f(x) / (BIPS - f(x))
            # We need to solve: output_amount = x * (BIPS / (BIPS + t(x)))

            # We can rearrange this to:
            # x = output_amount * (BIPS + t(x)) / BIPS
            # x = output_amount + output_amount * t(x) / BIPS
            # x = output_amount + output_amount * f(x) / (BIPS - f(x))

            # Since f(x) is a piecewise linear function, we can solve this by considering each case:

            # Case 1: If the ratio is below min threshold
            # f(x) = fee_min_bips
            # t(x) = BIPS * fee_min_bips / (BIPS - fee_min_bips)
            # x = output_amount * (1 + fee_min_bips / (BIPS - fee_min_bips))
            amount_in_min = SafeMath.muldiv(
                output_amount,
                BIPS,
                SafeMath.sub(BIPS, fee_params.fee_min_bips)
            )
            ratio_min = SafeMath.muldiv(
                SafeMath.add(reserves_token_0, amount_in_min),
                BIPS,
                reserves_token_1
            )
            if ratio_min <= fee_params.min_threshold_ratio_bips:
                return SafeMath.sub(amount_in_min, output_amount), amount_in_min

            # Case 2: If the ratio is above max threshold
            # f(x) = fee_max_bips
            # t(x) = BIPS * fee_max_bips / (BIPS - fee_max_bips)
            # x = output_amount * (1 + fee_max_bips / (BIPS - fee_max_bips))
            amount_in_max = SafeMath.muldiv(
                output_amount,
                BIPS,
                SafeMath.sub(BIPS, fee_params.fee_max_bips)
            )
            ratio_max = SafeMath.muldiv(
                SafeMath.add(reserves_token_0, amount_in_max),
                BIPS,
                reserves_token_1
            )
            if ratio_max >= fee_params.max_threshold_ratio_bips:
                return SafeMath.sub(amount_in_max, output_amount), amount_in_max

            # Case 3: Linear region - Using quadratic formula
            # Define the function we're trying to solve: f(x) = x - output_amount * (BIPS + t(x)) / BIPS
            # where t(x) is the transformed fee based on reserves after adding x
            # We want to find x where f(x) = 0
            
            # Scale down all numbers by 10^18 to work with smaller numbers
            SCALE = Decimal('1000000000000000000')  # 10^18
            scaled_output = Decimal(str(output_amount)) / SCALE
            scaled_reserves_0 = Decimal(str(reserves_token_0)) / SCALE
            scaled_reserves_1 = Decimal(str(reserves_token_1)) / SCALE
            
            # Calculate the quadratic coefficients directly from the original equation
            # The equation is: output_amount = x * (BIPS / (BIPS + t(x)))
            # where t(x) = BIPS * f(x) / (BIPS - f(x))
            # and f(x) = fee_min_bips + (fee_max_bips - fee_min_bips) * (ratio - min_threshold_ratio_bips) / (max_threshold_ratio_bips - min_threshold_ratio_bips)
            # where ratio = (reserves_token_0 + x) * BIPS / reserves_token_1
            
            # Let's expand this into a quadratic equation Ax² + Bx + C = 0
            
            # First, calculate the ratio terms
            ratio_min = Decimal(str(fee_params.min_threshold_ratio_bips))
            ratio_max = Decimal(str(fee_params.max_threshold_ratio_bips))
            ratio_range = ratio_max - ratio_min
            fee_range = Decimal(str(fee_params.fee_max_bips - fee_params.fee_min_bips))
            
            # Calculate the coefficients
            # A = -(fee_range * BIPS) / (ratio_range * reserves_token_1)
            A = -(fee_range * Decimal(str(BIPS))) / (ratio_range * scaled_reserves_1)
            
            # B = BIPS - (fee_range * reserves_token_0 * BIPS) / (ratio_range * reserves_token_1) - fee_min_bips
            B = Decimal(str(BIPS)) - (fee_range * scaled_reserves_0 * Decimal(str(BIPS))) / (ratio_range * scaled_reserves_1) - Decimal(str(fee_params.fee_min_bips))
            
            # C = -output_amount * BIPS
            C = -scaled_output * Decimal(str(BIPS))
            
            # If A is zero, we have a linear equation -- these are edge-cases that should never happen but including them for completeness
            if abs(A) < Decimal('1e-10'):  # Using small epsilon for Decimal comparison
                if abs(B) < Decimal('1e-10'):
                    # No solution, fall back to max fee
                    amount_in = round((scaled_output * Decimal(str(BIPS))) / (Decimal(str(BIPS)) - Decimal(str(fee_params.fee_max_bips))) * SCALE)
                    fee = amount_in - output_amount
                    return fee, amount_in
                else:
                    # Linear solution
                    amount_in = round(-C / B * SCALE)
                    if amount_in > 0:
                        _, actual_amount_out = self.swap(input_token, amount_in, pool_state, fixed_parameters)
                        if actual_amount_out >= output_amount:
                            fee = amount_in - output_amount
                            return fee, amount_in
            
            # Calculate discriminant
            discriminant = B * B - Decimal('4') * A * C
            
            # If discriminant is negative, no real solutions
            if discriminant < 0:
                # Fall back to max fee estimate
                amount_in = round((scaled_output * Decimal(str(BIPS))) / (Decimal(str(BIPS)) - Decimal(str(fee_params.fee_max_bips))) * SCALE)
                fee = amount_in - output_amount
                return fee, amount_in
            
            # Calculate solutions using quadratic formula
            sqrt_discriminant = discriminant.sqrt()
            x1 = (-B - sqrt_discriminant) / (Decimal('2') * A)
            x2 = (-B + sqrt_discriminant) / (Decimal('2') * A)
            
            # Choose the positive solution that gives us at least the desired output amount
            # Round up to ensure we get at least the desired output amount
            amount_in = int((x2 if x2 > 0 else x1) * SCALE + Decimal('0.5'))
            
            # Verify the solution
            _, actual_amount_out = self.swap(input_token, amount_in, pool_state, fixed_parameters)
            if actual_amount_out >= output_amount:
                fee = amount_in - output_amount
                return fee, amount_in
                
            # If the solution doesn't give us enough output, use the max fee estimate
            # Round up to ensure we get at least the desired output amount
            amount_in = int((scaled_output * Decimal(str(BIPS))) / (Decimal(str(BIPS)) - Decimal(str(fee_params.fee_max_bips))) * SCALE + Decimal('0.5'))
            fee = amount_in - output_amount
            return fee, amount_in

        # For token1 -> token0 swap, no fee is applied
        else:
            return 0, output_amount

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
                'https://analytics-v2.valantis-analytics.xyz/pool_info',
                json={
                    "chainId": "999",
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
        swap_fee = self.get_swap_fee_in_bips(input_token, amount_in, pool_state, fixed_parameters)
        amount_in_without_fee = SafeMath.muldiv(amount_in, MAX_SWAP_FEE_BIPS, SafeMath.add(MAX_SWAP_FEE_BIPS, swap_fee))
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
        reserves_token_0: int = pool_state['reserves_token_0']
        reserves_token_1: int = pool_state['reserves_token_1']
        amount_0_pending_unstaking: int = pool_state['amount_0_pending_unstaking']
        amount_1_pending_lp_withdrawal: int = pool_state['amount_1_pending_lp_withdrawal']
        amount_0_pending_lp_withdrawal: int = self.convert_to_token_0(amount_1_pending_lp_withdrawal)
        amount_0_total: int = SafeMath.sub(SafeMath.add(SafeMath.add(reserves_token_0, amount_0_pending_unstaking), amount_in), amount_0_pending_lp_withdrawal)
        amount_1_lending_pool: int = pool_state['amount_1_lending_pool']
        reserves_1_total: int = SafeMath.add(reserves_token_1, amount_1_lending_pool)

        if (reserves_1_total == 0):
            raise Exception('STEXRatioSwapFeeModule__getSwapFeeInBips_ZeroReserveToken1')

        fee_params: FeeParams = pool_state['fee_params']

        ratio_bips: int = SafeMath.muldiv(amount_0_total, BIPS, reserves_1_total)
        fee_in_bips: int = 0

        if (ratio_bips > fee_params.max_threshold_ratio_bips):
            fee_in_bips = fee_params.fee_max_bips
        elif (ratio_bips < fee_params.min_threshold_ratio_bips):
            fee_in_bips = fee_params.fee_min_bips
        else:
            numerator: int = SafeMath.sub(ratio_bips, fee_params.min_threshold_ratio_bips)
            denominator: int = SafeMath.sub(fee_params.max_threshold_ratio_bips, fee_params.min_threshold_ratio_bips)
            fee_in_bips: int = SafeMath.add(fee_params.fee_min_bips, SafeMath.muldiv(SafeMath.sub(fee_params.fee_max_bips, fee_params.fee_min_bips), numerator, denominator))

        return SafeMath.sub(SafeMath.muldiv(BIPS, BIPS, SafeMath.sub(BIPS, fee_in_bips)), BIPS)
    
    @staticmethod
    def convert_to_token_0(amount_token_1: int) -> int:
        return amount_token_1
    
    @staticmethod
    def convert_to_token_1(amount_token_0: int) -> int:
        return amount_token_0    

