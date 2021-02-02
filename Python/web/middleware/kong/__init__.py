# coding=utf-8
"""
Created on 2021/2/1 17:16

@author: EwdAger
"""
import logging

import requests
from requests.adapters import HTTPAdapter


class Kong:
    def __init__(self):
        self.url = ""
        self.name = ""
        self.service_path = ""

    @staticmethod
    def _request(req_url: str, request_data: dict = None, method: str = "post") -> bool:
        request_data = {} if not request_data else request_data

        session = requests.Session()
        session.mount('http://', HTTPAdapter(max_retries=3))
        session.mount('https://', HTTPAdapter(max_retries=3))

        try:
            req = getattr(session, method.lower())
            res = req(req_url, json=request_data)

            res.raise_for_status()

        except requests.exceptions.HTTPError as e:
            # 非 200
            logging.exception(e)

        except requests.exceptions.RequestException as e:
            # 超时
            logging.exception(e)

        else:
            return True

        return False

    def create_service(self):
        if not self._check_service_exist():
            logging.debug(f"{self.name} service 不存在，开始创建")
            request_data = {
                "name": f"{self.name}-service",
                "host": "",
                "port": 8081,
                "path": "/",
                "connect_timeout": 5000,
                "write_timeout": 60000,
                "read_timeout": 60000,
                "retries": 5,
                "protocol": "http"
            }
            req_url = f"{self.url}/services"

            self._request(req_url, request_data, "post")
            logging.debug(f"{self.name} service 创建成功")
        else:
            logging.debug(f"{self.name} service 已存在，跳过创建")

    def create_route(self, urls: list):
        ignore_list, auth_list = [], []

        # 暂时剔除 fastapi 自带的路由
        urls = [i for i in urls if i not in ["/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"]]

        for url in urls:
            if "ignore" in url:
                ignore_list.append(url)
            else:
                auth_list.append(url)

        if ignore_list:
            if self._check_route_exist(ignore=True):
                self._update_route(ignore_list, True)
            else:
                self._create_route(ignore_list, True)
        if auth_list:
            if self._check_route_exist(ignore=False):
                self._update_route(auth_list, False)
            else:
                self._create_route(auth_list, False)

    def _create_route(self, urls: list, ignore: bool = False):

        is_ignore = "" if ignore else "-ignore"

        request_data = {
            "service": {"name": f"{self.name}-service"},
            "name": f"{self.name}-route{is_ignore}",
            "protocols": ["http", "https"],
            "methods": ["GET", "POST", "DELETE", "PUT", "OPTION", "PATCH", "HEAD"],
            "paths": urls,
            "strip_path": False,
            "preserve_host": False
        }

        req_url = f"{self.url}/routes"
        self._request(req_url, request_data, "post")

        logging.debug(msg=f"{'非鉴权接口' if ignore else '鉴权接口'} 路由创建完毕")

    def _update_route(self, urls: list, ignore: bool = False):

        is_ignore = "" if ignore else "-ignore"

        request_data = {
            "protocols": ["http", "https"],
            "methods": ["GET", "POST", "DELETE", "PUT", "OPTION", "PATCH", "HEAD"],
            "paths": urls,
            "strip_path": False,
            "preserve_host": False
        }

        req_url = f"{self.url}/routes/{self.name}-route{is_ignore}"
        self._request(req_url, request_data, "patch")

        logging.debug(msg=f"{'非鉴权接口' if ignore else '鉴权接口'} 路由更新完毕")

    def _check_service_exist(self) -> bool:
        req_url = f"{self.url}/services/{self.name}-service"

        res = requests.get(req_url)

        return True if res.status_code == 200 else False

    def _check_route_exist(self, ignore: bool) -> bool:

        is_ignore = "" if ignore else "-ignore"
        req_url = f"{self.url}/routes/{self.name}-route{is_ignore}"

        res = requests.get(req_url)

        return True if res.status_code == 200 else False
