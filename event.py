import os
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import aiohttp
import asyncio
import math
import functools
import re

# type 0 普通常驻任务深渊 1 新闻 2 蛋池 3 限时活动H5

event_data = {
    'cn': [],
}

event_updated = {
    'cn': '',
}

lock = {
    'cn': asyncio.Lock(),
}

ignored_key_words = [
    "概率公示"
]

ignored_ann_ids = [

]

list_api = 'https://api.biligame.com/news/list.action?gameExtensionId=45&positionId=2&pageNum=1&pageSize=15&typeId='
detail_api = 'https://api.biligame.com/news/%s.action'


def cache(ttl=timedelta(hours=1), arg_key=None):
    def wrap(func):
        cache_data = {}

        @functools.wraps(func)
        async def wrapped(*args, **kw):
            nonlocal cache_data
            default_data = {"time": None, "value": None}
            ins_key = 'default'
            if arg_key:
                ins_key = arg_key + str(kw.get(arg_key, ''))
                data = cache_data.get(ins_key, default_data)
            else:
                data = cache_data.get(ins_key, default_data)

            now = datetime.now()
            if not data['time'] or now - data['time'] > ttl:
                try:
                    data['value'] = await func(*args, **kw)
                    data['time'] = now
                    cache_data[ins_key] = data
                except Exception as e:
                    raise e

            return data['value']

        return wrapped

    return wrap


@cache(ttl=timedelta(hours=3), arg_key='url')
async def query_data(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()
    except:
        pass
    return None


async def load_event_cn():
    result = await query_data(url=list_api)
    if result and 'code' in result and result['code'] == 0:
        event_data['cn'] = []
        datalist = result['data']
        for item in datalist:
            ignore = False
            for ann_id in ignored_ann_ids:
                if ann_id == item["id"]:
                    ignore = True
                    break
            if ignore:
                continue

            for keyword in ignored_key_words:
                if keyword in item['title']:
                    ignore = True
                    break
                if ignore:
                    continue

            # 从正文中获取活动时间
            content_result = await query_data(url=detail_api % item["id"])
            if not (content_result and 'code' in content_result and content_result['code'] == 0):
                # 直接跳过？
                continue

            detail = content_result['data']['content']
            # 小编不讲武德 时间就不识别了
            searchObj = re.search(
                r'.*?(\d{4,}).*?年.*?(\d+).*?月.*?(\d+).*?日.*?[~|～].*?.*?(\d+).*?月.*?(\d+).*?日', detail, re.M | re.I)

            try:
                datelist = searchObj.groups()  # ('2021', '9', '17', '9', '17')
            except Exception as e:
                continue
            if not (datelist and len(datelist) >= 5):
                continue

            syear = int(datelist[0])
            smonth = int(datelist[1])
            sday = int(datelist[2])

            emonth = int(datelist[3])
            eday = int(datelist[4])
            eyear = smonth > emonth and syear+1 or syear

            start_time = datetime.strptime(
                f'{syear}-{smonth}-{sday} 00:00:00', r"%Y-%m-%d  %H:%M:%S")
            end_time = datetime.strptime(
                f'{eyear}-{emonth}-{eday} 23:59:59', r"%Y-%m-%d  %H:%M:%S")
            event = {'title': item['title'],
                     'start': start_time,
                     'end': end_time,
                     'forever': False,
                     'type': 0}

            if '维护' in item['title']:
                event['type'] = 3
            elif '召唤' in item['title'] or '福袋' in item['title']:
                event['type'] = 2
            elif '活动' in item['title'] or '限时' in item['title']:
                event['type'] = 1
            event_data['cn'].append(event)
        return 0
    return 1


async def load_event(server):
    if server == 'cn':
        return await load_event_cn()
    return 1


def get_pcr_now(offset):
    pcr_now = datetime.now()
    if pcr_now.hour < 4:
        pcr_now -= timedelta(days=1)
    pcr_now = pcr_now.replace(
        hour=18, minute=0, second=0, microsecond=0)  # 用晚6点做基准
    pcr_now = pcr_now + timedelta(days=offset)
    return pcr_now


async def get_events(server, offset, days):
    events = []
    pcr_now = datetime.now()
    if pcr_now.hour < 4:
        pcr_now -= timedelta(days=1)
    pcr_now = pcr_now.replace(
        hour=18, minute=0, second=0, microsecond=0)  # 用晚6点做基准

    await lock[server].acquire()
    try:
        t = pcr_now.strftime('%y%m%d')
        if event_updated[server] != t:
            if await load_event(server) == 0:
                event_updated[server] = t
    finally:
        lock[server].release()

    start = pcr_now + timedelta(days=offset)
    end = start + timedelta(days=days)
    end -= timedelta(hours=18)  # 晚上12点结束

    for event in event_data[server]:
        if end > event['start'] and start < event['end']:  # 在指定时间段内 已开始 且 未结束
            event['start_days'] = math.ceil(
                (event['start'] - start) / timedelta(days=1))  # 还有几天开始
            event['left_days'] = math.floor(
                (event['end'] - start) / timedelta(days=1))  # 还有几天结束
            events.append(event)
    # 按type从大到小 按剩余天数从小到大
    events.sort(key=lambda item: item["type"]
                * 100 - item['left_days'], reverse=True)
    return events


if __name__ == '__main__':
    async def main():
        await load_event_cn()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
