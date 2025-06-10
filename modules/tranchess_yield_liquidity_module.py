from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

class TranchessYieldLiquidityModule(LiquidityModule):
    def _multiplyDecimal(self, x, y) -> int:
        # From SafeDecimalMath.sol
        decimals = 18
        UNIT = 10 ** decimals
        return (x * y) // UNIT

    def _get_swap_addy(self, swapMap: Dict, addr0: str, addr1: str) -> Optional[str]:
        addr0_int = int(addr0.replace('0x', ''), 16)
        addr1_int = int(addr1.replace('0x', ''), 16)
        base, quote = (addr0, addr1) if addr0_int < addr1_int else (addr1, addr0)
        return swapMap.get(base, {}).get(quote)
    
    def _get_split(
        self,
        pool_states: Dict,

        inQ: int
    ) -> int:
        # Obtained from Fund.splitRatio() view function
        splitRatio = pool_states["splitRatio"]

        outB = self._multiplyDecimal(inQ, splitRatio)
        return outB
    
    def _do_rebalance(
        self,
        pool_states: Dict,
        amountQ: int,
        amountB: int,
        amountR: int,
        index: int
    ) -> tuple[int, int, int]:
        # Obtainable from event RebalanceTriggered(uint256 indexed index, uint256 indexed day, uint256 navSum, uint256 navB, uint256 navROrZero, uint256 ratioB2Q, uint256 ratioR2Q, uint256 ratioBR);
        # it's on Fund contracts
        rebalance = pool_states["rebalances"][index]
        newAmountQ = amountQ + self._multiplyDecimal(amountB, rebalance["ratioB2Q"]) + self._multiplyDecimal(amountR, rebalance["ratioR2Q"])
        ratioBR = rebalance["ratioBR"]
        newAmountB = self._multiplyDecimal(amountB, ratioBR)
        newAmountR = self._multiplyDecimal(amountR, ratioBR)

        return newAmountQ, newAmountB, newAmountR
    
    def _batch_rebalance(
        self,
        pool_states: Dict,

        amountQ: int,
        amountB: int,
        amountR: int,
        fromIndex: int,
        toIndex: int
    ) -> tuple[int, int, int]:
        for i in range(fromIndex, toIndex):
            amountQ, amountB, amountR = self._do_rebalance(pool_states, amountQ, amountB, amountR, i)
        
        return amountQ, amountB, amountR
    
    def _get_v2_rebalance_result(
        self,
        pool_states: Dict,
        fixed_parameters: Dict,
        latest_version: int
    ) -> tuple[int, int]:
        currentVersion = pool_states["currentVersion"]
        baseBalance = pool_states["baseBalance"]
        quoteBalance = pool_states["quoteBalance"]

        newBase = 0
        newQuote = 0

        if currentVersion == latest_version:
            newBase = baseBalance
            newQuote = quoteBalance
        else:
            oldBaseBalance = baseBalance
            oldQuoteBalance = quoteBalance
            excessiveQ, newBase, _ = self._batch_rebalance(
                pool_states,

                0,
                oldBaseBalance,
                0,
                currentVersion,
                latest_version
            )

            if newBase < oldBaseBalance:
                pass # TODO
        
        return newBase, newQuote
    
    # Adaptation of StableSwap.getAmpl()
    def _get_ampl(
        self,
        pool_states: Dict,
        fixed_parameters: Dict
    ) -> int:
        pass

    # Adaptation of StableSwap.getQuoteOut()
    def _get_quote_out(
        self,
        pool_states: Dict,
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,

        baseIn: int
    ) -> int:
        # Obtainable from Fund.getRebalanceSize() view function
        rebalanceSize = pool_states["rebalanceSize"]
        oldBase, oldQuote = self._get_v2_rebalance_result(
            pool_states,
            fixed_parameters,
            rebalanceSize
        )
        newBase = oldBase + baseIn
    
    # Adaptation of SwapRouter.getAmountsOut()
    def _get_multihop_result(
        self,
        pool_states: Dict,
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        input_amount: int
    ) -> Optional[tuple[list[int], list[str], list[bool]]]:
        # Important addresses
        # BSC SwapRouter - 0x3599dDC1efcE801f8657f64127ACB07c0B5CAdC2
        
        # Obtainable from SwapAdded(address addr0, address addr1, address swap) event
        # it MUST be structured as this: swapMap[addr0][addr1] = swap
        # is a map of StableSwap addresses
        swapMap = pool_states["swapMap"]
        swapPath = pool_states["swapPath"]
        # Obtainable by calling baseAddress() view function from `swap` of SwapAdded event
        # it MUST be structured as this: baseAddresses[swap] = baseAddress
        baseAddresses = pool_states["baseAddresses"]

        # How many to swap?
        amounts = [0] * len(swapPath)
        # Where to swap?
        swaps = [None] * (len(swapPath) - 1)
        # Is it a buy or sell?
        isBuy = [False] * (len(swapPath) - 1)

        for i in range(len(swapPath) - 1):
            swaps[i] = self._get_swap_addy(
                swapMap,
                swapPath[i],
                swapPath[i + 1]
            )
            if swaps[i] is None:
                return None
            if swapPath[i] == baseAddresses[swaps[i]]:
                # Not a buy
                amounts[i + 1] = swaps[i].getQuoteOut(amounts[i])
            else:
                # Is a buy
                isBuy[i] = True
                amounts[i + 1] = swaps[i].getBaseOut(amounts[i])
    
    def _get_creation_result(
        self,
        fundUnderlying: int,
        fundEquivalentTotalQ: int,
        input_amount: int
    ) -> tuple[int | None, int | None]:
        fee = 0
        outputAmount = 0

        if fundEquivalentTotalQ <= 0:
            fee = None
            outputAmount = None
        else:
            prec = (fundEquivalentTotalQ - 1) / fundEquivalentTotalQ
            minOutQ = (fundEquivalentTotalQ * (input_amount - prec)) / fundUnderlying
            
            fee = None
            outputAmount = int(minOutQ)
        
        return fee, outputAmount

    def _get_redemption_result(
        self,
        fundUnderlying: int,
        fundEquivalentTotalQ: int,
        redemptionFee: int,
        input_amount: int
    ) -> tuple[int | None, int | None]:
        resultingUnderlying = input_amount * fundUnderlying / fundEquivalentTotalQ
        resultingFee = self._multiplyDecimal(resultingUnderlying, redemptionFee)

        return resultingFee, resultingUnderlying

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
                    fee, outputAmount = self._get_creation_result(
                        fundUnderlying,
                        fundEquivalentTotalQ,
                        input_amount
                    )
                elif input_token.address.lower() == fixed_parameters["QUEENTokenAddress"]:
                    # Redemption
                    resultingFee, resultingUnderlying = self._get_redemption_result(
                        fundUnderlying, 
                        fundEquivalentTotalQ, 
                        fixed_parameters["QUEENRedemptionFee"], 
                        input_amount
                    )
                    
                    fee = resultingFee
                    outputAmount = resultingUnderlying - resultingFee

            else:
                # Swap in secondary market
                # nQUEEN-BNB Stable Swap: 0xfcF44D5EB5C4A03D03CF5B567C7CDe9B66Ba5773
                pass
        elif pool_states["isTurboAndStableFund"]:
            if pool_states["isPrimaryMarket"]:
                # https://tranchess.com/primary-market/56
                # "Create QUEEN token at 1:1 ratio with asBNB, uniBTC or brBTC"
                fee = None
                slippagePrecaution = 10**4 # Sometimes, 100% of underlying will be 99.99% of QUEEN
                outputAmount = input_amount - slippagePrecaution
            else:
                # https://tranchess.com/swap/56
                pass
        elif pool_states["isTranche"]:
            # https://tranchess.com/bishop
            # https://tranchess.com/rook
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