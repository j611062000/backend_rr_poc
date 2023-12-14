from datetime import datetime

from requests import Response

try:
    from env import Env
except ImportError:
    from routing_api.env import Env


class RoundRobin(object):
    env = Env
    backend_srv_number: int = 0
    resp_time_ms_stat: list[int] = []
    prev_resp_time_ms_stat: list[int] = []
    resting_number: list[int] = []
    prev_resting_number: list[int] = []
    cur_idx: int = 0
    invalid_cur_idx: int = -1

    @staticmethod
    def circle_inc_cur_idx():
        RoundRobin.cur_idx = (RoundRobin.cur_idx + 1) % RoundRobin.backend_srv_number

    @staticmethod
    def update_cur_idx(idx: int) -> None:
        RoundRobin.cur_idx = idx

    @staticmethod
    def print_rr():
        print("----------- \n")
        print(f"slow down ms threshold, {RoundRobin.env.slow_down_threshold_ms}")
        print(f"slow down rest, {RoundRobin.env.slow_down_rest}")
        print(f"timeout ms threshold, {RoundRobin.env.app_api_timeout_ms}")
        print(f"timeout sec threshold, {RoundRobin.env.app_api_timeout_seconds}")
        print(f"timeout rest, {RoundRobin.env.timeout_rest}")
        print("resp_time_stat: ", RoundRobin.resp_time_ms_stat)
        print("resting_number: ", RoundRobin.resting_number)
        print("----------- \n")

    @staticmethod
    def init(backend_srv_number: int, cur_idx: int = 0) -> None:
        RoundRobin.backend_srv_number = backend_srv_number
        RoundRobin.cur_idx = cur_idx
        RoundRobin.resp_time_ms_stat = [0 for _ in range(backend_srv_number)]
        RoundRobin.resting_number = [0 for _ in range(backend_srv_number)]
        RoundRobin.prev_resp_time_ms_stat = [0 for _ in range(backend_srv_number)]
        RoundRobin.prev_resting_number = [0 for _ in range(backend_srv_number)]

    @staticmethod
    def update_resting_number(rest_numbers: list[int], idx: int, cnt: int) -> None:
        cur_numer = rest_numbers[idx]
        new_numer = cur_numer + cnt
        RoundRobin.prev_resting_number[idx] = cur_numer
        if new_numer < 0:
            rest_numbers[idx] = 0
        else:
            rest_numbers[idx] = new_numer

    @staticmethod
    def update_all_resting_number(rest_numbers: list[int], cnt: int) -> None:
        for i in range(len(rest_numbers)):
            RoundRobin.update_resting_number(rest_numbers, i, cnt)

    '''
    [Purpose]
    This method is designed to retrieve an instance index based on certain conditions, 
    presumably for a round-robin load balancing mechanism.
    
    [Initialization]
    visited: Tracks the number of instances checked.
    chosen_idx: Represents the chosen instance index. Initialized as -1.
    
    [Loop Through Instances]
    The method iterates through instances (backend_srv_number times) to find an available instance with 
    resting_number equal to 0. It updates chosen_idx when it finds an available instance.
    
    [Fallback Mechanism]
    If no instance with resting_number 0 is found:
    It checks if all response times are below a certain threshold (Env.app_api_timeout_ms). 
    If so, it selects the instance with the minimum response time.
    Updates cur_idx to the chosen instance.
    
    [Update and Return]
    Updates resting_number for all instances.
    Increases cur_idx in a circular manner.
    Returns the chosen instance index.
    '''

    @staticmethod
    def get_instance_index() -> tuple[int, str]:
        visited: int = 0
        chosen_idx = RoundRobin.invalid_cur_idx
        decision_reason = ""

        while visited < RoundRobin.backend_srv_number:
            if RoundRobin.resting_number[RoundRobin.cur_idx] == 0:
                chosen_idx = RoundRobin.cur_idx
                decision_reason = f"service {chosen_idx} is chosen because its resting number is zero"
                break
            visited += 1
            RoundRobin.circle_inc_cur_idx()

        if chosen_idx == RoundRobin.invalid_cur_idx:
            if all(resp_time < Env.app_api_timeout_ms for resp_time in RoundRobin.resp_time_ms_stat):
                min_resp_time = min(RoundRobin.resp_time_ms_stat)
                chosen_idx = RoundRobin.resp_time_ms_stat.index(min_resp_time)
                RoundRobin.update_cur_idx(chosen_idx)
                decision_reason = f"service {chosen_idx} is chosen because its previous response time is the smallest, {min_resp_time}"
            else:
                decision_reason = (f"no service is chosen (idx = -1) because all of their historical "
                                   f"response time are greater than timeout threshold (ms) {Env.app_api_timeout_ms}")

        RoundRobin.update_all_resting_number(RoundRobin.resting_number, -1)
        RoundRobin.circle_inc_cur_idx()
        return chosen_idx, decision_reason

    @staticmethod
    def update_response_time(cur_idx: int, resp_time_ms: int) -> str:
        RoundRobin.prev_resp_time_ms_stat = [t for t in RoundRobin.resp_time_ms_stat]
        RoundRobin.resp_time_ms_stat[cur_idx] = resp_time_ms
        reason = ""

        if RoundRobin.env.slow_down_threshold_ms <= resp_time_ms < RoundRobin.env.app_api_timeout_ms:
            RoundRobin.update_resting_number(RoundRobin.resting_number, cur_idx, RoundRobin.env.slow_down_rest)
            reason = f"{cur_idx} is slow down now, so we add the resting number {RoundRobin.env.slow_down_rest} for it."
        elif resp_time_ms >= RoundRobin.env.app_api_timeout_ms:
            RoundRobin.update_resting_number(RoundRobin.resting_number, cur_idx, RoundRobin.env.timeout_rest)
            reason = f"{cur_idx} is timeout now, so we add the resting number {RoundRobin.env.timeout_rest} for it."

        return " | " + reason if reason != "" else ""


def lst_to_str(l: list[any]) -> str:
    return ",".join([str(e) for e in l])


class Api(object):
    @staticmethod
    def get_response(status: str, response: Response = None, reason: str = "", cur_idx: int = -1) -> dict:
        return {
            "1_status": status,
            "2_data_from_upstream": response.json() if response else "",
            "3_upstream": {
                "upstream_index": cur_idx,
                "upstream_service": Env.app_instances[cur_idx] if cur_idx >= 0 else "no service is chosen",
            },
            "4_response_time_ms_statistic": {
                "current": lst_to_str(RoundRobin.resp_time_ms_stat),
                "previous": lst_to_str(RoundRobin.prev_resp_time_ms_stat),
            },
            "5_resting_number": {
                "current": lst_to_str(RoundRobin.resting_number),
                "previous": lst_to_str(RoundRobin.prev_resting_number),
            },
            "6_explanation": reason,
            "7_metadata": {
                "slow_down_threshold_ms": RoundRobin.env.slow_down_threshold_ms,
                "timeout_threshold_ms": RoundRobin.env.app_api_timeout_ms
            }
        }


def get_response_time_ms(start: datetime) -> int:
    return int((datetime.now() - start).total_seconds() * 1000)
