import asyncio
import glob
import os
import time
import uuid
from pathlib import Path

from graia.application import GraiaMiraiApplication
from graia.application.friend import Friend
from graia.application.group import Group, Member
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import At, Plain, Image
from graia.application.session import Session
from graia.broadcast import Broadcast
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 机器人APP初始化，不用管
bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host="http://localhost:8080",  # 这里填一个http服务器的地址和端口号，配置文件有写
        authKey="123456789",  # 填入 authKey，配置文件有写
        account=2953331668,  # 你的机器人的 qq 号，登录再填
        websocket=True  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    )
)

# 好友发给你消息的时候所执行的回调
@bcc.receiver("FriendMessage")
async def friend_message_listener(app: GraiaMiraiApplication, friend: Friend):
    await app.sendFriendMessage(friend, MessageChain.create([
        Plain("Hello, World!")
    ]))

# 移除一些网站的遮挡
def removeMask(browser:webdriver.Chrome):
    browser.execute_script("""
    var element = document.querySelector("#sign_in-bg");
    if (element)
        element.parentNode.removeChild(element);
    """)
    browser.execute_script("""
    var element = document.querySelector("#sign_in");
    if (element)
        element.parentNode.removeChild(element);
    """)
    browser.execute_script("""
    var elements = document.getElementsByTagName("button");
    if (elements.length)
    {
        for(var i = 0;i<elements.length;i++)
        {
            if(elements[i].innerText=="I Agree")
            {
                elements[i].click();
            }
        }
    }
    """)

def SearchAndCapture(search_site):
    # selenium访问，无头模式：
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280,720')
    browser = webdriver.Chrome(chrome_options=chrome_options)
    browser.get(search_site)
    removeMask(browser)
    browser.execute_script("document.body.style.zoom='1.2'")
    time.sleep(0.5)  # 这里休眠一小下，因为执行放大的时候需要一些时间，这样截图能不会截到它放大到一半的过程

    # 处理截图
    capture_filename_raw = ""
    capture_filename_final = ""
    unique_seq = str(uuid.uuid1())
    capture_filename_raw = "result_" + unique_seq + ".png"
    capture_filename_final = "final_result_" + unique_seq + ".jpg"
    browser.get_screenshot_as_file(capture_filename_raw)
    browser.close()

    # 调用个小程序压缩一下图片，降低分辨率，不然发得太慢了
    os.system("ffmpeg.exe -i " + capture_filename_raw + " " + capture_filename_final)
    return capture_filename_final

def SearchAndListen(song):
    song_filename_raw = ""
    song_filename_final = ""
    unique_seq = str(uuid.uuid1())
    song_filename_raw = "output_"+unique_seq
    song_filename_final = "final_output_" + unique_seq + ".mp3"
    os.system("youtube-dl --proxy 127.0.0.1:1080 -x \"ytsearch:" + song + "\" -o " + song_filename_raw + ".%(ext)s")
    print(glob.glob(song_filename_raw + "*")[0])
    # 调用个小程序剪切，40s开始剪切50S，并转码成mp3格式
    os.system("ffmpeg -ss 00:00:40 -i " + glob.glob(song_filename_raw + "*")[0] + " -t 00:00:40 -codec mp3 " + song_filename_final)

    return song_filename_final

# 收到群消息后所执行的回调
@bcc.receiver("GroupMessage")
async def group_message_listener(
        message: MessageChain,
        app: GraiaMiraiApplication,
        group: Group,
        member: Member,
        saying: MessageChain):
    # search:
    index_google = saying.asDisplay().find("帮谷歌下")
    index_baidu = saying.asDisplay().find("帮百度下")
    index_pic_google = saying.asDisplay().find("帮谷歌图片下")
    index_pic_baidu = saying.asDisplay().find("帮百度图片下")
    index_wiki = saying.asDisplay().find("帮维基下")
    index_song = saying.asDisplay().find("帮听下")
    search_site = ""

    if group.id == 1023914918:
        if message.has(At):
            objs = message.get(At)
            for obj in objs:
                if obj.target == 2953331668:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Image.fromLocalFile("punch.jpg")
                    ]))
                    return
        else:
            if index_song != -1:
                try:
                    song = saying.asDisplay()[3:]
                    song_name = SearchAndListen(song)
                    voice = Path(song_name).read_bytes()
                    await app.sendGroupMessage(group, MessageChain.create([
                        await app.uploadVoice(voice)
                    ]))
                finally:
                    os.system("del output_*")
                    os.system("del final_output_*")
                    return
            elif index_baidu != -1:
                search_site = "http://www.baidu.com/s?wd=" + saying.asDisplay()[4:]
            elif index_google != -1:
                search_site = "http://www.google.com/search?q=" + saying.asDisplay()[4:]
            elif index_wiki != -1:
                search_site = "https://zh.wikipedia.org/wiki/" + saying.asDisplay()[4:]
            elif index_pic_baidu != -1:
                search_site = "https://image.baidu.com/search/index?tn=baiduimage&fm=result&ie=utf-8&word=" + saying.asDisplay()[6:]
            elif index_pic_google != -1:
                search_site = "https://www.google.com/search?tbm=isch&source=hp&biw=2560&bih=1329&q=" + saying.asDisplay()[6:]
            elif saying.asDisplay() == "看下BBC":
                search_site = "https://www.bbc.com/"
            elif saying.asDisplay() == "看下泰晤士":
                search_site = "https://www.thetimes.co.uk/"
            elif saying.asDisplay() == "看下路透社":
                search_site = "https://www.reuters.com/"
            elif saying.asDisplay() == "看下cnn":
                search_site = "https://edition.cnn.com/"
            else:
                return
            try:
                imgname = SearchAndCapture(search_site)
                # 发送图片消息
                await app.sendGroupMessage(group, MessageChain.create([
                    Image.fromLocalFile(imgname)
                ]))
            finally:
                os.system("del result_*")
                os.system("del final_result_*")

app.launch_blocking()
