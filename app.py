import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackAction
import openai
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == "スタート":
        buttons_template = ButtonsTemplate(
            title='シチュエーションを選択',
            text='日常生活または仕事の場面を選んでください',
            actions=[
                PostbackAction(label='日常生活', data='scenario_daily'),
                PostbackAction(label='仕事', data='scenario_work')
            ]
        )
        template_message = TemplateSendMessage(
            alt_text='シチュエーション選択',
            template=buttons_template
        )
        line_bot_api.reply_message(event.reply_token, template_message)
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="「スタート」と入力してシナリオを開始してください。")
        )

@handler.add(PostbackEvent)
def handle_postback(event):
    if event.postback.data.startswith('scenario_'):
        scenario_type = event.postback.data.split('_')[1]
        scenario = generate_scenario(scenario_type)
        adhd_info = get_adhd_info(scenario)
        comparison = generate_comparison(scenario)
        hack = get_adhd_hack(scenario)
        explanation = generate_explanation(hack, comparison)

        messages = [
            TextSendMessage(text=f"シナリオ: {scenario}"),
            TextSendMessage(text=f"ADHD/ASD情報: {adhd_info}"),
            TextSendMessage(text=f"一般的な対応: {comparison}"),
            TextSendMessage(text=f"ADHD/ASDのハック: {hack}"),
            TextSendMessage(text=f"解説: {explanation}"),
            TemplateSendMessage(
                alt_text='次のアクション',
                template=ButtonsTemplate(
                    title='次のアクション',
                    text='次に何をしますか？',
                    actions=[
                        PostbackAction(label='スタートに戻る', data='restart'),
                        PostbackAction(label='さらなる理解', data=f'more_{scenario_type}_{scenario}')
                    ]
                )
            )
        ]
        line_bot_api.reply_message(event.reply_token, messages)

    elif event.postback.data == 'restart':
        buttons_template = ButtonsTemplate(
            title='シチュエーションを選択',
            text='日常生活または仕事の場面を選んでください',
            actions=[
                PostbackAction(label='日常生活', data='scenario_daily'),
                PostbackAction(label='仕事', data='scenario_work')
            ]
        )
        template_message = TemplateSendMessage(
            alt_text='シチュエーション選択',
            template=buttons_template
        )
        line_bot_api.reply_message(event.reply_token, template_message)

    elif event.postback.data.startswith('more_'):
        _, scenario_type, prev_scenario = event.postback.data.split('_', 2)
        new_scenario = generate_similar_scenario(prev_scenario)
        # ここから4-7のステップを繰り返す（上記のコードと同様）

def generate_scenario(scenario_type):
    prompt = f"Generate a {scenario_type} scenario related to ADHD or ASD."
    response = openai.Completion.create(engine="text-davinci-002", prompt=prompt, max_tokens=100)
    return response.choices[0].text.strip()

def get_adhd_info(scenario):
    url = "https://adhd-asd-information.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # ここでスクレイピングロジックを実装
    # 例: return soup.find('p', class_='adhd-info').text
    return "ADHD/ASD情報をスクレイピングで取得" # プレースホルダー

def generate_comparison(scenario):
    prompt = f"Compare how a person with and without ADHD/ASD might handle this scenario: {scenario}"
    response = openai.Completion.create(engine="text-davinci-002", prompt=prompt, max_tokens=150)
    return response.choices[0].text.strip()

def get_adhd_hack(scenario):
    url = "https://adhd-asd-information.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # ここでスクレイピングロジックを実装
    # 例: return soup.find('p', class_='adhd-hack').text
    return "ADHD/ASDのハックをスクレイピングで取得" # プレースホルダー

def generate_explanation(hack, comparison):
    prompt = f"Explain why this hack is necessary for people with ADHD/ASD: {hack}. Compare it with the typical experience: {comparison}"
    response = openai.Completion.create(engine="text-davinci-002", prompt=prompt, max_tokens=200)
    return response.choices[0].text.strip()

def generate_similar_scenario(prev_scenario):
    prompt = f"Generate a similar scenario to this, but with slight variations: {prev_scenario}"
    response = openai.Completion.create(engine="text-davinci-002", prompt=prompt, max_tokens=100)
    return response.choices[0].text.strip()

if __name__ == "__main__":
    app.run(debug=True)