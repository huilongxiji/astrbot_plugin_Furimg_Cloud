import os

import httpx

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.core import AstrBotConfig

from . import config as plugin_config
from .config import (
    CHECK,
    LOGIN,
    PICTURES_URL,
    SYJ_RANDOM,
    SYJ_RANDOM_NAME,
    TKAPPLY,
    TKQUERY,
)


class fox:
    def __init__(self):
        self.random = SYJ_RANDOM
        self.random_name = SYJ_RANDOM_NAME
        self.pictures_url = PICTURES_URL

    async def random_data(self, type: str = "", name = ""):
        """随机兽图数据获取实现
        type: 0.设定 1.毛图 2.插画 留空则随机"""
        try:
            async with httpx.AsyncClient() as client:
                data = await client.get(
                    url=self.random + type + f"&name={name}",
                    cookies=account_system.cookies_q
                )
        except TimeoutError:
            logger.error("随机搜索模式访问超时")
            return (False, "随机搜索模式访问超时", {})
        except Exception as e:
            logger.error(f"随机搜索模式访问异常: {e}")
            return (False, "随机搜索模式访问异常，请查看控制台输出", {})
        else:
            if data.status_code == 200:
                return (True, "查询目标获取成功", data.json())
            else:
                logger.error(f"请求异常， http 状态码: {data.status_code}")
                return (False, f"API 请求发送失败， http 状态码异常{data.status_code}", {})

    async def pictures_sid(self, sid: str) -> tuple:
        """指定sid数据获取"""
        try:
            async with httpx.AsyncClient() as client:
                data = await client.get(
                    url=self.pictures_url + sid,
                    cookies=account_system.cookies_q
                )
        except TimeoutError:
            logger.error("sid搜索模式访问超时")
            return (False, "sid搜索模式访问超时", {})
        except Exception as e:
            logger.error(f"sid搜索模式访问异常: {e}")
            return (False, "sid 搜索模式访问异常，请查看控制台输出", {})
        else:
            if data.status_code == 200:
                json = data.json()
                if json["code"] == "20600":
                    return (True, "查询目标获取成功", json)
                else:
                    return (False, str(json["msg"]), {})
            else:
                logger.error(f"请求异常， http 状态码: {data.status_code}")
                return (False, f"API 请求发送失败， http 状态码异常{data.status_code}", {})

    async def pictures_name(self, name: str) -> tuple:
        """指定名称数据获取"""
        try:
            async with httpx.AsyncClient() as client:
                data = await client.get(
                    url=self.random_name + name,
                    cookies=account_system.cookies_q
                )
        except TimeoutError:
            logger.error("名称搜索模式访问超时")
            return (False, "名称搜索模式访问超时", {})
        except Exception as e:
            logger.error(f"名称搜索模式访问异常: {e}")
            return (False, "名称搜索模式访问异常，请查看控制台输出", {})
        else:
            if data.status_code == 200:
                json = data.json()
                if json["code"] == "20900":
                    return await self.pictures_sid(json["picture"]["id"])
                else:
                    return (False, str(json["msg"]), {})
            else:
                logger.error(f"请求异常， http 状态码: {data.status_code}")
                return (False, f"API 请求发送失败， http 状态码异常{data.status_code}", {})

    async def goujian(self, _data: tuple, type: int) -> list:
        """消息构建，单条数据处理"""
        code, msg, json = _data
        if not code:
            return [
                Comp.Plain(msg)
            ]
        type_data = {"0":"随机搜索", "1":"sid搜索", "2":"名称搜索"}
        name = json["name"]
        sid = json["id"]
        suggest = json["suggest"]
        url = json["url"]
        _type = type_data[str(type)]
        return [
            Comp.Plain(f"""======毛毛图鉴======
                        名称: {name}
                        SID: {sid}
                        搜索方式: 【{_type}】
                        留言: {suggest}"""

                        .replace(" ", "")
                        .replace("\t", "")),
            Comp.Image.fromURL(url), # 从 URL 发送图片
            Comp.Plain("======FurBot======\n更多功能请发送“兽云菜单”")
        ]

    async def API_Data(self, text: str, type: int) -> list:
        """消息构建，总处理
        type [0:随机搜索, 1:sid搜索, 2:名称搜索]
        """
        sid = await self.pictures_sid(text)
        name = await self.pictures_name(text)
        if type == 0 and sid:
            return await self.goujian(sid,0)
        elif type == 1 and sid:
            return await self.goujian(sid,1)
        elif type == 2 and name:
            return await self.goujian(name,2)
        else:
            return [
                Comp.Plain("消息构建错误")
            ]

class Account_System:
    def __init__(self):
        self.cookies_q = {}
        self.dir_path = plugin_config.DATA_DIR
        self.account = None
        self.passwd = None
        self.token = None

    async def read_config(self, config: AstrBotConfig):
        self.account = config.get("account", None)
        self.passwd = config.get("password", None)
        return {"account": self.account, "password": self.passwd}

    async def read_token(self):
        """从插件数据路径加载token"""
        dir = str(self.dir_path) + "/resources/syj_config/token"
        if os.path.isfile(dir):
            with open(dir, encoding="utf_8") as r:
                y = r.read().strip()
                self.token = y
                logger.warning(f"自动加载key成功:{y}")

    async def w_token(self, token):
        """更新令牌函数"""
        dir = str(self.dir_path) + "/resources/syj_config/token"
        with open(dir, "w", encoding="utf_8") as w:
            self.token = f"{token}"
            w.write(token)
            w.close

    async def check_image(self, img_path):
        """获取兽云祭图片验证码"""
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                check = await client.get(url=CHECK, cookies=self.cookies_q)
                try:
                    image = check.content
                    key = check.cookies["PHPSESSID"]
                    self.cookies_q["PHPSESSID"] = key
                except KeyError:
                    logger.info("二次获取图片验证码,将不写入cookie")
                    key = None
            with open(img_path, "wb") as file:
                file.write(image)
            return True
        except Exception as e:
            logger.error(f"图片验证码获取失败: {str(e)}")
            return False

    async def login_auto(self):
        """自动登录函数"""
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                a = await client.post(
                    url=LOGIN,
                    cookies=self.cookies_q,
                    data={
                        "account": self.account,
                        "password": self.passwd,
                        "model": 1,
                        "token": self.token
                    })
                data = a.json()
                if data["code"] == "10000":
                    cookie = a.cookies
                    logger.info(f"兽云祭账户{self.account}登录成功,正在更新cookie")
                    self.cookies_q = {
                        "Token": cookie["Token"],
                        "PHPSESSID": cookie["PHPSESSID"],
                        "User": cookie["User"]
                    }
                    return "登录成功"
                elif data["code"] == "10020":
                    logger.info("兽云祭账户重复登录")
                    return "客户端已登录"
                else:
                    logger.error(f"登录失败！！！\n{data['msg']}")
                    return False
        except Exception as e:
            logger.error(f"登录请求发送失败: {e}")
            return False

    async def login(self, key: str) -> str:
        async with httpx.AsyncClient(timeout=None) as client:
            login_data = await client.post(
                url=LOGIN,
                cookies=self.cookies_q, data={
                    "account": self.account,
                    "password": self.passwd,
                    "model":0,
                    "proving": key
                })
            if login_data.status_code == 200:
                data = login_data.json()
                cookie = login_data.cookies
                if data["code"] == "10000":
                    logger.info(f"兽云祭账户{self.account}登录成功,正在更新cookie")
                    self.cookies_q = {
                        "Token": cookie["Token"],
                        "PHPSESSID": cookie["PHPSESSID"],
                        "User": cookie["User"]
                    }
                    return "登录成功"
                else:
                    self.cookies_q = {}
                    logger.error(f"兽云祭登录失败\n响应码:{data['code']}\n状态:{data['msg']}")
                    return f"响应码:{data['code']}\n状态:{data['msg']}"
            else:
                logger.error(f"兽云祭登录API请求失败\nHTTP响应码:{login_data.status_code}")
                return "请求失败"

    async def login_token(self, id: int):
        """登录令牌获取函数"""
        url = TKAPPLY if id == 1 else TKQUERY
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                u = await client.get(url,cookies=self.cookies_q)
                data = u.json()
                if data["code"] == "12000":
                    logger.info("唯一登录令牌重新获取")
                    return data["token"]
                elif data["code"] == "12100":
                    logger.info("唯一登录令牌读取成功")
                    return data["token"]
                elif data["code"] == "11101":
                    logger.info("cookie丢失")
                    return False
                else:
                    logger.error(f"唯一登录令牌获取失败！！！{data['msg']}")
                    return False
        except Exception as e:
            logger.error(f"获取令牌失败！！{e}")
            return False

syj = fox()
"""兽云祭基础实现"""

account_system = Account_System()
"""账户管理系统实现"""
