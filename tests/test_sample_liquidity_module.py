import unittest
from unittest.mock import MagicMock
from decimal import Decimal
import sys
from os import listdir, path, walk

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))))))

from modules.sample_liquidity_module import SampleLiquidityModule

class TestSampleLiquidityModule(unittest.TestCase):
    def setUp(self):
        # Mock the SampleLiquidityModule class
        self.module = SampleLiquidityModule()
        self.module.add_liquidity_to_pool = MagicMock(
            side_effect=lambda *args, **kwargs: {
                "bpt_amount_out_raw": 100,
                "amounts_in_raw": [100, 0]
            }
        )
        self.module.remove_liquidity_from_pool = MagicMock(
            side_effect=lambda *args, **kwargs: {
                "amounts_out_raw": [0, 50], 
                "bpt_amount_in_raw": 100
            }
        )
        self.module.swap_tokens = MagicMock(return_value=75)

        # Mock pool_states and fixed_parameters
        self.pool_states = {
            "stablePoolDynamicData": {
                "amplificationParameter": 100,
                "staticSwapFeePercentage": 0.01,
                "balancesLiveScaled18": [1000, 2000],
                "tokenRates": [1, 1],
                "totalSupply": 10000,
            },
            "aggregateFeePercentages": {"aggregateSwapFeePercentage": 0.01},
            "poolConfig": {
                "isPoolRegistered": True,
                "isPoolInitialized": True,
                "isPoolPaused": False,
                "isPoolInRecoveryMode": False,
                "disableUnbalancedLiquidity": False,
            },
            "fees": 1000,
            "tvl": 1000000,
            "days_accumulated": 10
        }
        self.fixed_parameters = {
            "pool_address": "0xPoolAddress",
            "lp_token_address": "0xLPToken",
            "tokens": ["0xTokenA", "0xTokenB"],
            "decimal_scaling_factors": [1, 1],
            "max_invariant_ratio": 1.5,
            "min_invariant_ratio": 0.5,
        }

        # Mock Token class
        self.input_token = MagicMock()
        self.output_token = MagicMock()

    def test_pool_not_registered_or_initialized(self):
        self.pool_states["poolConfig"]["isPoolRegistered"] = False
        fee, output_amount = self.module.get_amount_out(
            self.pool_states, self.fixed_parameters, self.input_token, self.output_token, 100
        )
        self.assertIsNone(fee)
        self.assertIsNone(output_amount)

    def test_add_liquidity_get_amount_out(self):
        self.input_token.address = "0xTokenA"
        self.output_token.address = "0xLPToken"
        fee, output_amount = self.module.get_amount_out(
            self.pool_states, self.fixed_parameters, self.input_token, self.output_token, 100
        )
        self.assertEqual(fee, 0)
        self.assertEqual(output_amount, 100)

    def test_remove_liquidity_get_amount_out(self):
        self.input_token.address = "0xLPToken"
        self.output_token.address = "0xTokenB"
        fee, output_amount = self.module.get_amount_out(
            self.pool_states, self.fixed_parameters, self.input_token, self.output_token, 100
        )
        self.assertEqual(fee, 0)
        self.assertEqual(output_amount, 50)

    def test_swap_tokens_get_amount_out(self):
        self.input_token.address = "0xTokenA"
        self.output_token.address = "0xTokenB"
        fee, output_amount = self.module.get_amount_out(
            self.pool_states, self.fixed_parameters, self.input_token, self.output_token, 100
        )
        self.assertEqual(fee, 0)
        self.assertEqual(output_amount, 75)
        
    def test_add_liquidity_get_amount_in(self):
        self.input_token.address = "0xTokenA"
        self.output_token.address = "0xLPToken"
        fee, input_amount = self.module.get_amount_in(
            self.pool_states, self.fixed_parameters, self.input_token, self.output_token, 100
        )
        self.assertEqual(fee, 0)
        self.assertEqual(input_amount, 100)

    def test_remove_liquidity_get_amount_in(self):
        self.input_token.address = "0xLPToken"
        self.output_token.address = "0xTokenB"
        fee, input_amount = self.module.get_amount_in(
            self.pool_states, self.fixed_parameters, self.input_token, self.output_token, 50
        )
        self.assertEqual(fee, 0)
        self.assertEqual(input_amount, 100)

    def test_swap_tokens_get_amount_in(self):
        self.input_token.address = "0xTokenA"
        self.output_token.address = "0xTokenB"
        fee, input_amount = self.module.get_amount_in(
            self.pool_states, self.fixed_parameters, self.input_token, self.output_token, 75
        )
        self.assertEqual(fee, 0)
        self.assertEqual(input_amount, 75)
        
    def test_get_apy(self):
        apy = self.module.get_apy(self.pool_states)
        assert isinstance(apy, Decimal)
        assert apy > 0


    def test_get_tvl(self):
        tvl = self.module.get_tvl(self.pool_states)
        assert isinstance(tvl, int)
        assert tvl == 1000000

if __name__ == "__main__":
    unittest.main()