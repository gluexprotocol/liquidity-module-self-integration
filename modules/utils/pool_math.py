from decimal import Decimal, getcontext

from modules.utils.base_math import *

getcontext().prec = 30
SECONDS_PER_YEAR = 365 * 24 * 60 * 60

class AaveV3PoolMath:
    def __init__(self, liquidityRate, variableBorrowRate, liquidityIndex, variableBorrowIndex, lastUpdateTimestamp, currentScaledVariableDebt, scaledBalance, previousIndex, currentTimeStamp):
        self.liquidityRate = liquidityRate
        self.liquidityIndex = liquidityIndex
        self.variableBorrowRate = variableBorrowRate
        self.variableBorrowIndex = variableBorrowIndex
        self.lastUpdateTimestamp = lastUpdateTimestamp
        self.currentScaledVariableDebt = currentScaledVariableDebt
        self.scaledBalance = scaledBalance
        self.previousIndex = previousIndex
        self.currentTimeStamp = currentTimeStamp

    def calculateLinearInterest(self, rate, lastUpdateTimestamp, currentTimeStamp):
        time_difference = currentTimeStamp - lastUpdateTimestamp
        result = (rate * time_difference) / SECONDS_PER_YEAR
        return RAY + Decimal(result)

    def calculateCompoundedInterest(self, rate, lastUpdateTimestamp, currentTimeStamp):
        exp = currentTimeStamp - lastUpdateTimestamp
        if(exp == 0):
            return RAY
        expMinusOne = exp - 1
        expMinusTwo = exp - 2 if exp > 2 else 0
        basePowerTwo = rayMul(rate, rate) / (SECONDS_PER_YEAR * SECONDS_PER_YEAR)
        basePowerThree = rayMul(basePowerTwo, rate) / SECONDS_PER_YEAR
        secondTerm = exp * expMinusOne * basePowerTwo
        secondTerm = secondTerm / 2
        thirdTerm = exp * expMinusOne * expMinusTwo * basePowerThree
        thirdTerm = thirdTerm / 6
        result = (rate * exp) / Decimal(SECONDS_PER_YEAR) + Decimal(secondTerm) + Decimal(thirdTerm)
        return RAY + Decimal(result)

    def updateIndexes(self, currentLiquidityRate, liquidityIndex, currentVariableBorrowRate, variableBorrowIndex, currentScaledVariableDebt, lastUpdateTimestamp, currentTimeStamp):
        if(currentLiquidityRate != 0):
            cumulatedLiquidityInterest = self.calculateLinearInterest(currentLiquidityRate, lastUpdateTimestamp, currentTimeStamp)
            nextLiquidityIndex = rayMul(cumulatedLiquidityInterest, liquidityIndex)

        return nextLiquidityIndex

    def updateState(self):
        if(self.lastUpdateTimestamp == self.currentTimeStamp):
            return self.liquidityIndex
        nextLiquidityIndex = self.updateIndexes(self.liquidityRate, self.liquidityIndex, self.variableBorrowRate, self.variableBorrowIndex, self.currentScaledVariableDebt, self.lastUpdateTimestamp, self.currentTimeStamp)
        self.lastUpdateTimestamp = self.currentTimeStamp
        return nextLiquidityIndex

    def burn(self, amount, nextLiquidityIndex, scaledBalance, previousIndex):
        # amountScaled = rayDiv(amount, nextLiquidityIndex)
        balanceIncrease = rayMul(scaledBalance, nextLiquidityIndex) - rayMul(scaledBalance, previousIndex)
        amountToTransfer = 0
        if(Decimal(balanceIncrease) > Decimal(amount)):
            amountToTransfer = Decimal(balanceIncrease) - Decimal(amount)
        else:
            amountToTransfer = Decimal(amount) - Decimal(balanceIncrease)
        return amountToTransfer

    def mint(self, amount, nextLiquidityIndex, scaledBalance, previousIndex):
        # amountScaled = rayDiv(amount, nextLiquidityIndex)
        balanceIncrease = rayMul(scaledBalance, nextLiquidityIndex) - rayMul(scaledBalance, previousIndex)
        amountToMint = Decimal(amount) + Decimal(balanceIncrease)
        return amountToMint

    def withdraw(self, amount):
        try:
            nextLiquidityIndex = self.updateState()
            amountScaled = self.burn(amount, nextLiquidityIndex, self.scaledBalance, self.previousIndex)
            return 0, int(amountScaled), nextLiquidityIndex
        except:
            return 0, amount, None

    def supply(self, amount):
        try:
            nextLiquidityIndex = self.updateState()
            amountScaled = self.mint(amount, nextLiquidityIndex, self.scaledBalance, self.previousIndex)
            return 0, int(amountScaled), nextLiquidityIndex
        except:
            return 0, amount, None