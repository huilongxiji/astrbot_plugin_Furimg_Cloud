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
from .fox import account_system, syj, image_upload


@register(
    "astrbot_plugin_Furimg_Cloud",
    "huilongxiji",
    "兽云祭对接插件插件",
    "1.2.0"
)
class FoxPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
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
        await account_system.read_token()  # 自动加载token
        await account_system.read_config(config=self.config)  # 载入账户信息

        if self.config.get("auto_login", False):
            # 检查账号密码是否已配置
            if not account_system.account or not account_system.passwd:
                logger.warning("未配置兽云祭账号或密码，跳过自动登录")
                logger.warning("请在插件配置文件中填写 account 和 password 参数")
                return

            zd = await account_system.login_auto()
            if zd:
                logger.info("兽云祭账户自动登录成功")
            else:
                logger.error(f"读取到全局变量为：{account_system.cookies_q}")
                logger.error(f"读取到唯一登录令牌为：{account_system.token}")

    @filter.command("随机兽图")
    async def fox_random_furry(self, event: AstrMessageEvent):
        """这个指令是随机获取兽图的指令"""
        logger.info("<兽云祭系统>[随机兽图:-->随机查询]: ")
        code, msg, json = await syj.random_data()
        if code:
            sid = str(json["picture"]["id"])
            data = await syj.API_Data(sid, 0)
        else:
            data: list = [
                Comp.Plain(msg)
            ]
        yield event.chain_result(data)

    @filter.command("来只")
    async def fox_laizhi(self, event: AstrMessageEvent):
        """这个是来仅根据sid或者图片名称来获取图片的指令"""
        message_str = event.message_str
        if message_str == "来只":
            yield event.plain_result(
                "<缺少参数>\n"
                "请携带参数使用哦\n"
                "例如:\n"
                "/来只 123  或  /来只 名称\n"
                "“来只”后面的sid或者名称需要用空格隔开\n"
                "**空格此只能携带一个参数哦"
            )
            return
        pattern = r"^来只\s*(.*)$"  # rf"^来只\s*(.*?)(?:\s|$)"
        match = re.search(pattern, message_str)
        text = match.group(1) if match else ""
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
            text = match.group(1) if match else ""
            logger.info(f"<兽云祭系统>[来只毛:-->毛图名称模糊查询]: {text}")
            code, msg, json = await syj.random_data(type=_type, name=text)

        data: list = [
            Comp.Plain(msg)
        ]

        if code:
            sid = str(json["picture"]["id"])
            data = await syj.API_Data(sid, 0)

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
            text = match.group(1) if match else ""
            logger.info(f"<兽云祭系统>[来只兽:-->插画名称模糊查询]: {text}")
            code, msg, json = await syj.random_data(type=_type, name=text)

        data: list = [
            Comp.Plain(msg)
        ]

        if code:
            sid = str(json["picture"]["id"])
            data = await syj.API_Data(sid, 0)

        yield event.chain_result(data)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("兽云验证码")
    async def fox_chack_image(self, event: AstrMessageEvent):
        """获取一张验证码图片"""
        if plugin_config.DATA_DIR is None:
            yield event.plain_result("数据目录未初始化，无法获取验证码")
            return

        assert plugin_config.DATA_DIR is not None
        check_path = plugin_config.DATA_DIR / "resources" / "验证码.jpg"
        await account_system.check_image(img_path=str(check_path))
        yield event.image_result(str(check_path))

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("兽云注册")
    async def fox_zhuce(self, event: AstrMessageEvent):
        """用来注册兽云祭账号"""
        try:
            if plugin_config.DATA_DIR is None:
                yield event.plain_result("数据目录未初始化，无法进行登录")
                return

            # 检查账号密码是否已配置
            if (
                not account_system.account
                or not account_system.passwd
                or not account_system.mailbox
            ):
                yield event.plain_result(
                    "未配置兽云祭账号或密码或邮箱！\n"
                    "请在插件配置文件中填写以下信息：\n"
                    "- account: 兽云祭账户\n"
                    "- password: 兽云祭账户密码\n"
                    "- mailbox: 你自己的邮箱"
                )
                return

            assert plugin_config.DATA_DIR is not None
            yield event.plain_result("准备注册流程ing")
            chack_dir = str(plugin_config.DATA_DIR) + "/resources/验证码.jpg"

            @session_waiter(timeout=60, record_history_chains=False)
            async def empty_mention_waiter(
                controller: SessionController,
                event: AstrMessageEvent
            ):
                user_msg = event.message_str

                if user_msg == "退出":  # 假设用户想主动退出，输入了 "退出"
                    await event.send(event.plain_result("已退出注册流程"))
                    controller.stop()  # 停止会话控制器，会立即结束。
                    return

                if (
                    register_msg := await account_system.register(str(user_msg))
                ) == "注册成功":
                    await event.send(
                        event.plain_result("注册成功\n请使用“兽云登录”指令来装载账号吧")
                    )
                    controller.stop()  # 停止会话控制器，会立即结束。
                    return

                if register_msg != "注册成功":
                    await account_system.check_image(img_path=str(chack_dir))
                    await event.send(event.plain_result(str(register_msg)))
                    await event.send(event.image_result(str(chack_dir)))
                    return

                controller.keep(
                    timeout=60, reset_timeout=True
                )  # 重置超时时间为 60s，如果不重置，则会继续之前的超时时间计时。

            try:
                yield event.plain_result("请发送下列验证码\n如需退出请输入“退出”")
                await account_system.check_image(img_path=str(chack_dir))
                yield event.image_result(str(chack_dir))
                await empty_mention_waiter(event)
            except TimeoutError as _:  # 当超时后，会话控制器会抛出 TimeoutError
                yield event.plain_result("等待时间超过60秒，自动结束进程！")
            except Exception as e:
                yield event.plain_result("发生错误，请联系管理员: " + str(e))
            finally:
                event.stop_event()
        except Exception as e:
            logger.error("注册流程异常: " + str(e))

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("兽云登录")
    async def fox_login(self, event: AstrMessageEvent):
        """兽云祭账户登录功能，流程式问答结构"""
        try:
            if plugin_config.DATA_DIR is None:
                yield event.plain_result("数据目录未初始化，无法进行登录")
                return

            # 检查账号密码是否已配置
            if not account_system.account or not account_system.passwd:
                yield event.plain_result(
                    "未配置兽云祭账号或密码！\n"
                    "请在插件配置文件中填写以下信息：\n"
                    "- account: 兽云祭账户\n"
                    "- password: 兽云祭账户密码"
                )
                return

            assert plugin_config.DATA_DIR is not None
            check_path = plugin_config.DATA_DIR / "resources" / "验证码.jpg"
            yield event.plain_result("开始登录流程Loding~~~")

            @session_waiter(timeout=60, record_history_chains=False)
            async def empty_mention_waiter(
                controller: SessionController,
                event: AstrMessageEvent
            ):
                user_msg = event.message_str

                if user_msg == "退出":  # 假设用户想主动退出，输入了 "退出"
                    await event.send(event.plain_result("已退出登录流程"))
                    controller.stop()  # 停止会话控制器，会立即结束。
                    return

                if (
                    login_msg := await account_system.login(str(user_msg))
                ) == "登录成功":
                    await event.send(event.plain_result("登录完成"))
                    if token := await account_system.login_token(1):
                        logger.info(f"令牌自动更新成功，新令牌为：{token}")
                        await event.send(event.plain_result("令牌自动更新成功"))
                    else:
                        await event.send(
                            event.plain_result(
                                "令牌更新失败，请检查控制台输出，下次也将无法自动登录"
                            )
                        )
                    controller.stop()  # 停止会话控制器，会立即结束。
                    return

                if login_msg != "登录成功":
                    await account_system.check_image(img_path=str(check_path))
                    await event.send(event.plain_result(str(login_msg)))
                    await event.send(
                        event.image_result(str(check_path))
                    )  # 发送回复，不能使用 yield
                    return

                controller.keep(
                    timeout=60, reset_timeout=True
                )  # 重置超时时间为 60s，如果不重置，则会继续之前的超时时间计时。

            try:
                zd = await account_system.login_auto()
                if zd:
                    yield event.plain_result(zd)
                else:
                    yield event.plain_result(
                        "自动登录失败，请发送下列验证码\n如需退出请输入退出二字"
                    )
                    await account_system.check_image(img_path=str(check_path))
                    yield event.image_result(str(check_path))
                    await empty_mention_waiter(event)
            except TimeoutError as _:  # 当超时后，会话控制器会抛出 TimeoutError
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
            status = await account_system.w_token(token)
            if status:
                yield event.plain_result("令牌更新完成")
            else:
                yield event.plain_result("缓存路径加载失败，请重启")
        else:
            yield event.plain_result("令牌更新失败，请检查控制台输出")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("兽云上传")
    async def fox_upload_image(self, event: AstrMessageEvent):
        """兽云祭图片上传"""
        try:
            if plugin_config.DATA_DIR is None:
                logger.warning("兽云祭数据目录未初始化，无法进行上传记录")
                yield event.plain_result("数据目录未初始化，无法进行上传记录")
                return

            # 检查账号密码是否已配置
            if not account_system.account or not account_system.passwd:
                yield event.plain_result(
                    "未配置兽云祭账号或密码！\n"
                    "请在插件配置文件中填写以下信息：\n"
                    "- account: 兽云祭账户\n"
                    "- password: 兽云祭账户密码"
                )
                return

            # 检查账户登录状态
            ckq = account_system.cookies_q
            if ckq == {}:
                logger.warning("触发上传时未检测到登录状态")
                yield event.plain_result("未检测到登录状态")
                return

            yield event.plain_result(
                "开始投稿流程，可随时发送「退出」结束问答。"
            )

            fox_upload_data: dict[str, str | None] = {
                "name": None,
                "type": None,
                "suggest": None,
                "path": None,
            }
            current_step = [0]
            retry_count = [0]
            awaiting_confirm = [False]
            max_retries = 3
            sess_timeout = 120

            type_labels = ["设定图", "毛图", "插画"]

            async def send_preview_and_ask_confirm(
                controller: SessionController,
                ev: AstrMessageEvent,
                data: dict[str, str | None],
            ) -> None:
                """整理最终上传决策"""
                t_label = type_labels[int(data["type"] or "0")]
                raw_suggest = data.get("suggest")
                if raw_suggest is None:
                    suggest_display = "未知"
                elif str(raw_suggest).strip() == "":
                    suggest_display = "无"
                else:
                    suggest_display = str(raw_suggest).strip()
                path_display = data.get("path") or ""

                await ev.send(
                    ev.chain_result(
                        [
                            Comp.Plain("采集完成，请确认以下内容：\n"),
                            Comp.Plain(f"投稿类型: {t_label}\n"),
                            Comp.Plain(f"设定名称: {data.get('name') or ''}\n"),
                            Comp.Plain(f"留言: {suggest_display}\n"),
                            Comp.Image.fromFileSystem(f"{path_display}"),
                        ]
                    )
                )
                await ev.send(
                    ev.plain_result(
                        "请回复「确认」开始上传，或回复「取消」放弃本次投稿。"
                    )
                )
                controller.keep(timeout=sess_timeout, reset_timeout=True)

            async def do_upload_and_stop(
                controller: SessionController,
                ev: AstrMessageEvent,
                data: dict[str, str | None],
            ) -> None:
                """提交上传并返回状态"""
                status = await image_upload.save(data=data)
                if status:
                    await ev.send(ev.plain_result("上传成功，感谢投稿！"))
                else:
                    await ev.send(ev.plain_result("数据保存异常，请联系管理员"))
                controller.stop()

            # questions = [
            #     {
            #         "key": "type",  # 本步通过后写入 fox_upload_data[key]
            #         "prompt": "（发给用户的题干，str）",
            #         "kind": "text",  # 文本类：读 event.message_str 为 raw → validator(raw) → 再 normalize(raw) 得到落库字符串
            #         "validator": "<callable，入参 str，原始输入是否合法>",
            #         "normalize": "<callable，入参 str，落库用；本插件 text 步均有>",
            #         "conditional": null  # Python 中为 None：必问；若填函数 (fox_upload_data)->bool 且返回 false，则整题跳过不问
            #     },
            #     {
            #         "key": "path",
            #         "prompt": "（发给用户的题干，str）",
            #         "kind": "image",  # 图片类：从消息链取首张 Comp.Image 转本地 path；validator(path|null)；不写 normalize（null）
            #         "validator": "<callable，入参 path 或 None（解析失败），是否视为合法>",
            #         "normalize": null,
            #         "conditional": null
            #     }
            # ]

            questions = [
                {
                    "key": "type",
                    "prompt": (
                        "请输入投稿类型：\n"
                        "[0: 设定图 / 1: 毛图 / 2: 插画]\n"
                        "（请发送纯数字 0、1 或 2）"
                    ),
                    "kind": "text",
                    "validator": lambda x: x.strip() in {"0", "1", "2"},
                    "normalize": lambda x: x.strip(),
                    "conditional": None,
                },
                {
                    "key": "name",
                    "prompt": "请输入设定名称：（纯文字）",
                    "kind": "text",
                    "validator": lambda x: x.strip() != "",
                    "normalize": lambda x: x.strip(),
                    "conditional": None,
                },
                {
                    "key": "suggest",
                    "prompt": (
                        "是否需要留言？\n"
                        "不需要请回复「无」；"
                        "若需要请直接发送留言全文（纯文字）。"
                    ),
                    "kind": "text",
                    "validator": lambda x: x.strip() != "",
                    "normalize": lambda x: "" if x.strip() == "无" else x.strip(),
                    "conditional": None,
                },
                {
                    "key": "path",
                    "prompt": "请仅发送一张要投稿的图片（不要附带多余文字）：",
                    "kind": "image",
                    "validator": lambda img_path: img_path is not None,
                    "normalize": None,
                    "conditional": None,
                },
            ]

            async def prompt_next_question(
                controller: SessionController,
                ev: AstrMessageEvent,
                next_index: int,
            ) -> bool:
                """循环发送提示"""
                while next_index < len(questions):
                    q_meta = questions[next_index]
                    if q_meta["conditional"] and not q_meta["conditional"](
                        fox_upload_data
                    ):
                        key = q_meta["key"]
                        fox_upload_data[key] = None
                        next_index += 1
                        current_step[0] = next_index
                        retry_count[0] = 0
                        continue
                    current_step[0] = next_index
                    retry_count[0] = 0
                    await ev.send(ev.plain_result(q_meta["prompt"]))
                    controller.keep(timeout=sess_timeout, reset_timeout=True)
                    return False
                current_step[0] = next_index
                awaiting_confirm[0] = True
                retry_count[0] = 0
                await send_preview_and_ask_confirm(controller, ev, fox_upload_data)
                return True

            @session_waiter(timeout=sess_timeout, record_history_chains=False)
            async def upload_waiter(
                controller: SessionController,
                event: AstrMessageEvent
            ):
                user_msg = event.message_str or ""
                message_chain = event.get_messages()

                if user_msg.strip() == "退出":
                    await event.send(event.plain_result("已退出上传流程"))
                    controller.stop()
                    return

                if awaiting_confirm[0]:
                    text = user_msg.strip()
                    if text == "确认":
                        await do_upload_and_stop(controller, event, fox_upload_data)
                        return
                    if text == "取消":
                        await event.send(event.plain_result("已取消本次上传。"))
                        controller.stop()
                        return
                    retry_count[0] += 1
                    if retry_count[0] >= max_retries:
                        await event.send(
                            event.plain_result(
                                f"已连续错误超过 {max_retries} 次，已退出上传流程。"
                            )
                        )
                        controller.stop()
                        return
                    left = max_retries - retry_count[0]
                    await event.send(
                        event.plain_result(
                            f"请回复「确认」或「取消」，还剩 {left} 次机会。"
                        )
                    )
                    controller.keep(timeout=sess_timeout, reset_timeout=True)
                    return

                if current_step[0] >= len(questions):
                    await event.send(event.plain_result("上传流程已结束"))
                    controller.stop()
                    return

                q_meta = questions[current_step[0]]

                value: str | None = None
                valid = False
                if q_meta["kind"] == "text":
                    raw_text = user_msg
                    normalize = q_meta.get("normalize")
                    if callable(normalize):
                        value_candidate = normalize(raw_text)
                    else:
                        value_candidate = raw_text
                    valid = bool(q_meta["validator"](raw_text))
                    if valid:
                        value = (
                            value_candidate
                            if isinstance(value_candidate, str)
                            else str(value_candidate)
                        )
                else:
                    for comp in message_chain:
                        if isinstance(comp, Comp.Image):
                            try:
                                value = await comp.convert_to_file_path()
                            except Exception as ex:
                                logger.warning(f"图片解析失败: {ex}")
                                value = None
                            break
                    valid = bool(q_meta["validator"](value))
                    extraneous_plain = False
                    for comp in message_chain:
                        if isinstance(comp, Comp.Plain) and (comp.text or "").strip():
                            extraneous_plain = True
                            break
                    if extraneous_plain and valid:
                        valid = False
                        value = None

                if not valid:
                    retry_count[0] += 1
                    if retry_count[0] >= max_retries:
                        await event.send(
                            event.plain_result(
                                f"已连续错误超过 {max_retries} 次，已退出上传流程。"
                            )
                        )
                        controller.stop()
                        return
                    left = max_retries - retry_count[0]
                    hint = (
                        "请按提示发送纯文本"
                        if q_meta["kind"] == "text"
                        else "请仅发送一张图片（不要附带文字）"
                    )
                    await event.send(
                        event.plain_result(f"{hint}，还剩 {left} 次机会。")
                    )
                    controller.keep(timeout=sess_timeout, reset_timeout=True)
                    return

                key = q_meta["key"]
                fox_upload_data[key] = value
                next_idx = current_step[0] + 1

                if await prompt_next_question(controller, event, next_idx):
                    return

            try:
                yield event.plain_result(questions[0]["prompt"])
                await upload_waiter(event)
            except TimeoutError:
                yield event.plain_result(
                    f"等待时间超过 {sess_timeout} 秒，上传流程已自动结束。"
                )
            except Exception as e:
                yield event.plain_result("发生错误，请联系管理员: " + str(e))
            finally:
                event.stop_event()
        except Exception as e:
            logger.error("图片上传功能异常: " + str(e))

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        pass
