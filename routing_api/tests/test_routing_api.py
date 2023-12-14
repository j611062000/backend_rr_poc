import unittest
from typing import Mapping
from routing_api.util import *


def sim_api_call(times: int, inject_resp_time_by_step_i: Mapping[int, int], default_resp_time: int = 0,
                 prt_result=True):
    actual_rest_numbers, actual_resp_time, chosen_instances, reasons = [], [], [], []

    for i in range(times):
        if i in inject_resp_time_by_step_i:
            resp_time = inject_resp_time_by_step_i[i]
        else:
            resp_time = default_resp_time

        chosen_instance, reason = RoundRobin.get_instance_index()
        RoundRobin.update_response_time(chosen_instance, resp_time)
        actual_rest_numbers.append([n for n in RoundRobin.resting_number])
        actual_resp_time.append([n for n in RoundRobin.resp_time_ms_stat])
        chosen_instances.append(chosen_instance)
        reasons.append(reason)

    if prt_result:
        print("actual_rest_numbers:", actual_rest_numbers, "\n")
        print("actual_resp_time:", actual_resp_time, "\n")
        print("chosen_instances:", chosen_instances, "\n")
        for idx, r in enumerate(reasons):
            print(f"{idx + 1}. {r}")
    return actual_rest_numbers, actual_resp_time, chosen_instances


class TestRR(unittest.TestCase):
    Env.update_mock_env()

    def setUp(self):
        RoundRobin.init(3)

    def test_positive_no_delay_and_no_timeout(self):
        expected_rest_numbers = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
        expected_resp_time = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
        expected_chosen_instances = [0, 1, 2, 0, 1]
        actual_rest_numbers, actual_resp_time, actual_chosen_instances = sim_api_call(5, {}, prt_result=True)

        assert actual_rest_numbers == expected_rest_numbers
        assert actual_resp_time == expected_resp_time
        assert expected_chosen_instances == actual_chosen_instances

    def test_negative_one_delay(self):
        expected_rest_numbers = [[3, 0, 0], [2, 0, 0], [1, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
        expected_resp_time = [[Env.slow_down_threshold_ms + 1, 0, 0], [Env.slow_down_threshold_ms + 1, 0, 0],
                              [Env.slow_down_threshold_ms + 1, 0, 0], [Env.slow_down_threshold_ms + 1, 0, 0],
                              [Env.slow_down_threshold_ms + 1, 0, 0], [0, 0, 0]]
        expected_chosen_instances = [0, 1, 2, 1, 2, 0]
        actual_rest_numbers, actual_resp_time, actual_chosen_instances = sim_api_call(6, {
            0: Env.slow_down_threshold_ms + 1})

        assert expected_rest_numbers == actual_rest_numbers
        assert expected_resp_time == actual_resp_time
        assert expected_chosen_instances == actual_chosen_instances

    def test_negative_all_delay(self):
        expected_rest_numbers = [[3, 0, 0], [2, 3, 0], [1, 2, 3], [3, 1, 2], [5, 0, 1], [4, 3, 0]]
        expected_resp_time = [[201, 0, 0], [201, 202, 0], [201, 202, 203], [201, 202, 203], [202, 202, 203], [202, 203, 203]]
        expected_chosen_instances = [0, 1, 2, 0, 0, 1]
        inject_resp_time = {
            0: Env.slow_down_threshold_ms + 1,
            1: Env.slow_down_threshold_ms + 2,
            2: Env.slow_down_threshold_ms + 3,
            3: Env.slow_down_threshold_ms + 1,
            4: Env.slow_down_threshold_ms + 2,
            5: Env.slow_down_threshold_ms + 3,
        }
        actual_rest_numbers, actual_resp_time, actual_chosen_instances = sim_api_call(6, inject_resp_time)

        assert expected_rest_numbers == actual_rest_numbers
        assert expected_resp_time == actual_resp_time
        assert expected_chosen_instances == actual_chosen_instances

    def test_negative_one_timeout(self):
        expected_rest_numbers = [[5, 0, 0], [4, 0, 0], [3, 0, 0], [2, 0, 0], [1, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0],
                                 [0, 0, 0], [0, 0, 0]]
        expected_resp_time = [[1001, 0, 0], [1001, 0, 0], [1001, 0, 0], [1001, 0, 0], [1001, 0, 0], [1001, 0, 0],
                              [1001, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]

        expected_chosen_instances = [0, 1, 2, 1, 2, 1, 2, 0, 1, 2]
        actual_rest_numbers, actual_resp_time, actual_chosen_instances = (
            sim_api_call(10, {0: Env.app_api_timeout_ms + 1}))
        assert expected_rest_numbers == actual_rest_numbers
        assert expected_resp_time == actual_resp_time
        assert expected_chosen_instances == actual_chosen_instances

    def test_negative_one_timeout_and_one_delay(self):
        expected_rest_numbers = [[5, 0, 0], [4, 3, 0], [3, 2, 0], [2, 1, 0], [1, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0],
                                 [0, 0, 0], [0, 0, 0]]
        expected_resp_time = [[1001, 0, 0], [1001, 201, 0], [1001, 201, 0], [1001, 201, 0], [1001, 201, 0],
                              [1001, 0, 0], [1001, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
        expected_chosen_instances = [0, 1, 2, 2, 2, 1, 2, 0, 1, 2]
        inject_resp_time = {0: Env.app_api_timeout_ms + 1, 1: Env.slow_down_threshold_ms + 1}

        actual_rest_numbers, actual_resp_time, actual_chosen_instances = (
            sim_api_call(10, inject_resp_time))

        assert expected_rest_numbers == actual_rest_numbers
        assert expected_resp_time == actual_resp_time
        assert expected_chosen_instances == actual_chosen_instances

    def test_all_timeout(self):
        steps = 10
        inject_resp_time = {}
        for i in range(steps):
            inject_resp_time[i] = Env.app_api_timeout_ms + 1
        actual_rest_numbers, actual_resp_time, actual_chosen_instances = (
            sim_api_call(10, inject_resp_time))

        expected_rest_numbers = [[5, 0, 0], [4, 5, 0], [3, 4, 5], [2, 3, 9], [1, 2, 13], [0, 1, 17], [5, 0, 16],
                                 [4, 5, 15], [3, 4, 19], [2, 3, 23]]
        expected_resp_time = [[1001, 0, 0], [1001, 1001, 0], [1001, 1001, 1001], [1001, 1001, 1001], [1001, 1001, 1001],
                              [1001, 1001, 1001], [1001, 1001, 1001], [1001, 1001, 1001], [1001, 1001, 1001],
                              [1001, 1001, 1001]]

        expected_chosen_instances = [0, 1, 2, -1, -1, -1, 0, 1, -1, -1]
        assert expected_rest_numbers == actual_rest_numbers
        assert expected_resp_time == actual_resp_time
        assert expected_chosen_instances == actual_chosen_instances


if __name__ == '__main__':
    print("test start")
    unittest.main()
