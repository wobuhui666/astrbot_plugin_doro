import logging
import time
import traceback

import httpx
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig


@register("astrbot_plugin_doro", "shingetsu", "随机doro表情包", "0.0.2")
class MyPlugin(Star):
    # last_called_time = 0  # 上次调用时间
    # cooldown_period  # 冷却时间（秒）

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.logger = None
        self.config = config
        self.cooldown_period = config.get("cooldown_period")
        self.last_called_time = 0
    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        self.logger = logging.getLogger(__name__)

    def is_on_cooldown(self) -> tuple[bool, float]:
        """检查是否在冷却时间内

        Returns:
            tuple[bool, float]: (是否在冷却中, 剩余冷却时间)
        """
        current_time = time.time()
        elapsed_time = current_time - self.last_called_time
        remaining_time = max(0, self.cooldown_period - elapsed_time)
        return elapsed_time < self.cooldown_period, remaining_time

    @filter.command("doro")
    async def doro(self, event: AstrMessageEvent):
        """发送一个随机doro表情包"""
        on_cooldown, remaining_time = self.is_on_cooldown()
        if on_cooldown:
            yield event.plain_result(
                f"请稍等，距离下一次获取随机Doro表情包还有 {remaining_time:.0f} 秒。"
            )
            return
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://www.doro.asia/api/random-sticker")
                response.raise_for_status()
                data = response.json()
                if data.get("success", False):  # 检查 API 返回的 success 字段
                    sticker_url = data["sticker"]["url"]
                    if sticker_url:
                        yield event.image_result(sticker_url)
                    else:
                        yield event.plain_result("未获取到表情包，请稍后再试")
                else:
                    yield event.plain_result("API 返回失败")
        except httpx.HTTPStatusError as e:
            error_detail = traceback.format_exc()
            self.logger.error(f"HTTP状态错误: {e}\n{error_detail}")
            print("发生错误:", e)
            yield event.plain_result(f"API 请求失败，错误码：{e.response.status_code}")
        except httpx.RequestError as e:
            error_detail = traceback.format_exc()
            self.logger.error(f"请求错误: {e}\n{error_detail}")
            print("发生错误:", e)
            yield event.plain_result("请求失败，请检查网络或 API 是否可用")
        except Exception as e:
            error_detail = traceback.format_exc()
            self.logger.error(f"未知错误: {e}\n{error_detail}")
            print("发生错误:", e)
            yield event.plain_result("发生未知错误:", e)
        finally:
            self.last_called_time = time.time()

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
