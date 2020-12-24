import asyncio
import sys
import time
import capture
import os
import uuid
from pathlib import Path
from graia.broadcast import Broadcast
from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import At, Plain, Image, Voice_LocalFile, Voice, UploadMethods
from graia.application.session import Session
from graia.application.message.chain import MessageChain
from graia.application.group import Group, Member
from graia.application.message.parser.kanata import Kanata
from graia.application.message.parser.signature import FullMatch, OptionalParam, RequireParam

from graia.application.message.elements.internal import Plain, Image
from graia.application.friend import Friend

from selenium import webdriver
loop = asyncio.get_event_loop()


# 机器人APP初始化，不用管
bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host="http://localhost:8080", # 这里填一个http服务器的地址和端口号，配置文件有写
        authKey="123456789", # 填入 authKey，配置文件有写
        account=2953331668, # 你的机器人的 qq 号，登录再填
        websocket=True # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    )
)

# 好友发给你消息的时候所执行的回调
@bcc.receiver("FriendMessage")
async def friend_message_listener(app: GraiaMiraiApplication, friend: Friend):
    await app.sendFriendMessage(friend, MessageChain.create([
        Plain("Hello, World!")
    ]))

# 收到群消息后所执行的回调
@bcc.receiver("GroupMessage")
async def friend_message_listener(
    message: MessageChain,
    app: GraiaMiraiApplication,
    group: Group,
    member: Member,
    saying: MessageChain):

    index_google = saying.asDisplay().find("帮谷歌下")
    index_baidu = saying.asDisplay().find("帮百度下")
    index_wiki  = saying.asDisplay().find("帮维基下")
    search_site = ""
    if group.id == 1023914918 and (index_google != -1 or index_baidu != -1 or index_wiki != -1):
        # 获取搜索地址
        if index_baidu != -1:
            search_site = "http://www.baidu.com/s?wd="+saying.asDisplay()[4:]
        if index_google != -1:
            search_site = "http://www.google.com/search?q="+saying.asDisplay()[4:]
        if index_wiki != -1:
            search_site = "https://zh.wikipedia.org/wiki/" + saying.asDisplay()[4:]

        try:
            # selenium访问：
            browser = webdriver.Chrome()
            browser.set_page_load_timeout(5)
            browser.get(search_site)
            browser.maximize_window()
            browser.execute_script("document.body.style.zoom='1.7'")
            time.sleep(0.5)# 这里休眠一小下，因为执行放大的时候需要一些时间，这样截图能不会截到它放大到一半的过程

            # 处理截图
            unique_seq = str(uuid.uuid1())
            capture_filename_raw = "result_" + unique_seq + ".jpg"
            capture_filename_final = "final_result_" + unique_seq + ".jpg"
            capture.window_capture(capture_filename_raw)
            browser.close()

            # 调用个小程序压缩一下图片，降低分辨率，不然发得太慢了
            os.system("ffmpeg.exe -i " + capture_filename_raw + " -video_size 1280x720 " + capture_filename_final)

            # 发送图片消息
            await app.sendGroupMessage(group, MessageChain.create([
                Image.fromLocalFile(capture_filename_final)
            ]))
        finally:
            os.system("del " + capture_filename_final)
            os.system("del " + capture_filename_raw)
            return
app.launch_blocking()