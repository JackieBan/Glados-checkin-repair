#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: checkin.py(GLaDOS签到 + 信息推送)
Update: 2026/10/08 
"""


import requests
import json
import os
import sys
import time


# ============ 配置 ============
AUTO_EXCHANGE = False       # 自动兑换开关
EXCHANGE_PLAN = "plan500"
EXCHANGE_COST = 500
SHOW_EXTRA    = True        # 是否推送扩展信息
# =============================


def get_cookies():
    if os.environ.get("GR_COOKIE"):
        print("已获取并使用Env环境 Cookie")
        if '&' in os.environ["GR_COOKIE"]:
            cookies = os.environ["GR_COOKIE"].split('&')
        elif '\n' in os.environ["GR_COOKIE"]:
            cookies = os.environ["GR_COOKIE"].split('\n')
        else:
            cookies = [os.environ["GR_COOKIE"]]
    else:
        from config import Cookies
        cookies = Cookies
        if len(cookies) == 0:
            print("未获取到正确的GlaDOS账号Cookie")
            return
    print(f"共获取到{len(cookies)}个GlaDOS账号Cookie\n")
    print(f"脚本执行时间(北京时区): {time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())}\n")
    return cookies


def load_send():
    cur_path = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(cur_path)
    if os.path.exists(cur_path + "/sendNotify.py"):
        try:
            from sendNotify import send
            return send
        except Exception as e:
            print(f"加载通知服务失败：{e}")
            return None
    else:
        print("加载通知服务失败")
        return None


def build_headers(cookie):
    return {
        'cookie': cookie,
        'referer': 'https://glados.cloud/console/checkin',
        'origin': 'https://glados.cloud',
        'user-agent': (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        ),
        'content-type': 'application/json;charset=UTF-8'
    }


def clean_num(v):
    if v is None:
        return "未知"
    try:
        return str(int(float(str(v))))
    except Exception:
        return str(v)


def fmt_gb(num_bytes):
    """字节转 GB，保留 2 位小数"""
    try:
        return f"{int(num_bytes) / (1024 ** 3):.2f} GB"
    except Exception:
        return "未知"


def map_plan_by_vip(vip):
    """
    根据 VIP 值映射套餐名和月流量额度。
    依据 https://glados.cloud 套餐页 + 社区信息：
        Pro  : 500GB/月   → vip = 31
        Team : 2000GB/月  → vip >= 41
        Basic: 200GB/月   → vip 21~30
        Free : 10GB/月    → vip < 21
    """
    try:
        v = int(vip)
    except Exception:
        return "未知", "未知"

    if v >= 41:
        return "Team", "2000GB/月"
    elif v >= 31:
        return "Pro", "500GB/月"
    elif v >= 21:
        return "Basic", "200GB/月"
    else:
        return "Free", "10GB/月"


def do_exchange(cookie, headers, plan, cost):
    url = "https://glados.cloud/api/user/exchange"
    for body in ({"plan": plan}, {"points": cost}):
        try:
            r = requests.post(url, headers=headers, data=json.dumps(body), timeout=20)
            j = r.json()
            msg = j.get('message') or j.get('msg') or str(j)
            if j.get('code') == 0 or j.get('success') is True:
                return True, msg
            print(f"兑换尝试 {body} 返回：{msg}")
        except Exception as e:
            print(f"兑换请求异常（{body}）：{e}")
    return False, "兑换请求失败"


def checkin(cookie):
    headers = build_headers(cookie)
    result = {
        "mess": "", "email": "未知账号", "remain": "未知",
        "used": "未知", "plan": "未知", "plan_limit": "未知",
        "points": None, "streak": None, "today_gain": None,
        "spins": None, "traffic_used": "未知",
        "port": "未知", "region": "未知", "code": "未知", "vip": "未知",
        "notice": "", "exchange_msg": "",
    }

    # ---------- 1. 签到 ----------
    try:
        r = requests.post(
            "https://glados.cloud/api/user/checkin",
            headers=headers,
            data=json.dumps({'token': 'glados.cloud'}),
            timeout=20
        )
        cj = r.json()
        result["mess"] = cj.get('message') or cj.get('msg') or '签到无返回'
    except Exception as e:
        print(f"签到请求失败：{e}")
        return None

    # ---------- 2. status ----------
    try:
        r = requests.get("https://glados.cloud/api/user/status", headers=headers, timeout=20)
        sj = r.json()
        data = sj.get('data') or sj.get('result') or sj

        result["email"] = data.get('email', '未知账号')

        left = data.get('leftDays')
        if left is not None:
            result["remain"] = clean_num(left)

        used = data.get('days')
        if used is not None:
            result["used"] = clean_num(used)

        # VIP → 套餐名 + 月流量额度
        vip = data.get('vip')
        result["vip"] = vip if vip is not None else "未知"
        plan_name, plan_limit = map_plan_by_vip(vip)
        result["plan"] = plan_name
        result["plan_limit"] = plan_limit

        result["port"]   = data.get('port', '未知')
        result["region"] = data.get('region', '未知')
        result["code"]   = data.get('code', '未知')

        # status.traffic = 本月已用流量（字节）
        traffic = data.get('traffic')
        if traffic is not None:
            result["traffic_used"] = fmt_gb(traffic)

        # 官方公告
        noti = data.get('notifications') or []
        if noti:
            n = noti[0]
            result["notice"] = f"{n.get('title','')}（{n.get('level','')}）"
    except Exception as e:
        print(f"状态查询失败（不影响签到）：{e}")

    # ---------- 3. points ----------
    try:
        r = requests.get("https://glados.cloud/api/user/points", headers=headers, timeout=20)
        pj = r.json()
        if pj.get('points') is not None:
            result["points"] = int(float(str(pj['points'])))
        if pj.get('streak') is not None:
            result["streak"] = pj['streak']
        if pj.get('spinsLeft') is not None:
            result["spins"] = pj['spinsLeft']
        hist = pj.get('history') or []
        if hist:
            chg = hist[0].get('change')
            if chg is not None:
                result["today_gain"] = clean_num(chg)
    except Exception as e:
        print(f"积分查询失败（不影响签到）：{e}")

    # ---------- 4. 自动兑换 ----------
    if AUTO_EXCHANGE and result["points"] is not None and result["points"] >= EXCHANGE_COST:
        print(f"当前积分 {result['points']} >= {EXCHANGE_COST}，尝试兑换 {EXCHANGE_PLAN} ...")
        ok, msg = do_exchange(cookie, headers, EXCHANGE_PLAN, EXCHANGE_COST)
        if ok:
            result["exchange_msg"] = f"已自动兑换 {EXCHANGE_PLAN}：{msg}"
            print(result["exchange_msg"])
            time.sleep(2)
            try:
                r = requests.get("https://glados.cloud/api/user/points", headers=headers, timeout=20)
                pj = r.json()
                if pj.get('points') is not None:
                    result["points"] = int(float(str(pj['points'])))
                if pj.get('streak') is not None:
                    result["streak"] = pj['streak']
            except Exception:
                pass
            try:
                r = requests.get("https://glados.cloud/api/user/status", headers=headers, timeout=20)
                sj = r.json()
                data = sj.get('data') or sj.get('result') or sj
                left = data.get('leftDays')
                if left is not None:
                    result["remain"] = clean_num(left)
            except Exception:
                pass
        else:
            result["exchange_msg"] = f"兑换未成功：{msg}"
            print(result["exchange_msg"])

    return result


def run_checkin():
    contents = []
    cookies = get_cookies()
    if not cookies:
        return ""

    for cookie in cookies:
        r = checkin(cookie)
        if not r or not r["mess"]:
            continue

        content = (
            f"账号：{r['email']}\n"
            f"签到结果：{r['mess']}\n"
            f"剩余天数：{r['remain']}\n"
            f"剩余积分：{clean_num(r['points'])}\n"
            f"今日得分：{clean_num(r['today_gain'])}\n"
            f"连续签到：{r['streak'] if r['streak'] is not None else '未知'} 天\n"
        )

        if SHOW_EXTRA:
            content += (
                f"套餐等级：{r['plan']} / VIP {r['vip']}\n"
                f"本月已用：{r['traffic_used']}\n"
                f"套餐额度：{r['plan_limit']}\n"
                f"剩余抽奖：{r['spins']} 次\n"
                f"节点端口：{r['port']}（{r['region']}）\n"
                f"邀请码：{r['code']}\n"
            )
            if r["notice"]:
                content += f"官方公告：{r['notice']}\n"

        if r["exchange_msg"]:
            content += f"自动兑换：{r['exchange_msg']}\n"

        print(content)
        contents.append(content)

    return "".join(contents)


if __name__ == '__main__':
    title = "GLaDOS签到通知"
    contents = run_checkin()
    send_notify = load_send()
    if send_notify:
        if contents == '':
            contents = '签到失败，请检查账户信息以及网络环境'
            print(contents)
        send_notify(title, contents)