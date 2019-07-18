import asyncio
import base64
import json
import logging
import re

from urllib.parse import parse_qs, urlparse

from ._base import BaseExtractor, JobFailedException

logger = logging.getLogger(__name__)


class AvgleExtractor(BaseExtractor):
    name = "Avgle"
    matcher = re.compile(r"^https?://(www\.)?avgle.com/video/([^/]{6,})/.*")
    priority = 10

    async def extract(self):
        state = {"count": 0}

        async def handle_response(r):
            if "//avgle.com/video-url.php?" in r.url:
                logger.debug("Got response that matches correct URL, %s" % (r.url,))
                d = json.loads(await r.text())
                state["url"] = base64.b64decode(
                    parse_qs(urlparse(d["url"]).query)["s3"][0]
                ).decode("utf-8")
                state["count"] += 1

        self.page.on("response", handle_response)

        await self.page.goto(self.job.url, waitUntil="networkidle2")

        element = await self.page.querySelector("title")
        title = (
            (await (await element.getProperty("innerHTML")).jsonValue())
            .rsplit(" - ", 1)[0]
            .strip()
        )
        id_ = self.job.url.split("/")[4]

        for _ in range(10):
            if state.get("url"):
                break
            await asyncio.sleep(1)

        found_recaptcha_count = 0
        found_recaptcha = await self.page.querySelector(
            'iframe[src*="google.com/recaptcha"]'
        )
        if found_recaptcha:
            logger.info("We need a captcha response")
            self.wait_for_user_input("Please input captcha")
            for _ in range(3200):
                if state["count"] == 2:
                    break

                if self.cancelled:
                    return

                found_recaptcha = await self.page.querySelector(
                    'iframe[src*="google.com/recaptcha"]'
                )
                if found_recaptcha:
                    found_recaptcha_count = 0
                else:
                    found_recaptcha_count += 1

                if found_recaptcha_count > 7:
                    raise JobFailedException("Recaptcha gone for too long, failing job")

                logger.debug("Is captcha still visible: %r" % (found_recaptcha,))
                await asyncio.sleep(1)
            else:
                raise JobFailedException("Failed while waiting for captcha")

        headers = {}
        if "ahcdn.com" not in state["url"]:
            headers["Referer"] = "http://avg" + "le.com"

        return {"url": state["url"], "title": title, "id": id_, "headers": headers}
