import unittest
from unittest.mock import patch, MagicMock
from stromverbrauch import print_power, power_readings

# FILE: test_stromverbrauch.py

class TestStromverbrauch(unittest.TestCase):

    @patch('stromverbrauch.get_system_power')
    @patch('stromverbrauch.calculate_cost')
    @patch('stromverbrauch.time.time')
    def test_print_power(self, mock_time, mock_calculate_cost, mock_get_system_power):
        # Mocking the time to control the elapsed time
        mock_time.side_effect = [1000, 1010]  # start time and current time
        mock_get_system_power.return_value = 50  # Mock power consumption
        mock_calculate_cost.return_value = 0.1  # Mock cost calculation

        # Clear power_readings before test
        power_readings.clear()

        # Call the function to test
        print_power()

        # Check if power_readings has the correct values
        self.assertEqual(len(power_readings), 1)
        self.assertEqual(power_readings[0], 50)

        # Call the function again to simulate another reading
        print_power()

        # Check if power_readings has the correct values
        self.assertEqual(len(power_readings), 2)
        self.assertEqual(power_readings[1], 50)

        # Check if the average power is calculated correctly
        avg_power = sum(power_readings) / len(power_readings)
        self.assertEqual(avg_power, 50)

if __name__ == '__main__':
    unittest.main()