import unittest
import sys
from os import listdir, path, walk

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))))))
from decimal import Decimal
from templates.liquidity_module import Token
from modules.sample_market_maker_liquidity_module import MarketMakerLiquidityModule  # Replace with the actual module name

class TestMarketMakerLiquidityModule(unittest.TestCase):
    def setUp(self):
        self.liquidity_module = MarketMakerLiquidityModule()
        self.token_a = Token(address="0xTokenA", symbol="TokenA", decimals=18, reference_price=Decimal("0.0001"))
        self.token_b = Token(address="0xTokenB", symbol="TokenB", decimals=18, reference_price=Decimal("0.0002"))
        self.pool_states = {
            "token_pairs": ["0xTokenA_0xTokenB"],
            "pricelevels": {
                "0xTokenA_0xTokenB": [
                    (100, 2000000),  # 100 TokenA available at a rate of 2000000 TokenB per TokenA
                    (200, 1500000),  # 200 TokenA available at a rate of 1500000 TokenB per TokenA
                ]
            }
        }
        self.fixed_parameters = {}
    
    def test_get_amount_out_valid(self):
        input_amount = 150  # Requesting 150 TokenA
        expected_output = int(100 * 2000000 + 50 * 1500000)  # 100 at rate 2.000000 + 50 at rate 1.500000
        _, output_amount = self.liquidity_module.get_amount_out(
            self.pool_states, self.fixed_parameters, self.token_a, self.token_b, input_amount
        )
        self.assertEqual(output_amount, expected_output)

    def test_get_amount_out_insufficient_liquidity(self):
        input_amount = 500  # More than available liquidity
        result = self.liquidity_module.get_amount_out(
            self.pool_states, self.fixed_parameters, self.token_a, self.token_b, input_amount
        )
        self.assertEqual(result, (None, None))

    def test_get_amount_out_no_price_levels(self):
        pool_states_no_levels = {"token_pairs": ["0xTokenA_0xTokenB"], "pricelevels": {}}
        result = self.liquidity_module.get_amount_out(
            pool_states_no_levels, self.fixed_parameters, self.token_a, self.token_b, 50
        )
        self.assertEqual(result, (None, None))

    def test_get_amount_out_pair_not_supported(self):
        token_c = Token(address="0xTokenC", symbol="TokenC", decimals=18, reference_price=Decimal("0.0003"))
        result = self.liquidity_module.get_amount_out(
            self.pool_states, self.fixed_parameters, token_c, self.token_b, 50
        )
        self.assertEqual(result, (None, None))

if __name__ == "__main__":
    unittest.main()
