import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime

import sys
from os import listdir, path, walk

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))))))

from modules.aave_v3_liquidity_module import Aavev3LiquidityModule
from templates.liquidity_module import Token

SECONDS_PER_YEAR = 365 * 24 * 60 * 60
RAY = 10**27

class TestAavev3LiquidityModule(unittest.TestCase):
    def setUp(self):
        self.module = Aavev3LiquidityModule()
        self.now = int(datetime.now().timestamp())
        self.input_token = Token(address="0xTokenA", decimals=18, symbol="TokenA", reference_price=1)
        self.output_token = Token(address="0xTokenA", decimals=18, symbol="TokenA", reference_price=1)  # Same address for supply

        self.valid_pool_states = {
            "ReserveData": {
                "liquidityRate": int(0.03 * RAY),
                "variableBorrowRate": int(0.05 * RAY),
                "liquidityIndex": RAY,
                "variableBorrowIndex": RAY,
                "lastUpdateTimestamp": self.now - 1000,
                "accruedToTreasury": 0
            },
            "ScaledBalance": 1000,
            "PreviousIndex": RAY,
            "ScaledTotalSupply": 500000,
            "ReserveConfigurationData": {
                "isActive": True,
                "isFrozen": False,
                "decimals": 18
            },
            "IsPaused": False,
            "ReserveCaps": {
                "supplyCap": 1000000
            },
            "ATokenScaledTotalSupply": 100000
        }

        self.fixed_parameters = {
            "reserve_token": "0xTokenA"
        }

    def test_supply_successful(self):
        fee, amount_out = self.module.get_amount_out(
            self.valid_pool_states, self.fixed_parameters, self.input_token, self.output_token, 1000
        )
        self.assertIsNotNone(amount_out)
        self.assertEqual(amount_out, 1000)

    def test_withdraw_successful(self):
        self.input_token.address = "0xOtherToken"  # force withdraw path
        fee, amount_out = self.module.get_amount_out(
            self.valid_pool_states, self.fixed_parameters, self.input_token, self.output_token, 1000
        )
        self.assertIsNotNone(amount_out)
        self.assertGreaterEqual(amount_out, 0)

    def test_supply_paused(self):
        self.valid_pool_states["IsPaused"] = True
        fee, amount_out = self.module.get_amount_out(
            self.valid_pool_states, self.fixed_parameters, self.input_token, self.output_token, 1000
        )
        self.assertIsNone(amount_out)

    def test_supply_above_cap(self):
        self.valid_pool_states["ReserveCaps"]["supplyCap"] = 1  # very low cap
        fee, amount_out = self.module.get_amount_out(
            self.valid_pool_states, self.fixed_parameters, self.input_token, self.output_token, 10**20
        )
        self.assertIsNone(amount_out)

    def test_withdraw_when_frozen(self):
        self.valid_pool_states["ReserveConfigurationData"]["isFrozen"] = True
        self.input_token.address = "0xTokenA"
        fee, amount_out = self.module.get_amount_out(
            self.valid_pool_states, self.fixed_parameters, self.input_token, self.output_token, 1000
        )
        self.assertIsNone(amount_out)

    def test_get_amount_in_supply(self):
        fee, amount_in = self.module.get_amount_in(
            self.valid_pool_states, self.fixed_parameters, self.input_token, self.output_token, 1000
        )
        self.assertIsNotNone(amount_in)
        self.assertGreater(amount_in, 0)

    def test_get_amount_in_paused(self):
        self.valid_pool_states["IsPaused"] = True
        fee, amount_in = self.module.get_amount_in(
            self.valid_pool_states, self.fixed_parameters, self.input_token, self.output_token, 1000
        )
        self.assertIsNone(amount_in)

    def test_get_amount_in_withdraw(self):
        self.input_token.address = "0xOtherToken"
        fee, amount_in = self.module.get_amount_in(
            self.valid_pool_states, self.fixed_parameters, self.input_token, self.output_token, 1000
        )
        self.assertIsNotNone(amount_in)

if __name__ == '__main__':
    unittest.main()