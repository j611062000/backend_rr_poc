import os
from typing import Optional

import consul


def safe_get_env_var_as_int(var_name: str, default_val: int = 0) -> int:
    try:
        return int(os.getenv(var_name))
    except:
        return default_val


def get_app_instances(env: str, port_in_docker: int) -> list[str]:
    value = ""

    try:
        c = consul.Consul(host='consul')
        # Specify the key you want to read
        consul_key = 'app_instances'
        # Retrieve the value associated with the key from Consul KV store
        _, consul_kv_data = c.kv.get(consul_key)

        if consul_kv_data is not None:
            # Convert the value to string (assuming it's stored as bytes)
            value = str(consul_kv_data['Value'].decode('utf-8')).split(",")
    except Exception as e:
        consul_kv_data = None

    if env == "docker":
        if consul_kv_data is not None and len(value) > 0:
            app_instances = value

        else:
            app_instances = [
                f"http://application_api_0:{port_in_docker}",
                f"http://application_api_1:{port_in_docker}",
                f"http://application_api_2:{port_in_docker}"
            ]
    else:
        app_instances = [
            f"http://localhost:10001",
            f"http://localhost:10002",
            f"http://localhost:10003"
        ]

    return app_instances


class Env(object):
    slow_down_threshold_ms: int = safe_get_env_var_as_int('SLOW_DOWN_THRESHOLD_MS')
    app_api_timeout_ms: int = safe_get_env_var_as_int('APP_API_TIMEOUT_MS')
    app_api_timeout_seconds: int = app_api_timeout_ms // 1000
    upstream_port: int = safe_get_env_var_as_int('UPSTREAM_PORT')
    slow_down_rest: int = safe_get_env_var_as_int('SLOW_DOWN_REST_NUMBER')
    timeout_rest: int = safe_get_env_var_as_int('TIMEOUT_REST_NUMBER')
    env: Optional[str] = os.getenv("ENV")
    app_instances: list[str] = get_app_instances(env, upstream_port)

    @staticmethod
    def update_mock_env():
        Env.slow_down_threshold_ms = 200
        Env.app_api_timeout_ms = 1000
        Env.app_api_timeout_seconds = 1
        Env.upstream_port = 5000
        Env.slow_down_rest = 3
        Env.timeout_rest = 5
        Env.app_instances = ["app1", "app2", "app3"]
