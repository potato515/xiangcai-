#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""百度App信息流标题采集器（uiautomator2 + MuMu模拟器）
采集30-60字长标题的家庭伦理冲突悬念故事，结果写入JSON文件
"""
import os
import sys
import subprocess
import time
import random
import json
import re
from datetime import datetime

# 自动将 MuMu 的 adb 目录加入 PATH
_MUMU_ADB = r"D:\Program Files\Netease\MuMu\nx_main"
if os.path.isdir(_MUMU_ADB) and _MUMU_ADB not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _MUMU_ADB + os.pathsep + os.environ.get("PATH", "")

import uiautomator2 as u2

# ============ 关键配置 ============
DEVICE_SERIAL = '127.0.0.1:16384'   # MuMu 实例0 ADB端口
MIN_VIEWS = 0                        # 不按阅读量过滤，全部采集
MAX_SWIPES = 50                      # 最大滑动次数
# 600x720 屏幕适配滑动坐标
SWIPE_START = (300, 620)
SWIPE_END = (300, 180)
# ==================================


def parse_view_count(text):
    """解析阅读量/热度数值"""
    if not text:
        return 0
    text = text.strip()
    # X万人阅读 / X万人看过 / X万热度
    match = re.search(r'([\d.]+)\s*万\s*(人|阅读|看过|热度|播放)', text)
    if match:
        return int(float(match.group(1)) * 10000)
    # X万人
    match = re.search(r'([\d.]+)\s*万\s*人', text)
    if match:
        return int(float(match.group(1)) * 10000)
    # X万
    match = re.search(r'([\d.]+)\s*万', text)
    if match:
        return int(float(match.group(1)) * 10000)
    # X人阅读 / X人看过 / X人播放
    match = re.search(r'(\d+)\s*(人|阅读|看过|播放)', text)
    if match:
        return int(match.group(1))
    # 纯数字
    match = re.search(r'(\d+)', text)
    if match:
        return int(match.group(1))
    return 0


def parse_watching_count(text):
    """解析正在看的人数"""
    if not text:
        return 0
    text = text.strip()
    # X万人正在看 / X万人在看
    match = re.search(r'([\d.]+)\s*万\s*人?\s*(正在看|在看|在线|观看中)', text)
    if match:
        return int(float(match.group(1)) * 10000)
    # X人正在看 / X人在看
    match = re.search(r'(\d+)\s*人?\s*(正在看|在看|在线|观看中)', text)
    if match:
        return int(match.group(1))
    return 0


def is_view_count_text(text):
    """判断文本是否是阅读量/热度相关"""
    if not text or len(text) > 20:
        return False
    keywords = ["人看过", "人阅读", "万人", "万热度", "万播放", "阅读", "热度", "播放"]
    for kw in keywords:
        if kw in text:
            return True
    # 纯数字+万
    if re.match(r'^[\d.]+\s*万$', text):
        return True
    return False


def is_watching_text(text):
    """判断文本是否是正在看人数相关"""
    if not text or len(text) > 20:
        return False
    keywords = ["正在看", "在看", "在线", "观看中"]
    for kw in keywords:
        if kw in text:
            return True
    return False


def is_story_title(text):
    if not text:
        return False
    text = text.strip()
    # 长标题 30-60 字
    if len(text) < 30 or len(text) > 60:
        return False
    if re.match(r'^[\d\s\W]+$', text):
        return False
    blacklist = ["广告", "推广", "直播", "热门", "下载", "游戏", "影视",
                 "免费", "红包", "福利", "新人专享", "关注", "点赞",
                 "评论", "分享", "收藏", "转发", "瑜伽", "一字马",
                 "卷腹", "健身", "动作", "治愈", "小院", "帐篷",
                 "美女", "女神", "户外", "练习", "功夫", "翻跃"]
    for word in blacklist:
        if word in text:
            return False
    return True


def adb_swipe(d, start, end, duration_ms=300):
    """使用 adb shell input swipe 滑动，规避 Android12 INJECT_EVENTS 权限限制"""
    cmd = ["adb", "-s", DEVICE_SERIAL, "shell", "input", "swipe",
           str(start[0]), str(start[1]), str(end[0]), str(end[1]),
           str(duration_ms)]
    try:
        subprocess.run(cmd, capture_output=True, timeout=15, check=False)
        return True
    except Exception as e:
        print(f"[!] adb滑动失败: {e}")
        try:
            d.swipe(start[0], start[1], end[0], end[1], duration=duration_ms)
        except Exception:
            pass
        return False


def collect(output_file=None, max_swipes=None):
    """执行采集，返回采集到的标题列表
    Args:
        output_file: 结果输出JSON文件路径，None则不写文件
        max_swipes: 最大滑动次数，None则用默认值
    Returns:
        list: 采集到的标题字典列表
    """
    if max_swipes:
        global MAX_SWIPES
        MAX_SWIPES = max_swipes

    print("=" * 65)
    print("  百度信息流 - 长标题故事采集器")
    print("=" * 65)

    # 检查模拟器连接
    print(f"[*] 正在连接模拟器 {DEVICE_SERIAL} ...")
    try:
        d = u2.connect(DEVICE_SERIAL)
        info = d.info
        print(f"[+] 已连接：{info.get('productName', '设备')} "
              f"分辨率 {info.get('displayWidth')}x{info.get('displayHeight')}")
    except Exception as e:
        print(f"[x] 连接模拟器失败: {e}")
        print("[!] 请确保 MuMu 模拟器已启动，并且 ADB 端口为 16384")
        return []

    print("[*] 正在启动百度App ...")
    try:
        d.app_start("com.baidu.searchbox")
        time.sleep(6)
    except Exception as e:
        print(f"[x] 启动百度App失败: {e}")
        return []

    # 回到推荐信息流
    try:
        if d(text="推荐").exists(timeout=2):
            d(text="推荐").click()
            time.sleep(2)
            print("[+] 已回到「推荐」信息流")
    except Exception:
        print("[!] 未找到推荐标签")

    collected = []
    seen_titles = set()
    print(f"\n[*] 开始采集，共滑动 {MAX_SWIPES} 次")
    print("-" * 65)

    for i in range(MAX_SWIPES):
        time.sleep(random.uniform(2.5, 5.0))

        # 防护：确认在推荐信息流
        try:
            has_rec = d(text="推荐").exists(timeout=0.5)
            has_msg_page = d(text="互动消息").exists(timeout=0.3) or \
                           d(text="收藏了你的作品").exists(timeout=0.3)
            if (not has_rec) or has_msg_page:
                print(f"[!] 检测到不在推荐流(第{i+1}次)，重启App...")
                d.app_stop("com.baidu.searchbox")
                time.sleep(2)
                d.app_start("com.baidu.searchbox")
                time.sleep(6)
                try:
                    d(text="推荐").click(timeout=2)
                    time.sleep(2)
                except Exception:
                    pass
        except Exception:
            pass

        # 关闭弹窗
        try:
            for pop in ["以后再说", "暂不", "取消", "关闭", "知道了", "拒绝"]:
                if d(text=pop).exists(timeout=0.3):
                    d(text=pop).click()
        except Exception:
            pass

        # 获取所有文本元素
        all_texts = d.xpath('//android.widget.TextView').all()

        # 第一遍：收集所有阅读量和正在看人数的位置
        view_map = {}
        watching_map = {}
        for idx, elem in enumerate(all_texts):
            try:
                t = (elem.text or "").strip()
            except Exception:
                continue
            if is_view_count_text(t):
                view_map[idx] = {
                    'num': parse_view_count(t),
                    'text': t
                }
            if is_watching_text(t):
                watching_map[idx] = {
                    'num': parse_watching_count(t),
                    'text': t
                }

        # 第二遍：抓 30-60 字长标题，就近匹配阅读量和正在看人数
        for idx, elem in enumerate(all_texts):
            try:
                text = (elem.text or "").strip()
            except Exception:
                continue
            if not is_story_title(text):
                continue

            # 就近找阅读量（前后8个元素内，扩大范围）
            view_num = None
            views_text = ""
            for dist in range(1, 9):
                if (idx - dist) in view_map:
                    view_num = view_map[idx - dist]['num']
                    views_text = view_map[idx - dist]['text']
                    break
                if (idx + dist) in view_map:
                    view_num = view_map[idx + dist]['num']
                    views_text = view_map[idx + dist]['text']
                    break

            # 就近找正在看人数（前后8个元素内）
            watching_num = None
            watching_text = ""
            for dist in range(1, 9):
                if (idx - dist) in watching_map:
                    watching_num = watching_map[idx - dist]['num']
                    watching_text = watching_map[idx - dist]['text']
                    break
                if (idx + dist) in watching_map:
                    watching_num = watching_map[idx + dist]['num']
                    watching_text = watching_map[idx + dist]['text']
                    break

            if view_num is not None and view_num < MIN_VIEWS:
                continue

            if text not in seen_titles:
                seen_titles.add(text)
                collected.append({
                    'id': len(collected) + 1,
                    'title': text,
                    'read_count': view_num or 0,
                    'views_text': views_text,
                    'watching_count': watching_num or 0,
                    'watching_text': watching_text,
                    'used': False,
                    'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                print(f"[+] [{len(collected)}] ({len(text)}字) {text[:40]}... "
                      f"(阅读: {views_text or '未知'}, 正在看: {watching_text or '未知'})")

        adb_swipe(d, SWIPE_START, SWIPE_END, random.randint(250, 400))
        print(f"[-] 滑动 {i+1}/{MAX_SWIPES}，已采集 {len(collected)} 条")

    # 写入输出文件
    if output_file:
        # 读取已有数据，合并去重
        existing = []
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        existing_titles = {item.get('title', '') for item in existing}
        new_items = [item for item in collected if item['title'] not in existing_titles]

        # 重新编号
        all_items = existing + new_items
        for idx, item in enumerate(all_items):
            item['id'] = idx + 1

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_items, f, ensure_ascii=False, indent=2)
        print(f"\n[+] 新增 {len(new_items)} 条，总计 {len(all_items)} 条")
        print(f"[+] 数据已保存至：{output_file}")

    print("\n" + "=" * 65)
    print(f"[+] 本次采集完成！共获取 {len(collected)} 条故事标题")
    return collected


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='百度信息流标题采集器')
    parser.add_argument('--output', type=str, default=None, help='输出JSON文件路径')
    parser.add_argument('--swipes', type=int, default=50, help='最大滑动次数')
    args = parser.parse_args()
    collect(output_file=args.output, max_swipes=args.swipes)
