from flask import Flask, request, abort
from flask_cors import CORS
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
import json
from pprint import pprint
import datetime

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    FollowEvent,MessageEvent, PostbackEvent, TextMessage, ImageMessage,
    TextSendMessage,TemplateSendMessage, ButtonsTemplate, ImagemapSendMessage, VideoSendMessage, BaseSize,
    PostbackTemplateAction, MessageTemplateAction,URITemplateAction,MessageImagemapAction,ImagemapArea,
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
CORS(app)

# Channel Access Token
line_bot_api = LineBotApi('MIhM1rtBQmPWHHUG0P6WT/q9sOeoe9PTM3NdfLOnI74qp4DtLTHR0WQydDUFbxe868ae78yTpWcRsVQSZJ2FWtV7w+Zqy+Uzomv0jKYFUia8+yT6DKKNd2InF61rFJlQWoPfgeaLzCfQ+JDRNIGFxQdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('c80566dca51b314332768ca929117904')

@handler.add(FollowEvent)
def handle_follow(event):
    print(event.source.user_id)
    template = template_env.get_template('welcome_message.json')
    data = template.render()
    data = eval(data)
    flex_message = FlexSendMessage(alt_text='下次產檢注意事項',contents=BubbleContainer.new_from_json_dict(data))
    line_bot_api.reply_message(event.reply_token, flex_message)

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

@app.route("/send_message", methods=['POST'])
def send_message():
    if not request.content_type == 'application/json':
        abort(401)

    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    if not user_id:
        abort(401)
    print(user_id)
    profile = line_bot_api.get_profile(user_id)
    user_name = profile.display_name
    line_bot_api.push_message(user_id, TextSendMessage(text='Hi %s, %s'%(user_name, message)))
    return 'OK'

@app.route("/reminder", methods=['POST'])
def reminder():
    if not request.content_type == 'application/json':
        abort(401)

    data = request.get_json()
    user_id = data.get('user_id')
    year = data.get('year')
    month = data.get('month')
    date = data.get('date')
    if not user_id:
        abort(401)
    print(user_id)
    profile = line_bot_api.get_profile(user_id)
    user_name = profile.display_name
    #line_bot_api.push_message(user_id, TextSendMessage(text='Hi, %s 媽咪！下次產檢在%s/%s/%s喔～以下為下次產檢的注意事項...bla bla bla' % (user_name, year, month, date)))
    template = template_env.get_template('reminder.json')
    data = template.render(year=year, month=month, date=date)
    data = eval(data)
    flex_message = FlexSendMessage(alt_text='下次產檢注意事項',contents=BubbleContainer.new_from_json_dict(data))
    line_bot_api.push_message(user_id, flex_message)
    return 'OK'

@app.route('/video', methods=['POST'])
def post_video():
    if not request.content_type == 'application/json':
        abort(401)

    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        abort(401)
    print(user_id)
    profile = line_bot_api.get_profile(user_id)
    user_name = profile.display_name
    message = []
    message.append(TextSendMessage(text="寶寶已經七個月囉～%s媽咪來回顧一下寶寶的成長吧！"%(user_name)))
    message.append(VideoSendMessage(
        original_content_url='https://line-mommy-baby.herokuapp.com/static/video2.mp4',
        preview_image_url='https://cdn-b-east.streamable.com/image/kdebf_first.jpg?token=6m7RlkvMHXKg7I-g9fezJA&expires=1534826912'
    ))
    message.append(VideoSendMessage(
        original_content_url='https://line-mommy-baby.herokuapp.com/static/video.mp4',
        preview_image_url='https://cdn-b-east.streamable.com/image/87kji_first.jpg?token=mDniALD2iAqCs1GqZeUDqA&expires=1534827632'
    ))
    line_bot_api.push_message(user_id, message)
    return 'OK'

user2baby_dict = {}

def baby_talk(user_id):
    current_time = datetime.datetime.now()
    print(current_time)
    if user_id in user2baby_dict:
        update_time = user2baby_dict[user_id]
        print(update_time)
        print("timedelta")
        print((current_time - update_time).total_seconds())
        if (current_time - update_time).total_seconds() >= 600:
            user2baby_dict[user_id] = current_time
            file = 'baby_week10.json'
        else:
            file = 'baby_week10_meaningless.json'
    else:
        user2baby_dict[user_id] = current_time
        file = 'baby_week10.json'
    template = template_env.get_template(file)
    data = template.render(hello="yoyo")
    data = eval(data)
    flex_message = FlexSendMessage(alt_text='baby_message',contents=BubbleContainer.new_from_json_dict(data))
    return flex_message

week = 5

def article_fetching(tag):
    files = [filename for filename in os.listdir('./article/') if filename.startswith(tag)]
    col = []
    template = template_env.get_template('article.json')

    for file_name in files:
        print(file_name)
        with open('article/%s'%(file_name)) as f:
            article = json.load(f)
        pprint(article)
        data = template.render(article)
        data = eval(data)
        col.append(BubbleContainer.new_from_json_dict(data))
    message = FlexSendMessage(alt_text='推薦文章', contents=CarouselContainer(contents=col))
    return message

def get_line_group(dir_name):
    files = [filename for filename in os.listdir(dir_name)]
    col = []
    for file_name in files:
        print(file_name)
        with open('%s%s'%(dir_name,file_name)) as f:
            group = json.load(f)
        pprint(group)
        col.append(CarouselColumn(
            title=group.get('title'), text=group.get('description'),
            thumbnail_image_url=group.get('image'),
            actions=[
                URITemplateAction(
                    label='加入群組',
                    uri=group.get('url')
                )
            ]
        ))
    carousel_temp = CarouselTemplate(type='carousel', columns=col[0:10])
    message = TemplateSendMessage(type='template', alt_text='line_group', template=carousel_temp)
    return message

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    user_name = profile.display_name
    print(user_name + " :")
    print(event.source.user_id)
    print(event.message.text)
    if event.message.text == "寶寶":
        flex_message = baby_talk(event.source.user_id)
        line_bot_api.reply_message(event.reply_token, flex_message)
    elif event.message.text == "媽媽論壇":
        print("社群")
        message = []
        message.append(TextSendMessage(text="請選擇想加入的社群分類～"))
        message.append(ImagemapSendMessage(
            base_url="https://i.imgur.com/sNhwbTh.jpg",
            alt_text="This is an imagemap",
            base_size=BaseSize(1040,1040),
            actions=[
                MessageImagemapAction(type='message',text="$素人媽媽", area=ImagemapArea(0, 0, 520, 520)),
                MessageImagemapAction(type='message',text="$醫生", area=ImagemapArea(0, 520, 520, 520)),
                MessageImagemapAction(type='message',text="$部落客", area=ImagemapArea(520, 0, 520, 520)),
                MessageImagemapAction(type='message',text="$其他", area=ImagemapArea(520, 520, 520, 520))
            ]
        ))
        line_bot_api.reply_message(event.reply_token, message)
    elif event.message.text == "大補帖":
        #search_info()
        template = template_env.get_template('quick_reply.json')
        with open('quick_reply/week%s.json' % (str(week))) as f:
            option = json.load(f)
        data = template.render(option)
        data = eval(data)
        message = TextSendMessage(text='請輸入欲搜尋文章的關鍵字～', quick_reply=QuickReply.new_from_json_dict(data))
        line_bot_api.reply_message(event.reply_token, message)
    elif event.message.text.startswith("\\"):
        message = article_fetching((event.message.text).replace("\\", ""))
        line_bot_api.reply_message(event.reply_token, message)
    elif event.message.text.startswith("$"):
        if event.message.text == "$醫生":
            dir_name = './line_group/doctor/'
        elif event.message.text == "$素人媽媽":
            dir_name = './line_group/mommy/'
        elif event.message.text == "$部落客":
            dir_name = './line_group/blogger/'
        elif event.message.text == "$其他":
            dir_name = './line_group/others/'
        message = get_line_group(dir_name)
        line_bot_api.reply_message(event.reply_token,message)

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=event.message.package_id,
            sticker_id=event.message.sticker_id)
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message = article_fetching("孕吐")
    line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    #crawl_index_movie()
    app.run(host='0.0.0.0', port=port)
