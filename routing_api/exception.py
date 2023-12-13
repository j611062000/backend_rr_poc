from requests import RequestException


class NoHealthyUpstream(RequestException, ValueError):
    pass