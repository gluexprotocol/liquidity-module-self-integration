from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

class TranchessYieldLiquidityModule(LiquidityModule):
    def _multiplyDecimal(self, x, y) -> int:
        # From SafeDecimalMath.sol
        decimals = 18
        UNIT = 10 ** decimals
        return (x * y) // UNIT
    
    def _get_multihop_result(
        self,
        pool_states: Dict,
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        input_amount: int
    ) -> int:
        # Obtainable from SwapAdded(address addr0, address addr1, address swap) event
        # it MUST be structured as this: swapMap[addr0][addr1] = swap
        swapMap = pool_states["swapMap"]


    def get_amount_out(
        self, 
        pool_states: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        """
        Calculate the amount of output token received for a given input amount.
        """
        fee = 0
        outputAmount = 0

        if pool_states["isLiquidStaking"]:
            if pool_states["isPrimaryMarket"]:
                fundUnderlying = pool_states["fundUnderlying"]
                fundEquivalentTotalQ = pool_states["fundEquivalentTotalQ"]
                
                if output_token.address.lower() == fixed_parameters["QUEENTokenAddress"]:
                    # Creation
                    if fundEquivalentTotalQ <= 0:
                        fee = None
                        outputAmount = None
                    else:
                        prec = (fundEquivalentTotalQ - 1) / fundEquivalentTotalQ
                        minOutQ = (fundEquivalentTotalQ * (input_amount - prec)) / fundUnderlying
                        
                        fee = None
                        outputAmount = int(minOutQ)
                if input_token.address.lower() == fixed_parameters["QUEENTokenAddress"]:
                    # Redemption
                    resultingUnderlying = input_amount * fundUnderlying / fundEquivalentTotalQ
                    resultingFee = self._multiplyDecimal(resultingUnderlying, fixed_parameters["QUEENRedemptionFee"])
                    
                    fee = resultingFee
                    outputAmount = resultingUnderlying - resultingFee

            else:
                # Swap in secondary market
                # nQUEEN-BNB Stable Swap: 0xfcF44D5EB5C4A03D03CF5B567C7CDe9B66Ba5773
                pass
        elif pool_states["isTurboAndStableFund"]:
            pass
        else:
            fee = None
            outputAmount = None
        
        return fee, outputAmount


    def get_amount_in(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:
        """
        Calculate the amount of input token required to receive a given output amount.
        """
        pass

    def get_apy(self, pool_state: Dict) -> Decimal:
        """
        Calculate the annual percentage yield (APY) for a yield farm pool.
        """
        pass

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        """
        Calculate the total value locked (TVL) in a yield farm pool.
        """
        pass