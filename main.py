import re
from pathlib import Path

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, StarTools, register
from astrbot.core import AstrBotConfig
from astrbot.core.utils.session_waiter import (
    SessionController,
    session_waiter,
)

from . import config as plugin_config
from .fox import account_system, syj


@register(
    "astrbot_plugin_Furimg_Cloud",
    "huilongxiji",
    "兽云祭对接插件插件",
    "1.0.1"
)
class FoxPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):   # , config: AstrBotConfig
        super().__init__(context)
        self.config = config

        logger.info("正在初始化兽云祭插件...")

        # 设置数据目录为AstrBot官方推荐的数据存储路径
        # 通过StarTools获取官方数据存储路径
        try:
            data_dir = StarTools.get_data_dir(plugin_config.PLUGIN_NAME)
            logger.info(f"兽云祭插件数据目录: {data_dir}")

            # 修改常量模块中的DATA_DIR
            plugin_config.DATA_DIR = data_dir

            # 确保目录存在
            data_dir.mkdir(parents=True, exist_ok=True)

            # 确保资源目录存在并初始化资源文件
            self._ensure_resource_files(data_dir)
        except Exception as e:
            logger.error(f"设置数据目录失败: {e}")
            # 创建临时目录作为备用
            fallback_dir = Path(__file__).parent / "temp_data"
            fallback_dir.mkdir(exist_ok=True)
            plugin_config.DATA_DIR = fallback_dir
            logger.warning(f"使用临时目录作为备用: {fallback_dir}")

            # 同样为临时目录准备资源文件
            self._ensure_resource_files(fallback_dir)

    def _ensure_resource_files(self, data_dir: Path) -> None:
        """
        确保数据目录存在必要的资源文件夹和子目录。

        Args:
            data_dir: 数据目录路径
        """
        try:
            # 创建必要的子目录
            resources_dir = data_dir / "resources"
            resources_dir.mkdir(exist_ok=True)

            # 创建账户信息储存目录
            config_dir = resources_dir / "syj_config"
            config_dir.mkdir(exist_ok=True)

            # 创建用于存放投稿数据的目录
            upload_dir = resources_dir / "upload"
            upload_dir.mkdir(exist_ok=True)

            # 创建用于存放投稿图片的目录 (upload)
            images_dir = upload_dir / "images"
            images_dir.mkdir(exist_ok=True)

            # 创建投稿数据的目录
            user_data_dir = upload_dir / "user_data"
            user_data_dir.mkdir(exist_ok=True)

            # 创建调试目录
            debug_dir = data_dir / "debug"
            debug_dir.mkdir(exist_ok=True)

        except Exception as e:
            logger.error(f"准备资源文件时出错: {e}")
            import traceback

            logger.error(f"错误详情: {traceback.format_exc()}")

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        await account_system.read_token()     # 自动加载token
        await account_system.read_config(config=self.config)    # 载入账户信息
        if self.config.get("auto_login", False):
            zd = await account_system.login_auto()
            if zd:
                logger.info("兽云祭账户自动登录成功")
            else:
                logger.error(f"读取到全局变量为：{account_system.cookies_q}")
                logger.error(f"读取到唯一登录令牌为：{account_system.token}")

    @filter.command("随机兽图")
    async def fox_randox_furry(self, event: AstrMessageEvent):
        """这个指令是随机获取兽图的指令"""
        logger.info("<兽云祭系统>[随机兽图:-->随机查询]: ")
        code, msg, json = await syj.random_data()
        if code:
            sid = str(json["picture"]["id"])
            data = await syj.API_Data(sid,0)
        else:
            data: list = [
                Comp.Plain(msg)
            ]
        yield event.chain_result(data)

    @filter.command("来只")
    async def fox_laizhi(self, event: AstrMessageEvent):
        """这个是来仅根据sid或者图片名称来获取图片的指令"""
        logger.error("来只触发")
        message_str = event.message_str
        if message_str == "来只":
            yield event.plain_result(
                """<缺少参数>
                请携带参数使用哦
                例如:
                /{} 123  或  /{} 名称
                “{}”后面的sid或者名称需要用空格隔开
                **空格此只能携带一个参数哦"""
                .format("来只", "来只", "来只")
                .replace(" ", "")
                .replace("\t", "")
            )
            return
        pattern = r"^来只\s*(.*)$"     # rf"^来只\s*(.*?)(?:\s|$)"
        match = re.search(pattern, message_str)
        text = (match.group(1) if match else "")
        if text.isdigit():
            logger.info(f"<兽云祭系统>[来只:-->SID精确查询]: {text}")
            data = await syj.API_Data(text=text, type=1)
        else:
            logger.info(f"<兽云祭系统>[来只:-->名称模糊查询]: {text}")
            data = await syj.API_Data(text=text, type=2)
        yield event.chain_result(data)

    @filter.command("来只毛")
    async def fox_laizhimao(self, event: AstrMessageEvent):
        """这个指令是根据名称查询毛毛图片，不携带名称则为随机获取"""
        message_str = event.message_str
        _type = "1"

        if message_str == "来只毛":
            logger.info("<兽云祭系统>[来只毛:-->随机查询]: ")
            code, msg, json = await syj.random_data(type=_type)
        else:
            pattern = r"^来只毛\s*(.*)$"
            match = re.search(pattern, message_str)
            text = (match.group(1) if match else "")
            logger.info(f"<兽云祭系统>[来只毛:-->毛图名称模糊查询]: {text}")
            code, msg, json = await syj.random_data(type=_type, name=text)

        data: list = [
            Comp.Plain(msg)
        ]

        if code:
            sid = str(json["picture"]["id"])
            data = await syj.API_Data(sid,0)

        yield event.chain_result(data)

    @filter.command("来只兽")
    async def fox_laizhishou(self, event: AstrMessageEvent):
        """这个指令是根据名称查询兽兽图片，不携带名称则为随机获取"""
        message_str = event.message_str
        _type = "2"

        if message_str == "来只兽":
            logger.info("<兽云祭系统>[来只兽:-->随机查询]: ")
            code, msg, json = await syj.random_data(type=_type)
        else:
            pattern = r"^来只兽\s*(.*)$"
            match = re.search(pattern, message_str)
            text = (match.group(1) if match else "")
            logger.info(f"<兽云祭系统>[来只兽:-->插画名称模糊查询]: {text}")
            code, msg, json = await syj.random_data(type=_type, name=text)

        data: list = [
            Comp.Plain(msg)
        ]

        if code:
            sid = str(json["picture"]["id"])
            data = await syj.API_Data(sid,0)

        yield event.chain_result(data)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("兽云验证码")
    async def fox_chack_image(self, event: AstrMessageEvent):
        """获取一张验证码图片"""
        chack_dir = str(plugin_config.DATA_DIR) + "/resources/验证码.jpg"
        await account_system.check_image(img_path=str(chack_dir))
        yield event.image_result(str(chack_dir))

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("兽云登录")
    async def fox_login(self, event: AstrMessageEvent):
        """兽云祭账户登录功能，流程式问答结构"""
        try:
            chack_dir = str(plugin_config.DATA_DIR) + "/resources/验证码.jpg"
            yield event.plain_result("开始登录流程Loding~~~")

            @session_waiter(timeout=60, record_history_chains=False)
            async def empty_mention_waiter(controller: SessionController, event: AstrMessageEvent):
                user_msg = event.message_str

                if user_msg == "退出":   # 假设用户想主动退出，输入了 "退出"
                    await event.send(event.plain_result("已退出登录流程"))
                    controller.stop()    # 停止会话控制器，会立即结束。
                    return

                if (login_msg := await account_system.login(str(user_msg))) == "登录成功":
                    await event.send(event.plain_result("登录完成"))
                    if token := await account_system.login_token(1):
                        logger.info(f"令牌自动更新成功，新令牌为：{token}")
                        await event.send(event.plain_result("令牌自动更新成功"))
                    else:
                        await event.send(event.plain_result("令牌更新失败，请检查控制台输出，下次也将无法自动登录"))
                    controller.stop()    # 停止会话控制器，会立即结束。
                    return

                if login_msg != "登录成功":
                    await account_system.check_image(img_path=str(chack_dir))
                    await event.send(event.plain_result(str(login_msg)))
                    await event.send(event.image_result(str(chack_dir)))  # 发送回复，不能使用 yield
                    return

                controller.keep(timeout=60, reset_timeout=True) # 重置超时时间为 60s，如果不重置，则会继续之前的超时时间计时。

            try:
                zd = await account_system.login_auto()
                if zd:
                    yield event.plain_result(zd)
                else:
                    yield event.plain_result("自动登录失败，请发送下列验证码\n如需退出请输入“退出”")
                    await account_system.check_image(img_path=str(chack_dir))
                    yield event.image_result(str(chack_dir))
                    await empty_mention_waiter(event)
            except TimeoutError as _: # 当超时后，会话控制器会抛出 TimeoutError
                yield event.plain_result("等待时间超过60秒，自动结束进程！")
            except Exception as e:
                yield event.plain_result("发生错误，请联系管理员: " + str(e))
            finally:
                event.stop_event()
        except Exception as e:
            logger.error("登录流程出错: " + str(e))

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("兽云更新登录令牌")
    async def fox_updata_token(self, event: AstrMessageEvent):
        """兽云祭登录令牌更新指令"""
        token = await account_system.login_token(1)
        if token:
            await account_system.w_token(token)
            yield event.plain_result("令牌更新完成")
        else:
            yield event.plain_result("令牌更新失败，请检查控制台输出")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        pass
