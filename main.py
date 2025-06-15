import logging
import time
import traceback
import asyncio  # 导入 asyncio 以使用 await asyncio.sleep

import httpx
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig


@register("astrbot_plugin_doro", "shingetsu", "随机doro表情包", "0.0.4")
class MyPlugin(Star):
    # last_called_time = 0  # 上次调用时间
    # cooldown_period  # 冷却时间（秒）

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.logger = None
        self.config = config
        self.cooldown_period = config.get("cooldown_period")  # 从配置中获取冷却时间
        self.last_called_time = 0
        self.last_called_time_cheshire = 0

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

    def is_on_cooldown_cheshire(self) -> tuple[bool, float]:
        """检查 Cheshire 命令是否在冷却时间内

        Returns:
            tuple[bool, float]: (是否在冷却中, 剩余冷却时间)
        """
        current_time = time.time()
        elapsed_time = current_time - self.last_called_time_cheshire
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

        max_retries = 3  # 最大重试次数
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://www.doro.asia/api/random-sticker")
                    response.raise_for_status()  # 对 4xx/5xx 响应抛出异常
                    data = response.json()
                    if data.get("success", False):  # 检查 API 返回的 success 字段
                        sticker_url = data["sticker"]["url"]
                        if sticker_url:
                            yield event.image_result(sticker_url)  # 发送图片结果
                            self.last_called_time = time.time()  # 更新上次调用时间
                            return  # 成功获取，退出函数
                        else:
                            yield event.plain_result("未获取到表情包，请稍后再试")
                            self.last_called_time = time.time()
                            return
                    else:
                        yield event.plain_result("Doro API request failed")  # API 返回失败
                        self.last_called_time = time.time()
                        return
            except httpx.HTTPStatusError as e:
                self.logger.warning(f"尝试 {attempt + 1}: HTTP 状态错误: {e}")
                if attempt < max_retries - 1:
                    await self._sleep_before_retry(attempt)  # 等待后重试
                else:
                    error_detail = traceback.format_exc()
                    self.logger.error(f"HTTP状态错误: {e}\n{error_detail}")
                    yield event.plain_result(f"API 请求失败，错误码：{e.response.status_code}")  # API 请求失败
            except httpx.RequestError as e:
                self.logger.warning(f"尝试 {attempt + 1}: 请求错误: {e}")
                if attempt < max_retries - 1:
                    await self._sleep_before_retry(attempt)  # 等待后重试
                else:
                    error_detail = traceback.format_exc()
                    self.logger.error(f"请求错误: {e}\n{error_detail}")
                    yield event.plain_result("请求失败，请检查网络或 API 是否可用")  # 请求失败
            except Exception as e:
                error_detail = traceback.format_exc()
                self.logger.error(f"未知错误: {e}\n{error_detail}")
                yield event.plain_result(f"发生未知错误: {e}")  # 未知错误
                self.last_called_time = time.time()
                return

        # 如果所有重试都失败
        self.last_called_time = time.time()

    @filter.command("cheshire")
    async def cheshire(self, event: AstrMessageEvent):
        """发送一个随机Cheshire表情包"""
        on_cooldown, remaining_time = self.is_on_cooldown_cheshire()
        if on_cooldown:
            yield event.plain_result(
                f"请稍等，距离下一次获取随机Cheshire表情包还有 {remaining_time:.0f} 秒。"
            )
            return

        max_retries = 3  # 最大重试次数
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://www.cheshire.asia/api/random-sticker")
                    response.raise_for_status()  # 对 4xx/5xx 响应抛出异常
                    data = response.json()
                    if data.get("success", False):  # 检查 API 返回的 success 字段
                        sticker_url = data["sticker"]["url"]
                        if sticker_url:
                            yield event.image_result(sticker_url)  # 发送图片结果
                            self.last_called_time_cheshire = time.time()  # 更新上次调用时间
                            return  # 成功获取，退出函数
                        else:
                            yield event.plain_result("未获取到Cheshire表情包，请稍后再试")
                            self.last_called_time_cheshire = time.time()
                            return
                    else:
                        yield event.plain_result("Cheshire API request failed")
                        self.last_called_time_cheshire = time.time()
                        return
            except httpx.HTTPStatusError as e:
                self.logger.warning(f"Cheshire - 尝试 {attempt + 1}: HTTP 状态错误: {e}")
                if attempt < max_retries - 1:
                    await self._sleep_before_retry(attempt)  # 等待后重试
                else:
                    error_detail = traceback.format_exc()
                    self.logger.error(f"Cheshire - HTTP状态错误: {e}\n{error_detail}")
                    yield event.plain_result(f"API 请求失败，错误码：{e.response.status_code}")
                    self.last_called_time_cheshire = time.time() # Update cooldown on final failure
                    return
            except httpx.RequestError as e:
                self.logger.warning(f"Cheshire - 尝试 {attempt + 1}: 请求错误: {e}")
                if attempt < max_retries - 1:
                    await self._sleep_before_retry(attempt)  # 等待后重试
                else:
                    error_detail = traceback.format_exc()
                    self.logger.error(f"Cheshire - 请求错误: {e}\n{error_detail}")
                    yield event.plain_result("请求失败，请检查网络或 API 是否可用")
                    self.last_called_time_cheshire = time.time() # Update cooldown on final failure
                    return
            except Exception as e:
                error_detail = traceback.format_exc()
                self.logger.error(f"Cheshire - 未知错误: {e}\n{error_detail}")
                yield event.plain_result(f"发生未知错误: {e}")
                self.last_called_time_cheshire = time.time()
                return

        # 如果所有重试都失败
        self.last_called_time_cheshire = time.time()

    async def _sleep_before_retry(self, attempt: int):
        """在重试前进行指数退避等待的辅助函数。"""
        await asyncio.sleep(2 ** attempt)  # 指数退避：1, 2, 4 秒

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""