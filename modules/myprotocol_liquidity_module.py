from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

class MyProtocolLiquidityModule(LiquidityModule):
    def get_amount_out(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        
        # Implement logic to calculate output amount given input amount

        # This is a simple implementation for a constant-product pool
        # The function is based on the Uniswap V2 formula for calculating the output amount of a swap

        if input_token.address == fixed_parameters['token0']:
            reserve_in = pool_state.Reserves.value['reserve0']
            reserve_out = pool_state.Reserves.value['reserve1']
        else:
            reserve_in = pool_state.Reserves.value['reserve1']
            reserve_out = pool_state.Reserves.value['reserve0']

        if not reserve_in or not reserve_out:
            
            return None, None

        fee_amount, amount_out = self.swap(reserve_in = reserve_in, reserve_out = reserve_out, amount_in = input_amount)

        return fee_amount, amount_out

    def get_amount_in(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:
        
        # Implement logic to calculate required input amount given output amount

        # This is a simple implementation for a constant-product pool
        # The function is based on the Uniswap V2 formula for calculating the input amount of a swap

        if input_token.address == fixed_parameters["token0"]:
            reserve_in = pool_state.Reserves.value['reserve0']
            reserve_out = pool_state.Reserves.value['reserve1']
        else:
            reserve_in = pool_state.Reserves.value['reserve1']
            reserve_out = pool_state.Reserves.value['reserve0']

        fee_amount, amount_in = self.swap(reserve_in = reserve_in, reserve_out = reserve_out, amount_out = output_amount)

        return fee_amount, amount_in

    def swap(
        self,
        reserve_in:int,
        reserve_out:int,
        amount_out: int = None,
        amount_in:int = None
    ) -> tuple[int | None, int | None]:
        
        '''
			Calculation for amount out or amount_in of constant-product pools given reserves.

			Source sample:
			https://etherscan.io/address/0x7a250d5630b4cf539739df2c5dacb4c659f2488d#code 
		'''

        reserve_in = Decimal(reserve_in)
        reserve_out = Decimal(reserve_out)
        
        if amount_out is None:

            amount_in = Decimal(amount_in)

            if not (reserve_in > 0 and reserve_out > 0):
                return None, None
            amount_in_with_fee = amount_in * Decimal(997)
            fee_amount = int(amount_in * Decimal(0.003))
            numerator = amount_in_with_fee * reserve_out
            denominator = reserve_in * Decimal(1000) + amount_in_with_fee
            amount = int(numerator/denominator) 
            
            # round down amount to avoid univ2 K
            if len(str(amount)) <= 6 and amount != 0:
                amount = amount - 1
            else:
                amount = int(amount*0.999999)
            
        else:

            if not (reserve_in > 0 and reserve_out > 0):
                return 0, 0
            amount_out = int(amount_out)
            amount_out = Decimal(amount_out)
            numerator = reserve_in * amount_out * Decimal(1000)
            denominator = (reserve_out - amount_out) * Decimal(997)
            amount =  int(numerator / denominator) + 1

            # round down amount to avoid invariant K error
            if len(str(amount)) <= 6 and amount != 0:
                amount = amount + Decimal(1)
            else:
                amount = int(amount*1.000001)

            if amount < 0:
                return None, None
            
            fee_amount = int(amount * Decimal(0.003)) 

        return int(fee_amount), int(amount)
    
    def get_apy(self, pool_state: Dict) -> Decimal:
        # Implement APY calculation logic
        pass

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        # Implement TVL calculation logic
        pass