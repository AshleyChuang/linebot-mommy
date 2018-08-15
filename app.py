from flask import Flask, request, abort
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
import json

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    FollowEvent,MessageEvent, PostbackEvent, TextMessage, TextSendMessage,TemplateSendMessage, ButtonsTemplate,
    PostbackTemplateAction, MessageTemplateAction,
    URITemplateAction, DatetimePickerTemplateAction,
    ConfirmTemplate, CarouselTemplate, CarouselColumn,
    ImageCarouselTemplate, ImageCarouselColumn,
    RichMenu,RichMenuSize, RichMenuArea, RichMenuBounds,
    BubbleContainer,FlexSendMessage, CarouselContainer
)

template_env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['json'])
)

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('MIhM1rtBQmPWHHUG0P6WT/q9sOeoe9PTM3NdfLOnI74qp4DtLTHR0WQydDUFbxe868ae78yTpWcRsVQSZJ2FWtV7w+Zqy+Uzomv0jKYFUia8+yT6DKKNd2InF61rFJlQWoPfgeaLzCfQ+JDRNIGFxQdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('c80566dca51b314332768ca929117904')

@handler.add(FollowEvent)
def handle_follow(event):
    buttons_template = ButtonsTemplate(
        type='buttons', title="歡迎加入寶寶說",
        text='bla bla bla',
        actions=[uri_template = URITemplateAction(type = 'uri',label='Picture', uri="line://app/1599707218-4898LaxV")]
        )
    message = TemplateSendMessage(
        type = 'template', alt_text="Welcome",
        template=buttons_template
        )
    line_bot_api.reply_message(event.reply_token, message)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def baby_talk():
    template = template_env.get_template('flex_example.json')
    data = template.render(hello="yoyo")
    data = eval(data)
    flex_message = FlexSendMessage(alt_text='tag',contents=BubbleContainer.new_from_json_dict(data))
    return flex_message

def social_media():


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #print(event.source.user_id)
    profile = line_bot_api.get_profile(event.source.user_id)
    user_name = profile.display_name
    if event.message.text == "寶寶":
        flex_message = baby_talk()
        line_bot_api.reply_message(event.reply_token, flex_message)
    elif event.message.text == "紀錄":
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text="Jack還在寫啦"))
    elif event.message.text == "社群":
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text="沒有合作對象謝謝"))
    elif event.message.text == "資訊":
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text="請自己去google"))
    elif event.message.text == "設定":
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text="沒東西可設定"))
    else:
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=event.message.text))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    #crawl_index_movie()
    app.run(host='0.0.0.0', port=port)
