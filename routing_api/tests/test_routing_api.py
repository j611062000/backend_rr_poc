import unittest
from unittest.mock import patch
from routing_api.env import Env
from routing_api.util import *


class TestRR(unittest.TestCase):
    Env.update_mock_env()
    RoundRobin.init(3)
    def test_rr(self):
        RoundRobin.update_response_time(1, 1000)
        RoundRobin.print_rr()

        RoundRobin.update_response_time(1, 10)
        RoundRobin.print_rr()

        RoundRobin.update_response_time(1, 10)
        RoundRobin.print_rr()
        assert RoundRobin.resp_time_stat[1] == 11
        # round_robin()  # Mock the requests.get function


if __name__ == '__main__':
    print("test start")
    unittest.main()
