from flask import Flask, request, abort
import os
import base64

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

@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text='Got follow event'))

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
    bubble = BubbleContainer(
            direction='ltr',
            hero=ImageComponent(
                url='https://example.com/cafe.jpg',
                size='full',
                aspect_ratio='20:13',
                aspect_mode='cover',
                action=URIAction(uri='http://example.com', label='label')
            ),
            body=BoxComponent(
                layout='vertical',
                contents=[
                    # title
                    TextComponent(text='Brown Cafe', weight='bold', size='xl'),
                    # review
                    BoxComponent(
                        layout='baseline',
                        margin='md',
                        contents=[
                            IconComponent(size='sm', url='https://example.com/gold_star.png'),
                            IconComponent(size='sm', url='https://example.com/grey_star.png'),
                            IconComponent(size='sm', url='https://example.com/gold_star.png'),
                            IconComponent(size='sm', url='https://example.com/gold_star.png'),
                            IconComponent(size='sm', url='https://example.com/grey_star.png'),
                            TextComponent(text='4.0', size='sm', color='#999999', margin='md',
                                          flex=0)
                        ]
                    ),
                    # info
                    BoxComponent(
                        layout='vertical',
                        margin='lg',
                        spacing='sm',
                        contents=[
                            BoxComponent(
                                layout='baseline',
                                spacing='sm',
                                contents=[
                                    TextComponent(
                                        text='Place',
                                        color='#aaaaaa',
                                        size='sm',
                                        flex=1
                                    ),
                                    TextComponent(
                                        text='Shinjuku, Tokyo',
                                        wrap=True,
                                        color='#666666',
                                        size='sm',
                                        flex=5
                                    )
                                ],
                            ),
                            BoxComponent(
                                layout='baseline',
                                spacing='sm',
                                contents=[
                                    TextComponent(
                                        text='Time',
                                        color='#aaaaaa',
                                        size='sm',
                                        flex=1
                                    ),
                                    TextComponent(
                                        text="10:00 - 23:00",
                                        wrap=True,
                                        color='#666666',
                                        size='sm',
                                        flex=5,
                                    ),
                                ],
                            ),
                        ],
                    )
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='sm',
                contents=[
                    # callAction, separator, websiteAction
                    SpacerComponent(size='sm'),
                    # callAction
                    ButtonComponent(
                        style='link',
                        height='sm',
                        action=URIAction(label='CALL', uri='tel:000000'),
                    ),
                    # separator
                    SeparatorComponent(),
                    # websiteAction
                    ButtonComponent(
                        style='link',
                        height='sm',
                        action=URIAction(label='WEBSITE', uri="https://example.com")
                    )
                ]
            ),
        )
    return FlexSendMessage(alt_text="hello", contents=bubble)


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
