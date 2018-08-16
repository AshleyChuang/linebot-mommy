from flask import Flask, request, abort
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
import json
from pprint import pprint
#import article

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    FollowEvent,MessageEvent, PostbackEvent, TextMessage, ImageMessage,
    TextSendMessage,TemplateSendMessage, ButtonsTemplate,
    PostbackTemplateAction, MessageTemplateAction,URITemplateAction,
    ConfirmTemplate, CarouselTemplate, CarouselColumn,
    ImageCarouselTemplate, ImageCarouselColumn,
    RichMenu,RichMenuSize, RichMenuArea, RichMenuBounds,
    BubbleContainer,FlexSendMessage, CarouselContainer,
    StickerMessage, StickerSendMessage,
    QuickReply, QuickReplyButton,
    DatetimePickerAction, PostbackAction, CameraAction, CameraRollAction, LocationAction,MessageAction
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
        actions=[URITemplateAction(type = 'uri',label='初次使用設定', uri="line://app/1599707218-4898LaxV")]
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

#def search_info():
# quick replies
week = 5

def article_fetching():
    template = template_env.get_template('article.json')
    data = template.render(title="lala")
    data = eval(data)
    message = TemplateSendMessage(type='template', alt_text='article', template=CarouselTemplate.new_from_json_dict(data))
    return message

@handler.add(MessageEvent, message=(ImageMessage))
def handle_content_message(event):
    message = article_fetching()
    line_bot_api.reply_message(event.reply_token, message) # carousel

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #print(event.source.user_id)
    profile = line_bot_api.get_profile(event.source.user_id)
    user_name = profile.display_name
    if event.message.text == "寶寶":
        flex_message = baby_talk()
        line_bot_api.reply_message(event.reply_token, flex_message)
    elif event.message.text == "社群":
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text="沒有合作對象謝謝"))
    elif event.message.text == "資訊":
        #search_info()
        template = template_env.get_template('quick_reply.json')
        with open('quick_reply/week%s.json' % (str(week))) as f:
            option = json.load(f)
        data = template.render(option)
        data = eval(data)
        message = TextSendMessage(text='Quick reply', quick_reply=QuickReply.new_from_json_dict(data))
        line_bot_api.reply_message(event.reply_token, message)
    elif event.message.text == "設定":
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text="沒東西可設定"))
    else:
        if event.message.text.startswith("\\"):
            message = article_fetching()
            line_bot_api.reply_message(event.reply_token, message)
        else:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=event.message.text))

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=event.message.package_id,
            sticker_id=event.message.sticker_id)
    )
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    #crawl_index_movie()
    app.run(host='0.0.0.0', port=port)
