import asyncio
import concurrent.futures
import logging
import os
import re
import socket
import subprocess
import tempfile
import time

import m3u8
import requests

from celery import shared_task
from django.conf import settings
from pyppeteer import connect, errors

from .extractors import EXTRACTORS
from .models import Job

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"


class JobNotPendingException(Exception):
    """Prevent double-handling of job exception"""


class FailedToDownloadSegmentException(Exception):
    """A piece could not be downloaded"""


def get_chrome_url():
    schema, _, hostname, path = settings.CHROME_REMOTE_URL.split("/", 3)
    hostname, port = hostname.split(":")
    url = "%s//%s:%s/%s" % (schema, socket.gethostbyname(hostname), port, path)

    r = requests.get(url).json()
    return r["webSocketDebuggerUrl"]


def sanitize_title(title):
    keepcharacters = (" ", ".", "_")
    return "".join(c for c in title if c.isalnum() or c in keepcharacters).strip()[-50:]


async def execute_job(extractor_cls, chrome_url, job):
    logger.info("Initiating browser for job execution")
    browser = await connect({"browserWSEndpoint": chrome_url})

    page = await browser.newPage()
    await page.setUserAgent(USER_AGENT)
    await page.setViewport({"width": 1024, "height": 768})
    extractor = extractor_cls(job, page)

    def on_restart_required():
        extractor.cancelled = True

    browser.on("disconnected", on_restart_required)
    page.on("close", on_restart_required)

    result = await extractor.extract()

    logger.info("Cleaning up browser")
    await page.close()
    await browser.disconnect()

    return result


def duration_to_number(duration):
    duration_time, partial_seconds = duration.split(".")
    hours, minutes, seconds = duration_time.split(":")
    total = int(hours) * 60
    total += int(minutes)
    total *= 60
    total += int(seconds)
    return total


def download_file_segment(url, target, headers):
    for i in range(3):
        logger.debug("Starting to download %s attempt %s" % (url, i))
        try:
            with requests.get(url, stream=True, headers=headers) as r:
                with open(target, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
        except requests.exceptions.RequestException:
            logger.warning("Failed to download url %s" % (url,))
            continue
        return
    raise FailedToDownloadSegmentException()


@shared_task
def handle_job(job_id):
    logger.info("Trying to handle job %s" % (job_id,))
    job = Job.objects.get(pk=job_id)
    if job.status != Job.PENDING:
        raise JobNotPendingException(
            "Job %i is not in correct status, it is in %s" % (job_id, job.status)
        )

    for extractor_cls in EXTRACTORS:
        if extractor_cls.matcher.match(job.url):
            break
    else:
        logger.warning("Failed to find any extractor for %s" % (job_id,))
        job.status = job.FAILED
        job.status_message = "Failed to find any extractor"
        job.save()
        return

    job.status = job.PARSING
    job.status_message = "Extracting video using %s" % (extractor_cls.name,)
    job.save()

    for i in range(3):
        try:
            chrome_url = get_chrome_url()
        except:
            logger.exception("Failed to get chrome URL")

            job.status_message = "Failed to get chrome URL"
            job.status = job.FAILED
            job.save()

            return

        try:
            result = asyncio.get_event_loop().run_until_complete(
                execute_job(extractor_cls, chrome_url, job)
            )
        except (errors.PyppeteerError, asyncio.TimeoutError):
            logger.exception("Pyppeteer failed, attempt %s of 3" % (i + 1))
            time.sleep(5)
        else:
            break
    else:
        job.status_message = "Failed to get puppeteer to get url"
        job.status = job.FAILED
        job.save()

        return

    media_path = str(job.pk)
    target_path = os.path.join(settings.MEDIA_ROOT, media_path)
    if not os.path.isdir(target_path):
        os.makedirs(target_path)

    logger.debug("Fetching m3u8")
    headers = {"User-Agent": USER_AGENT}
    headers.update(result["headers"])
    r = requests.get(result["url"], headers=headers)
    playlist = m3u8.loads(r.text)

    target_filename = "%s - %s.mp4" % (sanitize_title(result["title"]), result["id"])
    target_full_path = os.path.join(target_path, target_filename)

    job.name = target_filename
    job.status = job.DOWNLOADING
    job.status_message = f"Downloading {len(playlist.segments)} segments"
    job.save()

    logger.debug("Queuing up %s segments" % (len(playlist.segments),))
    with tempfile.TemporaryDirectory() as download_dir:
        segments = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=settings.DOWNLOAD_CONCURRENCY
        ) as executor:
            futures = []
            for i, segment in enumerate(playlist.segments):
                target = os.path.join(download_dir, f"{i:05}.ts")
                segments.append(target)
                futures.append(
                    (
                        executor.submit(
                            download_file_segment, segment.uri, target, headers
                        )
                    )
                )

            for i, future in enumerate(futures, 1):
                try:
                    future.result()
                except Exception:
                    logger.exception("Failed to download")
                    job.status = job.FAILED
                    job.status_message = f"Failed while downloading segment {i}"
                    job.save()
                    return
                else:
                    job.send_progress_update(total=len(playlist.segments), progress=i)

        job.status_message = f"Finished downloading {len(playlist.segments)} segments, merging with ffmpeg"
        job.save()

        cmd = ["ffmpeg"]
        cmd += [
            "-y",
            "-i",
            f"concat:{'|'.join(segments)}",
            "-c",
            "copy",
            "-f",
            "mp4",
            target_full_path,
        ]

        logger.debug("Merging result with ffmpeg")

        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        duration, progress = None, None

        for line in p.stderr:
            line = line.decode("utf-8")
            if not duration:
                duration_result = re.findall(
                    r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})", line
                )
                if duration_result:
                    duration = duration_to_number(duration_result[0])

            progress_result = re.findall(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", line)
            if progress_result:
                progress = duration_to_number(progress_result[0])

            if duration is not None and progress is not None:
                job.send_progress_update(duration, progress)

        returncode = p.wait()

        if returncode:
            job.status_message = "Failed FFMpeg with returncode %s" % (returncode,)
            job.status = job.FAILED
        else:
            job.path = os.path.join(media_path, target_filename)
            job.status_message = "Finished"
            job.status = job.SUCCESS
        job.save()
