from flask import Flask, request, abort
import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    FollowEvent,MessageEvent, PostbackEvent, TextMessage, TextSendMessage,TemplateSendMessage, ButtonsTemplate,
    PostbackTemplateAction, MessageTemplateAction,
    URITemplateAction, DatetimePickerTemplateAction,
    ConfirmTemplate, CarouselTemplate, CarouselColumn,
    ImageCarouselTemplate, ImageCarouselColumn,
    RichMenu,RichMenuSize, RichMenuArea, RichMenuBounds
)

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('MIhM1rtBQmPWHHUG0P6WT/q9sOeoe9PTM3NdfLOnI74qp4DtLTHR0WQydDUFbxe868ae78yTpWcRsVQSZJ2FWtV7w+Zqy+Uzomv0jKYFUia8+yT6DKKNd2InF61rFJlQWoPfgeaLzCfQ+JDRNIGFxQdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('c80566dca51b314332768ca929117904')
lst_rich_menu_obj = line_bot_api.get_rich_menu_list()
for rich_menu_obj in lst_rich_menu_obj:
    line_bot_api.delete_rich_menu(rich_menu_obj.rich_menu_id)
rich_menu_to_create = RichMenu(
    size=RichMenuSize(width=2500,height=1686),
    selected=False,
    name="nice richmenu",
    chat_bar_text="touch me",
    areas=[
    RichMenuArea(RichMenuBounds(x=0,y=0,width=624,height=1686),URITemplateAction(uri='line://nv/location')),
    RichMenuArea(RichMenuBounds(x=624,y=0,width=938,height=843),URITemplateAction(uri='line://nv/location')),
    RichMenuArea(RichMenuBounds(x=624,y=421.5,width=938,height=843),URITemplateAction(uri='line://nv/location')),
    RichMenuArea(RichMenuBounds(x=938,y=0,width=938,height=843),URITemplateAction(uri='line://nv/location')),
    RichMenuArea(RichMenuBounds(x=938,y=421.5,width=938,height=843),URITemplateAction(uri='line://nv/location'))
    ])
rich_menu_id = line_bot_api.create_rich_menu(rich_menu_to_create)
f = open('pic.jpg', 'r+')
jpgdata = f.read()
line_bot_api.set_rich_menu_image(rich_menu_to_create, 'image/jpeg', jpgdata)
print(rich_menu_id)
print(len(line_bot_api.get_rich_menu_list()))

@handler.add(FollowEvent)
def link_rich_menu(event):
    print("link rich menu")
    line_bot_api.link_rich_menu_to_user(event.source.user_id, rich_menu_id)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    #app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #print(event.source.user_id)
    profile = line_bot_api.get_profile(event.source.user_id)
    user_name = profile.display_name
    line_bot_api.reply_message(event.reply_token,TextSendMessage(text=event.message.text))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    #crawl_index_movie()
    app.run(host='0.0.0.0', port=port)
