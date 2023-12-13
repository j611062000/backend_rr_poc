import os
from datetime import datetime

from requests import Response

from .env import Env


class RoundRobin(object):
    env = Env
    backend_srv_number: int = 0
    # in ms
    resp_time_stat: list[int] = []
    resting_number: list[int] = []
    cur_idx = 0

    @staticmethod
    def print_rr():
        print("----------- \n")
        print(f"slow down ms threshold, {RoundRobin.env.slow_down_threshold_ms}")
        print(f"slow down rest, {RoundRobin.env.slow_down_rest}")
        print(f"timeout ms threshold, {RoundRobin.env.app_api_timeout_ms}")
        print(f"timeout sec threshold, {RoundRobin.env.app_api_timeout_seconds}")
        print(f"timeout rest, {RoundRobin.env.timeout_rest}")
        print("resp_time_stat: ", RoundRobin.resp_time_stat)
        print("resting_number: ", RoundRobin.resting_number)
        print("----------- \n")

    @staticmethod
    def init(backend_srv_number: int):
        RoundRobin.backend_srv_number = backend_srv_number
        RoundRobin.resp_time_stat = [0 for _ in range(backend_srv_number)]
        RoundRobin.resting_number = [0 for _ in range(backend_srv_number)]

    @staticmethod
    def update_resting_number(rest_numbers: list[int], idx: int, cnt: int) -> None:
        cur_numer = rest_numbers[idx]
        new_numer = cur_numer + cnt
        if new_numer < 0:
            rest_numbers[idx] = 0
        else:
            rest_numbers[idx] = new_numer

    @staticmethod
    def get_instance_index() -> int:
        RoundRobin.cur_idx = (RoundRobin.cur_idx + 1) % RoundRobin.backend_srv_number
        print("cur_idx", RoundRobin.cur_idx)
        visited = 0

        while visited < RoundRobin.backend_srv_number:
            print("get_instance_index", RoundRobin.resting_number[visited], RoundRobin.cur_idx)
            RoundRobin.update_resting_number(RoundRobin.resting_number, RoundRobin.cur_idx, -1)
            if RoundRobin.resting_number[RoundRobin.cur_idx] == 0:
                return RoundRobin.cur_idx
            visited += 1
            RoundRobin.cur_idx += 1

        return RoundRobin.resp_time_stat.index(min(RoundRobin.resp_time_stat))

    @staticmethod
    def update_response_time(cur_idx: int, resp_time_ms: int) -> None:
        RoundRobin.resp_time_stat[cur_idx] = resp_time_ms

        if RoundRobin.env.slow_down_threshold_ms <= resp_time_ms < RoundRobin.env.app_api_timeout_ms:
            RoundRobin.update_resting_number(RoundRobin.resting_number, cur_idx, RoundRobin.env.slow_down_rest)
        elif resp_time_ms >= RoundRobin.env.app_api_timeout_ms:
            RoundRobin.update_resting_number(RoundRobin.resting_number, cur_idx, RoundRobin.env.timeout_rest)


class Api(object):
    @staticmethod
    def get_success_response(response: Response) -> dict:
        return {
            "status": "success",
            "data_from_upstream": response.json(),
            "upstream_index": RoundRobin.cur_idx + 1,
            "upstream_service": Env.app_instances[RoundRobin.cur_idx],
            "response_time_ms_statistics": RoundRobin.resp_time_stat,
            "rest_number": RoundRobin.resting_number,
        }


def get_response_time_ms(start: datetime) -> int:
    return int((datetime.now() - start).total_seconds() * 1000)
