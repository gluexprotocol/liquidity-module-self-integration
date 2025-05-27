from .math import SafeMath, Math
class LPTokenSwap():

    @staticmethod
    def mint(
        _reserve0: int,
        _reserve1: int,
        balance0: int,
        balance1: int,
        feeTo: str,
        _kLast: int,
        totalSupply: int,
        MINIMUM_LIQUIDITY: int
    ):
        amount0: int = balance0 - _reserve0
        amount1: int = balance1 - _reserve1

        _, _totalSupply = LPTokenSwap._mintFee(_reserve0, _reserve1, feeTo, _kLast, totalSupply)

        if (_totalSupply == 0):
            liquidity = SafeMath.sub(Math.sqrt(SafeMath.mul(amount0, amount1)), MINIMUM_LIQUIDITY)
            _totalSupply = LPTokenSwap._mint(_totalSupply, MINIMUM_LIQUIDITY); # permanently lock the first MINIMUM_LIQUIDITY tokens
        else:
            liquidity = min(SafeMath.mul(amount0, _totalSupply) // _reserve0, SafeMath.mul(amount1, _totalSupply) // _reserve1)

        if (liquidity <= 0):
            raise Exception ('UniswapV2: INSUFFICIENT_LIQUIDITY_MINTED')
        _totalSupply = LPTokenSwap._mint(_totalSupply, liquidity)

        return liquidity

    @staticmethod
    def burn(
        _reserve0: int,
        _reserve1: int,
        balance0: int,
        balance1: int,
        liquidity: int, #balanceOf[address(this)]
        feeTo: str,
        _kLast: int,
        totalSupply: int
    ):

        feeOn, _totalSupply = LPTokenSwap._mintFee(_reserve0, _reserve1, feeTo, _kLast, totalSupply)
        amount0: int = SafeMath.mul(liquidity, balance0) // _totalSupply # using balances ensures pro-rata distribution
        amount1: int = SafeMath.mul(liquidity, balance1) // _totalSupply # using balances ensures pro-rata distribution

        if not (amount0 > 0 and amount1 > 0):
            raise Exception ('UniswapV2: INSUFFICIENT_LIQUIDITY_BURNED')

        LPTokenSwap._burn(_totalSupply, liquidity)

        if (feeOn):
            _kLast = SafeMath.mul(_reserve0, _reserve1)

        return amount0, amount1



    # Utils

    @staticmethod
    def _mintFee(
        _reserve0: int,
        _reserve1: int,
        feeTo: str,
        _kLast: int,
        totalSupply
    ): 
        feeOn: bool = feeTo != "0x0000000000000000000000000000000000000000"
        if (feeOn):
            if (_kLast != 0):
                rootK = Math.sqrt(SafeMath.mul(_reserve0, _reserve1))
                rootKLast = Math.sqrt(_kLast)
                if (rootK > rootKLast):
                    numerator = SafeMath.mul(totalSupply, SafeMath.sub(rootK, rootKLast))
                    denominator = SafeMath.add(SafeMath.mul(rootK, 5), rootKLast)
                    liquidity = numerator // denominator
                    if (liquidity > 0):
                        totalSupply = LPTokenSwap._mint(totalSupply, liquidity)        
        elif (_kLast != 0):
            kLast = 0

        return feeOn, totalSupply


    @staticmethod
    def _mint(
        totalSupply: int,
        value: int
    ):
        return SafeMath.add(totalSupply, value)

    @staticmethod
    def _burn(
        totalSupply: int,
        value: int
    ):
        return SafeMath.sub(totalSupply, value)