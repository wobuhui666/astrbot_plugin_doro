import logging
import time
import traceback
import asyncio

import httpx
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig


@register("astrbot_plugin_doro", "shingetsu", "随机doro表情包", "0.0.6")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.logger = None
        self.config = config
        self.cooldown_period = config.get("cooldown_period", 60)
        self.last_called_time = 0
        self.last_called_time_cheshire = 0

    async def initialize(self):
        self.logger = logging.getLogger(__name__)

    def is_on_cooldown(self) -> tuple[bool, float]:
        current_time = time.time()
        elapsed_time = current_time - self.last_called_time
        remaining_time = max(0, self.cooldown_period - elapsed_time)
        return elapsed_time < self.cooldown_period, remaining_time

    def is_on_cooldown_cheshire(self) -> tuple[bool, float]:
        current_time = time.time()
        elapsed_time = current_time - self.last_called_time_cheshire
        remaining_time = max(0, self.cooldown_period - elapsed_time)
        return elapsed_time < self.cooldown_period, remaining_time

    @filter.command("doro")
    async def doro(self, event: AstrMessageEvent):
        """发送一个随机doro表情包 (已修正以处理302重定向)"""
        on_cooldown, remaining_time = self.is_on_cooldown()
        if on_cooldown:
            yield event.plain_result(
                f"请稍等，距离下一次获取随机Doro表情包还有 {remaining_time:.0f} 秒。"
            )
            return

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 关键改动：显式创建一个允许重定向的客户端，覆盖框架的默认设置
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    response = await client.get("http://192.168.1.3:3333/random-gif")
                    response.raise_for_status()  # 现在它不会因为302而报错了

                    # 对于重定向的API, 最终的 response.url 就是我们需要的图片链接
                    sticker_url = str(response.url)

                    if sticker_url:
                        yield event.image_result(sticker_url)
                        self.last_called_time = time.time()
                        return
                    else:
                        yield event.plain_result("未获取到表情包链接，请稍后再试")
                        self.last_called_time = time.time()
                        return

            except httpx.HTTPStatusError as e:
                self.logger.warning(f"Doro - 尝试 {attempt + 1}: HTTP 状态错误: {e}")
                if attempt < max_retries - 1:
                    await self._sleep_before_retry(attempt)
                else:
                    error_detail = traceback.format_exc()
                    self.logger.error(f"Doro - HTTP状态错误: {e}\n{error_detail}")
                    yield event.plain_result(f"API 请求失败，错误码：{e.response.status_code}")
            except httpx.RequestError as e:
                self.logger.warning(f"Doro - 尝试 {attempt + 1}: 请求错误: {e}")
                if attempt < max_retries - 1:
                    await self._sleep_before_retry(attempt)
                else:
                    error_detail = traceback.format_exc()
                    self.logger.error(f"Doro - 请求错误: {e}\n{error_detail}")
                    yield event.plain_result("请求失败，请检查网络或 API 是否可用")
            except Exception as e:
                error_detail = traceback.format_exc()
                self.logger.error(f"Doro - 未知错误: {e}\n{error_detail}")
                yield event.plain_result(f"发生未知错误: {e}")
                self.last_called_time = time.time()
                return

        # 如果所有重试都失败
        self.last_called_time = time.time()

    @filter.command("cheshire")
    async def cheshire(self, event: AstrMessageEvent):
        """发送一个随机Cheshire表情包 (处理JSON响应)"""
        on_cooldown, remaining_time = self.is_on_cooldown_cheshire()
        if on_cooldown:
            yield event.plain_result(
                f"请稍等，距离下一次获取随机Cheshire表情包还有 {remaining_time:.0f} 秒。"
            )
            return

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Cheshire API 不需要强制重定向，可以使用默认客户端
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://www.cheshire.asia/api/random-sticker")
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if data.get("success", False):
                        sticker_url = data.get("sticker", {}).get("url")
                        if sticker_url:
                            yield event.image_result(sticker_url)
                            self.last_called_time_cheshire = time.time()
                            return
                        else:
                            yield event.plain_result("API成功返回但未找到Cheshire表情包链接")
                            self.last_called_time_cheshire = time.time()
                            return
                    else:
                        api_message = data.get("message", "无详细错误信息")
                        yield event.plain_result(f"Cheshire API 请求失败: {api_message}")
                        self.last_called_time_cheshire = time.time()
                        return
            except httpx.HTTPStatusError as e:
                self.logger.warning(f"Cheshire - 尝试 {attempt + 1}: HTTP 状态错误: {e}")
                if attempt < max_retries - 1:
                    await self._sleep_before_retry(attempt)
                else:
                    error_detail = traceback.format_exc()
                    self.logger.error(f"Cheshire - HTTP状态错误: {e}\n{error_detail}")
                    yield event.plain_result(f"API 请求失败，错误码：{e.response.status_code}")
                    self.last_called_time_cheshire = time.time()
                    return
            except httpx.RequestError as e:
                self.logger.warning(f"Cheshire - 尝试 {attempt + 1}: 请求错误: {e}")
                if attempt < max_retries - 1:
                    await self._sleep_before_retry(attempt)
                else:
                    error_detail = traceback.format_exc()
                    self.logger.error(f"Cheshire - 请求错误: {e}\n{error_detail}")
                    yield event.plain_result("请求失败，请检查网络或 API 是否可用")
                    self.last_called_time_cheshire = time.time()
                    return
            except Exception as e:
                error_detail = traceback.format_exc()
                self.logger.error(f"Cheshire - 未知错误: {e}\n{error_detail}")
                yield event.plain_result(f"发生未知错误(可能是API响应格式不正确): {e}")
                self.last_called_time_cheshire = time.time()
                return

        self.last_called_time_cheshire = time.time()

    async def _sleep_before_retry(self, attempt: int):
        wait_time = 2 ** attempt
        await asyncio.sleep(wait_time)

    async def terminate(self):
        pass