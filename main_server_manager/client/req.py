import requests


class Client:
    def __init__(self, host, port):
        self.req_link = f'http://{host}:{port}'

    def req(self, path: str, **kwargs):
        """
        Function for request to server.
        :param path: Path to server. Exemple: /get_proxies
        :param kwargs: arguments for specifying request
        :return: response from server

        Args:
            - elements for post requests
            - headers: dict
            - params: dict
        """
        headers = kwargs.pop('headers', {})
        params = kwargs.pop('params', {})

        if kwargs:
            return requests.post(self.req_link + path, data=kwargs, headers=headers, params=params)
        return requests.get(self.req_link + path, headers=headers, params=params)

