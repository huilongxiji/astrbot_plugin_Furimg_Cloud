
from pathlib import Path

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


class Fox:
    def __init__(self):
        self.random = SYJ_RANDOM
        self.random_name = SYJ_RANDOM_NAME
        self.pictures_url = PICTURES_URL

    async def random_data(self, type: str = "", name = ""):
        """随机兽图数据获取实现
        type: 0.设定 1.毛图 2.插画 留空则随机"""
        try:
            async with httpx.AsyncClient(timeout=account_system.api_timeout) as client:
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
            async with httpx.AsyncClient(timeout=account_system.api_timeout) as client:
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
            async with httpx.AsyncClient(timeout=account_system.api_timeout) as client:
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
        if type == 0:
            data = await self.pictures_sid(text)
            return await self.goujian(data, 0)
        elif type == 1:
            data = await self.pictures_sid(text)
            return await self.goujian(data, 1)
        elif type == 2:
            data = await self.pictures_name(text)
            return await self.goujian(data, 2)
        else:
            return [Comp.Plain("无效的搜索类型")]

class Account_System:
    def __init__(self):
        self.cookies_q = {}
        self.dir_path: Path | None = plugin_config.DATA_DIR
        self.account = None
        self.passwd = None
        self.token = None
        self.api_timeout = 30.0  # 默认超时时间

    async def read_config(self, config: AstrBotConfig):
        self.account = config.get("account", None)
        self.passwd = config.get("password", None)

        # 读取 API 超时配置，若不是合法数字则使用默认值
        timeout_config = config.get("api_timeout", 30.0)
        try:
            timeout_value = float(timeout_config)
            # 确保超时时间为正数
            if timeout_value > 0:
                self.api_timeout = timeout_value
                logger.info(f"API超时时间设置为: {self.api_timeout}秒")
            else:
                logger.warning(f"API超时时间配置无效（{timeout_config}），必须为正数，使用默认值: 30.0秒")
                self.api_timeout = 30.0
        except (ValueError, TypeError):
            logger.warning(f"API超时时间配置无效（{timeout_config}），使用默认值: 30.0秒")
            self.api_timeout = 30.0

        return {"account": self.account, "password": self.passwd, "api_timeout": self.api_timeout}

    async def read_token(self):
        """从插件数据路径加载token"""
        if self.dir_path is None:
            logger.warning("数据目录未初始化，无法读取token")
            return

        # 类型窄化：此时 self.dir_path 确定不是 None
        assert self.dir_path is not None
        token_file = self.dir_path / "resources" / "syj_config" / "token"
        if token_file.is_file():
            with open(token_file, encoding="utf_8") as r:
                y = r.read().strip()
                self.token = y
                logger.warning(f"自动加载key成功:{y}")

    async def w_token(self, token):
        """更新令牌函数"""
        if self.dir_path is None:
            logger.warning("数据目录未初始化，无法写入token")
            return

        # 类型窄化：此时 self.dir_path 确定不是 None
        assert self.dir_path is not None
        token_file = self.dir_path / "resources" / "syj_config" / "token"
        with open(token_file, "w", encoding="utf_8") as w:
            self.token = f"{token}"
            w.write(token)

    async def check_image(self, img_path):
        """获取兽云祭图片验证码"""
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                check = await client.get(url=CHECK, cookies=self.cookies_q)
                try:
                    image = check.content
                    key = check.cookies["PHPSESSID"]
                    self.cookies_q["PHPSESSID"] = key
                except KeyError:
                    logger.warning("二次获取图片验证码,将不写入cookie")
                    key = None
            with open(img_path, "wb") as file:
                file.write(image)
            return True
        except Exception as e:
            logger.error(f"图片验证码获取失败: {str(e)}")
            return False

    async def login_auto(self):
        """自动登录函数"""
        # 检查账号密码是否已配置
        if not self.account or not self.passwd:
            logger.warning("账号或密码未配置，无法进行自动登录")
            return False

        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                a = await client.post(
                    url=LOGIN,
                    cookies=self.cookies_q,
                    data={
                        "account": self.account,
                        "password": self.passwd,
                        "model": 1,
                        "token": self.token
                    })
        except TimeoutError:
            logger.error("登录API访问超时")
            return False
        except Exception as e:
            logger.error(f"登录请求发送失败: {e}")
            return False
        else:
            if a.status_code == 200:
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
                    logger.warning(f"自动登录失败！！！\n{data['msg']}")
                    return False
            else:
                logger.warning(f"自动登录请求异常， http 状态码: {a.status_code}")
                return False

    async def login(self, key: str) -> str:
        # 检查账号密码是否已配置
        if not self.account or not self.passwd:
            logger.warning("账号或密码未配置，无法进行登录")
            return "账号或密码未配置，请在配置文件中填写"

        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                login_data = await client.post(
                    url=LOGIN,
                    cookies=self.cookies_q, data={
                        "account": self.account,
                        "password": self.passwd,
                        "model":0,
                        "proving": key
                    })
        except TimeoutError:
            logger.error("登录API访问超时")
            return "登录API访问超时"
        except Exception as e:
            logger.error(f"登录请求发送失败: {e}")
            return f"登录请求发送失败: {e}"
        else:
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
                    logger.warning(f"兽云祭登录失败\n响应码:{data['code']}\n状态:{data['msg']}")
                    return f"响应码:{data['code']}\n状态:{data['msg']}"
            else:
                logger.warning(f"兽云祭登录API请求失败\nHTTP响应码:{login_data.status_code}")
                return "登录请求发送失败"

    async def login_token(self, id: int):
        """登录令牌获取函数"""
        url = TKAPPLY if id == 1 else TKQUERY
        try:
            async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                token_data = await client.get(url, cookies=self.cookies_q)
        except Exception as e:
            logger.error(f"获取令牌失败！！{e}")
            return False
        else:
            if token_data.status_code == 200:
                data = token_data.json()
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
                    logger.warning(f"唯一登录令牌获取失败！！！{data['msg']}")
                    return False
            else:
                logger.warning(f"兽云祭唯一登录令牌请求失败\nHTTP响应码:{token_data.status_code}")
                return False

syj = Fox()
"""兽云祭基础实现"""

account_system = Account_System()
"""账户管理系统实现"""
