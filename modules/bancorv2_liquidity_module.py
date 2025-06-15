from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

class BancorV2LiquidityModule(LiquidityModule):
    NATIVE_ASSET = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE".lower()
    AFFILIATE_FEE_RESOLUTION = 1_000_000
    AFFILIATE_FEE = 10_000  # 1% fee, customizable by the referrer

    def _isV28OrHigherConverter(
        self,
        fixed_parameters: Dict,
        converter_address: str
    ):
        """
        bytes4 private constant IS_V28_OR_HIGHER_FUNC_SELECTOR = bytes4(keccak256("isV28OrHigher()"));

        // using assembly code to identify converter version
        // can't rely on the version number since the function had a different signature in older converters
        function isV28OrHigherConverter(IConverter _converter) internal view returns (bool) {
            bool success;
            uint256[1] memory ret;
            bytes memory data = abi.encodeWithSelector(IS_V28_OR_HIGHER_FUNC_SELECTOR);

            assembly {
                success := staticcall(
                    5000,          // isV28OrHigher consumes 190 gas, but just for extra safety
                    _converter,    // destination address
                    add(data, 32), // input buffer (starts after the first 32 bytes in the `data` array)
                    mload(data),   // input length (loaded from the first 32 bytes in the `data` array)
                    ret,           // output buffer
                    32             // output length
                )
            }

            return success && ret[0] != 0;
        }
        """

        mapping = fixed_parameters.get('v28_or_higher_converters', {})
        return converter_address.lower() in mapping

    def _is_ether_token(
        self, 
        fixed_parameters: Dict, 
        token_address: str,
        converter_address: str
    ) -> bool:
        """
            /**
            * @dev allows the owner to register/unregister ether tokens
            *
            * @param _token       ether token contract address
            * @param _register    true to register, false to unregister
            */
            function registerEtherToken(IEtherToken _token, bool _register)
                public
                ownerOnly
                validAddress(_token)
                notThis(_token)
            {
                etherTokens[_token] = _register;
            }

        Every tx called with _register == true adds the token to the etherTokens mapping.
        Every tx called with _register == false removes the token from the etherTokens mapping.
        Unfortunately, there is no event emitted when ether token is registered or unregistered.
        key = token address (lowercase)
        value = true if registered, false if unregistered
        """

        etherTokens = fixed_parameters.get('etherTokens', {})

        if self._isV28OrHigherConverter(fixed_parameters, converter_address):
            # In V28 or higher, the Ether token is always the native asset
            return token_address.lower() == self.NATIVE_ASSET
        else:
            return etherTokens.get(token_address.lower(), False)

    def get_amount_out(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        # Since BancorV2 does not accept deposit anymore, we ignore LP token swaps
        # This very function is derived from the for loop inside of doConversion function in StandardPoolConverter.sol
        # where each call is equivalent to these lines:
        #
        # if (!stepData.isV28OrHigherConverter)
        #     toAmount = ILegacyConverter(stepData.converter).change(stepData.sourceToken, stepData.targetToken, fromAmount, 1);
        # else if (etherTokens[stepData.sourceToken])
        #     toAmount = stepData.converter.convert.value(msg.value)(stepData.sourceToken, stepData.targetToken, fromAmount, msg.sender, stepData.beneficiary);
        # else
        #     toAmount = stepData.converter.convert(stepData.sourceToken, stepData.targetToken, fromAmount, msg.sender, stepData.beneficiary);
        #
        # The function also handles affiliate fees which by default are designated for GlueX as its receiver.
        # So, stepData.processAffiliateFee is always equals to true.
        #

        converter_address = pool_state.get('converter_address', '').lower()
        
        fee = 0
        output_amount = 0

        if not self._isV28OrHigherConverter(fixed_parameters, converter_address):
            # legacy converter
            output_amount, fee = self._legacy_change_out(
                pool_state, fixed_parameters,
                input_token, output_token,
                input_amount
            )
        elif self._is_ether_token(fixed_parameters, input_token.address, converter_address):
            # Native asset conversion
            pass
        else:
            # Non-native asset conversion
            pass

        # Paid in output token
        affiliate_amount = output_amount * self.AFFILIATE_FEE / self.AFFILIATE_FEE_RESOLUTION
        output_amount -= affiliate_amount
        fee += affiliate_amount

        return fee, output_amount

    def get_amount_in(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:
        # Implement logic to calculate output amount given input amount
        pass

    def get_apy(
		self, 
		pool_state: Dict, 
		underlying_amount:int,
		underlying_token:Token, 
		pool_tokens: Dict[Token.address, Token]
    ) -> int:
        token1_address = pool_state.get('token1').lower()
        token2_address = pool_state.get('token2').lower()

        rprice1 = pool_tokens[token1_address].reference_price
        rprice2 = pool_tokens[token2_address].reference_price

        token1_decimals = pool_tokens[token1_address].decimals
        token2_decimals = pool_tokens[token2_address].decimals

        if rprice1 == 0 or rprice2 == 0:
            return 0


        reserve1 = pool_state.get('reserve1', 0)
        reserve2 = pool_state.get('reserve2', 0)

        if underlying_token.address == token1_address:
            reserve1 += underlying_amount
        elif underlying_token.address == token2_address:
            reserve2 += underlying_amount

        aux_pool_state = {
            'reserve1': reserve1,
            'reserve2': reserve2,
            'token1': token1_address,
            'token2': token2_address,
        }
        tvl = self.get_tvl(aux_pool_state, pool_tokens)
        if tvl == 0:
            return 0
        

        # Fees in a pool can be obtained from `conversionFee` in this event in StandardPoolConverter contract:
        # https://etherscan.deth.net/address/0xe331821bc94187c2649E932810A60204699d45cB
        # Not to be confused with the Conversion event from BancorNetwork contract.
        #
        # Where a pool is a pair of sourceToken and targetToken. One swap transaction may emit multiple of these
        # Conversion events, one for each source/target token pair (pool).
        #
        # event Conversion(
        #     IReserveToken indexed sourceToken,
        #     IReserveToken indexed targetToken,
        #     address indexed trader,
        #     uint256 sourceAmount,
        #     uint256 targetAmount,
        #     int256 conversionFee
        # );
        fee_data = pool_state.get("fees_over_period", {})
        fee_amount1 = fee_data.get("amount1", 0)
        fee_amount2 = fee_data.get("amount2", 0)
        days = fee_data.get("days", 0)

        if days == 0:
            return 0
        
        # Normalize fee to native currency
        fee_normalized1 = fee_amount1 * rprice1 / (10 ** token1_decimals)
        fee_normalized2 = fee_amount2 * rprice2 / (10 ** token2_decimals)
        total_fees = fee_normalized1 + fee_normalized2

        daily_fees = total_fees / days
        daily_rate = daily_fees / tvl

        apy = daily_rate * 365 * 100
        apy_bps = int(apy * 10_000)

        return apy_bps

    def get_tvl(
        self, 
        pool_state: Dict, 
        pool_tokens: Dict[Token.address, Token]
    ) -> int:
        # LP Tokens are not included in the TVL calculation. Because they don't hold value.

        # Obtainable from StandardPoolConverter.reserveBalances:
        # function reserveBalances() public view returns (uint256, uint256) {
        #     return _loadReserveBalances(1, 2);
        # }
        reserve1 = pool_state.get('reserve1', 0)
        reserve2 = pool_state.get('reserve2', 0)

        # Reserve tokens 1 and 2 are btainable from StandardPoolConverter.reserveTokens()
        token1_address = pool_state.get('token1').lower()
        token2_address = pool_state.get('token2').lower()
        
        token1_decimals = pool_tokens[token1_address].decimals
        token2_decimals = pool_tokens[token2_address].decimals

        rprice1 = pool_tokens[token1_address].reference_price
        rprice2 = pool_tokens[token2_address].reference_price
        
        tvl = 0

        if token1_address == self.NATIVE_ASSET:
            tvl += reserve1
        else:
            tvl += reserve1 * rprice1 / (10 ** token1_decimals)
        if token2_address == self.NATIVE_ASSET:
            tvl += reserve2
        else:
            tvl += reserve2 * rprice2 / (10 ** token2_decimals)
        
        return tvl