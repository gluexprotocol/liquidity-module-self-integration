from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal

from modules.utils.pool_math import AaveV3PoolMath
from modules.utils.base_math import *

class Aavev3LiquidityModule(LiquidityModule):
    def get_amount_out(
        self, 
        pool_states: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        # Implement logic to calculate output amount given input amount
        d = datetime.now()
        reserveData = pool_states['ReserveData'] ## Fetched from the aavev3 pool getReserveData
        scaledBalance = pool_states['ScaledBalance'] ## Fetched from the aavev3 pool scaledBalanceOf
        previousIndex = pool_states['PreviousIndex'] ## Fetched from the aavev3 pool getPreviousIndex
        currentScaledVariableDebt = pool_states['ScaledTotalSupply'] ## Fetched from the aavev3 pool getScaledTotalSupply
        reserveConfigurationData = pool_states['ReserveConfigurationData'] ## Fetched from the aavev3 pool getReserveConfigurationData
        isPaused = pool_states['IsPaused'] ## Fetched from the aavev3 pool isPaused
        reserveCaps = pool_states['ReserveCaps'] ## Fetched from the aavev3 pool getReserveCaps
        scaledTotalSupply = pool_states['ATokenScaledTotalSupply'] ## Fetched from the aavev3 pool getScaledTotalSupply

        liquidityRate = reserveData['liquidityRate']
        variableBorrowRate = reserveData['variableBorrowRate']
        liquidityIndex = reserveData['liquidityIndex']
        variableBorrowIndex = reserveData['variableBorrowIndex']
        lastUpdateTimestamp = reserveData['lastUpdateTimestamp']
        currentTimeStamp = int(d.timestamp())
        isActive = reserveConfigurationData['isActive']
        isFrozen = reserveConfigurationData['isFrozen']
        supplyCap = reserveCaps['supplyCap']
        accruedToTreasury = reserveData['accruedToTreasury']
        decimals = reserveConfigurationData['decimals']

        poolMath = AaveV3PoolMath(liquidityRate, variableBorrowRate, liquidityIndex, variableBorrowIndex, lastUpdateTimestamp, currentScaledVariableDebt, scaledBalance, previousIndex, currentTimeStamp)

        if input_token.address == fixed_parameters['reserve_token']:
            fee, output_amount, nextLiquidityIndex = poolMath.supply(input_amount)
            # Validate Supply
            if nextLiquidityIndex == None:
                nextLiquidityIndex = liquidityIndex
            if isActive == False or isFrozen == True or isPaused == True:
                fee, output_amount = None, None
            elif supplyCap !=0:
                if rayMul((scaledTotalSupply + accruedToTreasury), nextLiquidityIndex) + input_amount > supplyCap * (10**decimals):
                    fee, output_amount = None, None
        else:
            fee, output_amount, nextLiquidityIndex = poolMath.withdraw(input_amount)
            # Validate Withdraw
            if isActive == False or isPaused == True:
                fee, output_amount = None, None

        return fee, output_amount

    def get_amount_in(
        self, 
        pool_states: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:
        d = datetime.now()
        
        reserveData = pool_states['ReserveData'] ## Fetched from the aavev3 pool getReserveData
        scaledBalance = pool_states['ScaledBalance'] ## Fetched from the aavev3 pool scaledBalanceOf
        previousIndex = pool_states['PreviousIndex'] ## Fetched from the aavev3 pool getPreviousIndex
        currentScaledVariableDebt = pool_states['ScaledTotalSupply'] ## Fetched from the aavev3 pool getScaledTotalSupply
        reserveConfigurationData = pool_states['ReserveConfigurationData'] ## Fetched from the aavev3 pool getReserveConfigurationData
        isPaused = pool_states['IsPaused'] ## Fetched from the aavev3 pool isPaused
        reserveCaps = pool_states['ReserveCaps'] ## Fetched from the aavev3 pool getReserveCaps
        scaledTotalSupply = pool_states['ATokenScaledTotalSupply'] ## Fetched from the aavev3 pool getScaledTotalSupply

        liquidityRate = reserveData['liquidityRate']
        variableBorrowRate = reserveData['variableBorrowRate']
        liquidityIndex = reserveData['liquidityIndex']
        variableBorrowIndex = reserveData['variableBorrowIndex']
        lastUpdateTimestamp = reserveData['lastUpdateTimestamp']
        currentTimeStamp = int(d.timestamp())
        isActive = reserveConfigurationData['isActive']
        isFrozen = reserveConfigurationData['isFrozen']
        supplyCap = reserveCaps['supplyCap']
        accruedToTreasury = reserveData['accruedToTreasury']
        decimals = reserveConfigurationData['decimals']

        poolMath = AaveV3PoolMath(liquidityRate, variableBorrowRate, liquidityIndex, variableBorrowIndex, lastUpdateTimestamp, currentScaledVariableDebt, scaledBalance, previousIndex, currentTimeStamp)

        if input_token.address == fixed_parameters['reserve_token']:
            fee, input_amount, nextLiquidityIndex = poolMath.withdraw(output_amount)
            # Validate Supply
            if nextLiquidityIndex == None:
                nextLiquidityIndex = liquidityIndex
            if isActive == False or isFrozen == True or isPaused == True:
                fee, input_amount = None, None
            elif supplyCap !=0:
                if rayMul((scaledTotalSupply + accruedToTreasury), nextLiquidityIndex) + input_amount > supplyCap * (10**decimals):
                    fee, input_amount = None, None
        else:
            fee, input_amount, nextLiquidityIndex = poolMath.supply(output_amount)
            # Validate Withdraw
            if isActive == False or isPaused == True:
                fee, input_amount = None, None

        return fee, input_amount

    def get_apy(self, pool_state: Dict) -> Decimal:
        # Implement APY calculation logic
        pass

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        # Implement TVL calculation logic
        pass