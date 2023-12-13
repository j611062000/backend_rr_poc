import unittest

from routing_api.util import *


def sim_api_call(times: int, inject_resp_time: int):
    actual_rest_numbers, actual_resp_time = [], []
    for i in range(times):
        if i == 0:
            resp_time = inject_resp_time
        else:
            resp_time = 0

        RoundRobin.update_response_time(RoundRobin.get_instance_index(), resp_time)
        RoundRobin.print_rr()
        actual_rest_numbers.append([n for n in RoundRobin.resting_number])
        actual_resp_time.append([n for n in RoundRobin.resp_time_stat])

    return actual_rest_numbers, actual_resp_time


class TestRR(unittest.TestCase):
    Env.update_mock_env()

    def setUp(self):
        RoundRobin.init(3)

    def test_positive_no_delay_and_timeout(self):
        expected_rest_numbers = [0 for _ in range(len(Env.app_instances))]
        for i in range(10):
            RoundRobin.update_response_time(RoundRobin.get_instance_index(), Env.slow_down_threshold_ms - 1)
            assert RoundRobin.resting_number == expected_rest_numbers

    def test_negative_one_delay(self):
        expected_rest_numbers = [[1, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
        expected_resp_time = [[Env.slow_down_threshold_ms + 1, 0, 0], [Env.slow_down_threshold_ms + 1, 0, 0],
                              [Env.slow_down_threshold_ms + 1, 0, 0], [0, 0, 0], [0, 0, 0]]

        actual_rest_numbers, actual_resp_time = sim_api_call(5, Env.slow_down_threshold_ms + 1)

        assert (expected_rest_numbers == actual_rest_numbers)
        assert (expected_resp_time == actual_resp_time)

    def test_negative_one_timeout(self):
        expected_rest_numbers = [[5, 0, 0], [4, 0, 0], [3, 0, 0], [2, 0, 0], [1, 0, 0], [0, 0, 0]]
        expected_resp_time = [[Env.app_api_timeout_ms + 1, 0, 0], [Env.app_api_timeout_ms + 1, 0, 0],
                              [Env.app_api_timeout_ms + 1, 0, 0], [Env.app_api_timeout_ms + 1, 0, 0],
                              [Env.app_api_timeout_ms + 1, 0, 0], [0, 0, 0]]

        actual_rest_numbers, actual_resp_time = sim_api_call(6, Env.app_api_timeout_ms + 1)

        print(expected_rest_numbers, actual_rest_numbers)
        assert (expected_rest_numbers == actual_rest_numbers)
        assert (expected_resp_time == actual_resp_time)


if __name__ == '__main__':
    print("test start")
    unittest.main()
