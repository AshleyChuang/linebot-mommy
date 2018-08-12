from flask import Flask, request, abort
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

vieshow_url = 'https://www.vscinemas.com.tw/'
hot_url = 'https://www.vscinemas.com.tw/film/hot.aspx'
index_url = 'https://www.vscinemas.com.tw/film/index.aspx'
detail_url_by_id = 'https://www.vscinemas.com.tw/film/detail.aspx?id='
coming_url = 'https://www.vscinemas.com.tw/film/coming.aspx'
theater_url = 'https://www.vscinemas.com.tw/theater/index.aspx'
movie_dict = {}
# movie info by movie id: 0->movie name, 1->image, 2->{theater_id:theater_name}, 3->{theater_id: [ dates "[date, [tuple(time, url)] ]" ]}
theater_info = [] # [{北區}, {竹苗}, {中區}, {南區}]
hot_movie_list = []
usersId = []

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
    ImageCarouselTemplate, ImageCarouselColumn
)
############
def crawl_index_movie():
    r = requests.get(index_url)
    content = r.text
    soup = BeautifulSoup(content, 'html.parser')
    moviePage = soup.find(class_='pagebar').find_all('a', href=True)
    movie_dict.clear();
    for p in moviePage[1:]:
        movieList = soup.find(class_='movieList').find_all('li')
        for m in movieList:
            #movie_name = "%s (%s)" % (m.find('h2').text, m.find('h3').text)
            movie_name = m.find('h2').text
            movie_id = re.search('id=(.*)',m.find('h2').find('a')['href']).group(1)
            movie_info_url = vieshow_url + 'film/' + m.find('h2').find('a')['href']
            movie_start_time = m.find('time').text
            movie_img = m.find('img')['src'].replace('../', vieshow_url)
            #info = [movie_img,movie_start_time, movie_info_url, {}]
            info = [movie_name, movie_img, {}, {}]
            movie_dict[movie_id] = info
        next_page_url = index_url + p['href']
        soup = BeautifulSoup(requests.get(next_page_url).text, 'html.parser')

def crawl_hot_movie():
    r = requests.get(hot_url)
    content = r.text
    soup = BeautifulSoup(content, 'html.parser')
    rank1_id = re.search('id=(.*)',soup.find('section',class_='hotArea').find('a', href=True)['href']).group(1)
    hot_movie_list.append(rank1_id)
    others = soup.find(class_='hotList').find_all('li')
    for movie in others:
        id = re.search('id=(.*)', movie.find('a')['href']).group(1)
        hot_movie_list.append(id)

def search_movie_id(text):
    for movie_id in movie_dict:
        if text in movie_dict[movie_id][0]:
            return movie_id
    return None

def get_trailer_url(url):
    r = requests.get(url)
    content = r.text
    soup = BeautifulSoup(content, 'html.parser')
    movieVideo = soup.find(class_='mainVideo')
    if movieVideo is None:
        return None
    return movieVideo.find('iframe')['src']

def crawl_theater(movie_id):
    url = detail_url_by_id + movie_id
    if len(movie_dict[movie_id][2]) != 0:
        return None
    movie_theater = {}
    r = requests.get(url)
    content = r.text
    soup = BeautifulSoup(content, 'html.parser')
    theaterList = soup.find("ul", {"class": "versionList"}).find("li").find_all("li")
    for i in theaterList:
        t = i.find('a')
        movie_theater[t['href']] = t.text
    movie_dict[movie_id][2] = movie_theater

def crawl_movie_time(movie_id, movie_theater):
    # movie_dict_key=3  -> {theater_id: [ dates "[date, [tuple(time, url)] ]" ]}
    all_times_in_theaters = [] # element: [date, [tuple]]
    url = detail_url_by_id + movie_id
    r = requests.get(url)
    content = r.text
    soup = BeautifulSoup(content, 'html.parser')
    movie_times = soup.find("article", {"id": movie_theater[1:]})
    if movie_times is None:
        return []
    movieDays = movie_times.find_all("div", {"class": "movieDay"})
    dates = [] # date -> times&urls
    for day in movieDays:
        date2times = []
        #dates.append(date)
        date = day.find("h4").text
        date = date.replace('年', '/').replace('月', '/').replace('日', '/',1)
        date2times.append(date)
        dates.append(date)
        sessions = day.find("ul", {"class": "bookList"}).find_all("li")
        timesessions = []
        for sess in sessions:
            time_session = sess.find('a')
            time = time_session.text
            if "soldout" in sess.attrs['class']:
                continue
            booking_url = time_session['href']
            timesessions.append( (time, booking_url) )
        date2times.append(timesessions)
        all_times_in_theaters.append(date2times)
    movie_dict[movie_id][3][movie_theater] = all_times_in_theaters
    return dates

def crawl_theater_info():
    r = requests.get(theater_url)
    content = r.text
    soup = BeautifulSoup(content, 'html.parser')
    areaList = soup.find_all('ul', class_='theaterInfoList')
    for area in areaList:
        theaters = area.find_all('li')
        theaters_in_area = {}
        for t in theaters:
            img = t.find('img')['src'].replace('../', vieshow_url)
            name = t.find('h2').find('a').text
            address = t.find('p').text
            theaters_in_area[name] = [img, address]
        theater_info.append(theaters_in_area)
def crawl_movie_info(movie_id):
    url = detail_url_by_id + movie_id
    r = requests.get(url)
    content = r.text
    soup = BeautifulSoup(content, 'html.parser')
    infoArea = soup.find(class_='infoArea')
    if infoArea is None:
        return TextSendMessage(text='抱歉！本電影沒有包含電影資訊')
    table = infoArea.find('table')
    if table is None:
        return TextSendMessage(text='抱歉！本電影沒有包含電影資訊')
    infos = table.find_all('tr')
    info=[]
    for i in infos:
        info.append(''.join(i.find_all(text = True)))
    info_text = ''.join(info)
    return TextSendMessage(text=info_text[0:2000])

def crawl_movie_story(movie_id):
    url = detail_url_by_id + movie_id
    r = requests.get(url)
    content = r.text
    soup = BeautifulSoup(content, 'html.parser')
    story = soup.find(class_='bbsArticle').find('p').find_all(text = True)
    story_text = ''.join(story)
    return TextSendMessage(text=story_text[0:2000])

############
app = Flask(__name__)

# Channel Access Token
#line_bot_api = LineBotApi('bQu1j0/rJMgNGK++uQcD1Pu8zLcB/Gdp3kwwcwrP4Quj33AGyX1wZtTjPmy8TaNTiEgTgbgzGvN7ZMNtBnDPSubZ0waBtV1tLnbRM7x7O0gkO/z165gjVEJ7YvxoBEMLyzjobckPsfnw5Ncb6hH1fQdB04t89/1O/w1cDnyilFU=')
line_bot_api = LineBotApi('MIhM1rtBQmPWHHUG0P6WT/q9sOeoe9PTM3NdfLOnI74qp4DtLTHR0WQydDUFbxe868ae78yTpWcRsVQSZJ2FWtV7w+Zqy+Uzomv0jKYFUia8+yT6DKKNd2InF61rFJlQWoPfgeaLzCfQ+JDRNIGFxQdB04t89/1O/w1cDnyilFU=')
# Channel Secret
#handler = WebhookHandler('756c8ca2e53d032ae70d8e1cb6624294')
handler = WebhookHandler('c80566dca51b314332768ca929117904')

# 監聽所有來自 /callback 的 Post Request
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

def get_movie_template(movie_id):
    if movie_id is None:
        return TextSendMessage(text="沒有這個電影耶～查查看別的吧！")
    movie_name = movie_dict[movie_id][0]
    movie_pic = movie_dict[movie_id][1]
    movie_url = detail_url_by_id + movie_id
    movie_trailer = get_trailer_url(movie_url)
    if movie_trailer is None:
        uri_template = URITemplateAction(type = 'uri',label='Picture', uri=movie_pic)
    else:
        uri_template = URITemplateAction(type = 'uri',label='Trailer', uri=movie_trailer)
    buttons_template = ButtonsTemplate(
        type='buttons', title=movie_name[0:40],
        text='Check out more information for the movie!',
        thumbnail_image_url = movie_pic,
        actions=[
        PostbackTemplateAction(label='Movie Info', data='movie=%s&action=3&'%movie_id),
        PostbackTemplateAction(label='Movie Story', data='movie=%s&action=6&'%movie_id),
        uri_template,
        PostbackTemplateAction(label='Show Times', data='movie=%s&action=1&'%movie_id)]
        )
    message = TemplateSendMessage(
        type = 'template', alt_text=movie_name,
        template=buttons_template
        )
    return message

def get_hot_movie_list(user_name):
    col = []
    for movie_id in hot_movie_list:
        col.append(ImageCarouselColumn(
                        image_url=movie_dict[movie_id][1],
                        action=PostbackTemplateAction(
                            label='Learn More',
                            data='movie=%s&action=5&' % (movie_id)
                        )
                    ))
    imagecarousel = ImageCarouselTemplate(type='image_carousel',columns=col)
    message = TemplateSendMessage(type='template', alt_text='Hot Movie List', template=imagecarousel)
    return [TextSendMessage(text='哈囉 %s! 這是本週熱門電影喔！可以參考看看～'%(user_name)),message]

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #print(event.source.user_id)
    if event.source.user_id not in usersId:
        usersId.append(event.source.user_id)
    profile = line_bot_api.get_profile(event.source.user_id)
    user_name = profile.display_name
    if '推薦' in event.message.text or '好看' in event.message.text or '熱門' in event.message.text or 'recommend' in event.message.text:
        message = get_hot_movie_list(user_name);
        line_bot_api.reply_message(event.reply_token, message)
    elif 'hi' in event.message.text or 'hello' in event.message.text or '你好' in event.message.text or '嗨' in event.message.text or '哈囉' in event.message.text:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='哈囉 %s! 可以輸入電影關鍵字來查詢電影喔！也可以請我幫你推薦電影喔～'%(user_name)))
    else:
        movie_id = search_movie_id(event.message.text)
        message = get_movie_template(movie_id)
        line_bot_api.reply_message(event.reply_token, message)

def generate_carousel_col(date_times,description, movie_id, movie_theater):
    date = date_times[0]
    times = date_times[1]
    col = CarouselColumn(
            title=date,text=description[0:60],
            actions=[
                PostbackTemplateAction(
                    type='postback',label='Get Show Times',
                    data='movie=%s&action=4&theater=%s&date=%s&slot=0&' %(movie_id, movie_theater, date)
                )
            ]
        )
    return col

def get_movie_times_message(movie_id, movie_theater, movie_date, time_slot):
    if len(movie_dict[movie_id][2]) == 0:
        crawl_theater(movie_id)
    if len(movie_dict[movie_id][3]) == 0:
        crawl_movie_time(movie_id, movie_theater)
    date_times = movie_dict[movie_id][3][movie_theater]
    theater_name = movie_dict[movie_id][2][movie_theater]
    col = []
    description = ''.join(['《',movie_dict[movie_id][0], '》@', theater_name])
    for date in date_times:
        if date[0] == movie_date:
            time_sessions = date[1] # it's an array of show times for the movie in designated theater
            if len(time_sessions) == 0:
                return TextSendMessage(text='哎呀! 目前所有在%s %s的場次 都賣光了耶!' % (theater_name,movie_date))
            for session in time_sessions:
                movie_time = session[0]
                if session[1].startswith('#'):
                    continue
                col.append(CarouselColumn(
                    title=movie_date+' '+movie_time, text=description[0:60],
                    actions=[
                        URITemplateAction(
                            type='uri',
                            label='Booking',
                            uri=session[1]
                        )
                    ]
                ))
            break
    if len(col) <= 10:
        #print("<=10!!!", len(col))
        ca_temp = CarouselTemplate(type='carousel',columns=col)
        return TemplateSendMessage(type='template', alt_text='Show Times', template=ca_temp)
    col_array = [col[i:i+10] for i  in range(0, len(col), 10)]
    message = []
    for c in col_array:
        message.append(TemplateSendMessage(type='template', alt_text='Show Times', template=CarouselTemplate(columns=c)))
    return message[0:5]

def get_theater_carousel(movie_id, theaters, movie_name):
    text_message = ['《',movie_name,'》目前有在以下的威秀影城播出喔！選擇您想要的影城吧～\n']
    col = []
    for t in theaters:
        for i in range(0,len(theater_info)):
            if theaters[t] in theater_info[i]:
                theater_img_add = theater_info[i][theaters[t]]
                break
        col.append(CarouselColumn(
            title=theaters[t], text=theater_img_add[1],
            thumbnail_image_url=theater_img_add[0],
            actions=[
                PostbackTemplateAction(
                    label='See Movie Here',
                    data='movie=%s&action=2&confirm=1&theater=%s&'%(movie_id, t)
                )
            ]
        ))
    if len(col) <=10:
        carousel_temp = CarouselTemplate(type='carousel', columns=col)
        return [TextSendMessage(text=''.join(text_message)),TemplateSendMessage(type='template',alt_text='Choose Theater',template=carousel_temp)]
    else :
        temp1 = TemplateSendMessage(type='template',alt_text='Choose Theater',template=CarouselTemplate(type='carousel', columns=col[:10]))
        temp2 = TemplateSendMessage(type='template',alt_text='Choose Theater',template=CarouselTemplate(type='carousel', columns=col[10:]))
    return [TextSendMessage(text=''.join(text_message)),temp1, temp2]


@handler.add(PostbackEvent)
def handle_message(event):
    movie_id = re.search('movie=(.+?)&',event.postback.data).group(1)
    action_type = re.search('&action=(.+?)&',event.postback.data).group(1)
    movie_name = movie_dict[movie_id][0]
    ## action: 1->電影院 , 2->只有一個電影院 (confirm-> 1:yes, 0:no), 4->
    #if action_type == '1':
    if action_type == '1':
        crawl_theater(movie_id)
        theaters = movie_dict[movie_id][2]
        if len(theaters) == 1:
            # confirm template
            theater = next(iter(theaters))
            text = '《%s》目前只有在以下的威秀影城播岀喔！想要得到更詳細的場次嗎？' %(movie_name)
            confirm_template = ConfirmTemplate(
                type = 'confirm', text= theaters[theater],
                actions=[
                    PostbackTemplateAction(
                        type = 'postback',
                        label='Yes',
                        data='movie=%s&action=2&confirm=1&theater=%s&' %(movie_id, theater)
                    ),
                    PostbackTemplateAction(
                        type = 'postback',
                        label='No',
                        data='movie=%s&action=2&confirm=0&' %(movie_id)
                    )
                ]
            )
            message = TemplateSendMessage(
                type='template',
                alt_text='Confirmation',
                template=confirm_template
            )
            line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=text),message])
        else:
            message = get_theater_carousel(movie_id, theaters, movie_name)
            line_bot_api.reply_message(event.reply_token, message)
    elif action_type == '2':
        confirm_type = re.search('&confirm=(.+?)&',event.postback.data).group(1)
        if confirm_type == '1':
            # 用carousel來分上午下午晚上
            movie_theater = re.search('&theater=(.+?)&',event.postback.data).group(1)
            crawl_movie_time(movie_id, movie_theater)
            movie_days = movie_dict[movie_id][3][movie_theater] # [date_times,...]
            if len(movie_days) <= 0:
                line_bot_api.reply_message(event.reply_token, [
                TextSendMessage(text="抱歉！找不到任何在這個影城的場次...試試看其他電影吧！"),#"Sorry! Can't find any movie times in the theater. Try another movie!"
                TextSendMessage(text='可以用關鍵字來找其他的電影呦～')])
            else:
                movie_days_col = []
                if len(movie_dict[movie_id][2]) == 0:
                    crawl_theater(movie_id)
                description = ''.join(['《',movie_name, '》@', movie_dict[movie_id][2][movie_theater]])
                for date_times in movie_days:
                    col = generate_carousel_col(date_times, description, movie_id, movie_theater)
                    movie_days_col.append(col)
                carousel_template = CarouselTemplate(tyep='carousel', columns=movie_days_col)
                carousel_template_message = TemplateSendMessage(type = 'template',alt_text='Select Moive Dates',template=carousel_template)
                line_bot_api.reply_message(event.reply_token, carousel_template_message)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='可以用關鍵字來找其他的電影呦～'))
    elif action_type == '3':
        message = crawl_movie_info(movie_id)
        line_bot_api.reply_message(event.reply_token, message)
    elif action_type =='4':
        movie_theater = re.search('&theater=(.+?)&',event.postback.data).group(1)
        movie_date = re.search('&date=(.+?)&',event.postback.data).group(1)
        time_slot = re.search('&slot=(.+?)&',event.postback.data).group(1)
        message = get_movie_times_message(movie_id, movie_theater, movie_date, time_slot)
        #message = TextSendMessage(text='test')
        line_bot_api.reply_message(event.reply_token, message)
    elif action_type == '5':
        # display movie info from hot movie List
        line_bot_api.reply_message(event.reply_token, get_movie_template(movie_id))
    elif action_type == '6':
        message = crawl_movie_story(movie_id)
        line_bot_api.reply_message(event.reply_token, message)
crawl_index_movie()
crawl_theater_info()
crawl_hot_movie()
'''
sched = BlockingScheduler()
i=0
def my_job():
    print("hi")
    print(i)
    i += 1
    if len(usersId) !=0:
        line_bot_api.multicast(['U84434259e4dcdd16ea11fd37a358b6e7'], TextSendMessage(text='Hello World!'))

sched.add_job(my_job, 'interval', seconds=5)
sched.start()

def job():
    print('Hi')
    if len(usersId) !=0:
        line_bot_api.multicast(usersId, TextSendMessage(text='Hello World!'))
schedule.every(5).seconds.do(job)
while True:
    schedule.run_pending()
    time.sleep(1)
'''
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    #crawl_index_movie()
    app.run(host='0.0.0.0', port=port)
