import requests
import json
import datetime
import logging
import time
import os
from openai import OpenAI
from dotenv import load_dotenv
from logging.handlers import TimedRotatingFileHandler

# ================= 加载环境变量 =================
load_dotenv()

# ================= 配置区 =================
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
JIEKOU_ID = os.getenv("JIEKOU_ID")
JIEKOU_KEY = os.getenv("JIEKOU_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not all([FEISHU_WEBHOOK, JIEKOU_ID, JIEKOU_KEY, DEEPSEEK_API_KEY]):
    raise ValueError("❌ 请在 .env 文件中配置 FEISHU_WEBHOOK, JIEKOU_ID, JIEKOU_KEY, DEEPSEEK_API_KEY")

CONFIG_FILE = "config.json"

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logging.error(f"❌ 加载配置文件失败: {e}")
        return {"RED_KEYWORDS": [], "YELLOW_PEOPLE": [], "GREEN_DATES": []}

def setup_logging():
    main_handler = TimedRotatingFileHandler(
        'bot.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    main_handler.setLevel(logging.INFO)
    main_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    error_handler = TimedRotatingFileHandler(
        'error.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    logging.basicConfig(
        level=logging.INFO,
        handlers=[main_handler, error_handler, console_handler]
    )

setup_logging()

GREEN_LOG_FILE = "green_alert_log.json"
PUSHED_FILE = "pushed_events.json"

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

def send_to_feishu(message):
    payload = {"msg_type": "text", "content": {"text": message}}
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=payload, timeout=5)
        if resp.status_code == 200:
            logging.info("✅ 飞书推送成功")
        else:
            logging.error(f"❌ 飞书失败: {resp.text}")
    except Exception as e:
        logging.error(f"❌ 推送异常: {e}")

def fetch_hotspots():
    url = "https://cn.apihz.cn/api/xinwen/weibo2.php"
    params = {"id": JIEKOU_ID, "key": JIEKOU_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get('code') == 200:
            return data.get('data', [])
        else:
            logging.error(f"❌ 接口异常: {data.get('msg')}")
            return []
    except Exception as e:
        logging.error(f"❌ 抓取失败: {e}")
        return []

def call_deepseek(title, desc):
    system_prompt = """你是一个舆情审核标准制定专家。请根据给定事件输出JSON：
{"pass": "通过标准", "block": "拦截标准", "manual": "人工复核内容"}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"事件标题：{title}\n事件描述：{desc or '无详细描述'}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("pass"), result.get("block"), result.get("manual")
    except Exception as e:
        logging.error(f"❌ DeepSeek失败: {e}")
        return ("表达哀悼、祈福、理性追问...", "幸灾乐祸、地域攻击、编造谣言...", "疑似谣言需人工核实")

def is_domestic_event(title, desc):
    prompt = f"""
请根据以下事件信息，判断该事件是否发生在中国境内（包括中国大陆、香港、澳门、台湾）。
只回答“是”或“否”，不要输出其他任何内容。
事件标题：{title}
事件描述：{desc or '无详细描述'}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=5
        )
        answer = response.choices[0].message.content.strip()
        return "是" in answer
    except Exception as e:
        logging.error(f"❌ 国内判断API调用失败: {e}")
        return True

def check_green_alerts(green_dates):
    today = datetime.date.today()
    log = {}
    if os.path.exists(GREEN_LOG_FILE):
        with open(GREEN_LOG_FILE, "r", encoding="utf-8") as f:
            try:
                log = json.load(f)
            except:
                log = {}

    messages = []
    for date_str in green_dates:
        try:
            target = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            logging.error(f"日期格式错误: {date_str}，跳过")
            continue

        delta = (target - today).days
        if delta < -3 or delta > 3:
            continue

        if log.get(date_str) == str(today):
            continue

        if delta > 0:
            msg = f"距离 {target.month}月{target.day}日 还有 {delta} 天"
        elif delta == 0:
            msg = f"今天是 {target.month}月{target.day}日！"
        else:
            msg = f"距离 {target.month}月{target.day}日 已过去 {-delta} 天"

        full_msg = f"🟢 绿色警报【日期提醒】\n{msg}"
        messages.append(full_msg)
        log[date_str] = str(today)

    if messages:
        with open(GREEN_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

    return messages

def main():
    logging.info("开始扫描微博热点...")

    config = load_config()
    red_keywords = config.get("RED_KEYWORDS", [])
    yellow_people = config.get("YELLOW_PEOPLE", [])
    green_dates = config.get("GREEN_DATES", [])
    if not red_keywords and not yellow_people and not green_dates:
        logging.warning("⚠️ 配置文件为空或加载失败，请检查 config.json")

    pushed = {}
    if os.path.exists(PUSHED_FILE):
        with open(PUSHED_FILE, 'r', encoding='utf-8') as f:
            try:
                pushed = json.load(f)
            except:
                pushed = {}
    expire_time = datetime.datetime.now() - datetime.timedelta(days=3)
    pushed = {k: v for k, v in pushed.items() if datetime.datetime.fromisoformat(v) > expire_time}

    hotspots = fetch_hotspots()
    if not hotspots:
        logging.info("无数据")
        return

    logging.info(f"共 {len(hotspots)} 条热点")
    red_count = yellow_count = 0

    for item in hotspots:
        title = item.get('title', '')
        hot = item.get('desc_extr', '')
        red = False

        for kw in red_keywords:
            if kw in title:
                event_key = f"red_{title}"
                if event_key in pushed:
                    logging.info(f"⏭️ 重复红色事件，跳过: {title}")
                    break

                if not is_domestic_event(title, hot):
                    logging.info(f"⏭️ 非国内事件，跳过红色警报: {title}")
                    break

                pass_std, block_std, manual_std = call_deepseek(title, hot)
                text_msg = f"""🔴 红色警报【舆情动态】
事件：{title}
详情：热度值 {hot}

🤖 AI审核
✅通过：{pass_std}
❌拦截：{block_std}
⚠️复核：{manual_std}"""
                send_to_feishu(text_msg)
                red_count += 1
                red = True
                pushed[event_key] = datetime.datetime.now().isoformat()
                break

        if not red:
            for person in yellow_people:
                if person in title:
                    event_key = f"yellow_{title}"
                    if event_key in pushed:
                        logging.info(f"⏭️ 重复黄色事件，跳过: {title}")
                        break

                    text_msg = f"""🟡 黄色警报【舆情动态】
事件：{title}
详情：热度值 {hot}"""
                    send_to_feishu(text_msg)
                    yellow_count += 1
                    pushed[event_key] = datetime.datetime.now().isoformat()
                    break

    logging.info(f"热点扫描完成：红色 {red_count} 条，黄色 {yellow_count} 条")

    with open(PUSHED_FILE, 'w', encoding='utf-8') as f:
        json.dump(pushed, f, ensure_ascii=False, indent=2)

    green_msgs = check_green_alerts(green_dates)
    for msg in green_msgs:
        send_to_feishu(msg)
        logging.info(f"绿色警报已推送: {msg[:30]}...")

import schedule

if __name__ == "__main__":
    main()
    schedule.every(15).minutes.do(main)
    logging.info("🤖 机器人已启动，每15分钟扫描一次")
    logging.info("绿色日期窗口：前3天～后3天，每天每个日期仅推送一天")
    while True:
        schedule.run_pending()
        time.sleep(10)