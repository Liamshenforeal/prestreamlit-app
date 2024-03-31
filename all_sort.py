import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import requests
import json
import time
import re
import xgboost as xgb
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
import numpy as np
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

service = ChromeService(executable_path=ChromeDriverManager().install())
chrome_options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=chrome_options)


headers = {
    'authority': 'api.bilibili.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    # 需定期更换cookie，否则location爬不到
    'cookie': "i-wanna-go-back=-1; header_theme_version=CLOSE; nostalgia_conf=-1; CURRENT_PID=48e7c380-d774-11ed-b043-a76171efa2f7; DedeUserID=3493136064056111; DedeUserID__ckMd5=0d65c5fa36863cf3; enable_web_push=DISABLE; hit-dyn-v2=1; CURRENT_BLACKGAP=0; fingerprint=8edb046d8598423e594ff305a0f49ace; buvid_fp_plain=undefined; CURRENT_FNVAL=4048; PVID=1; buvid3=2E4C2934-913D-2351-4300-3AEE113D4B6E07674infoc; b_nut=1705226307; b_ut=7; _uuid=9C2A5519-5E41-10CC1-99CE-BB32EF9E735B37279infoc; buvid_fp=42e68d1839873d3b0a85e26bc2fd2619; buvid4=EEA57664-EEA9-B54E-B6AF-3F09F8E51E1208443-024011409-HJwPMewZWLS8kLGKMCXTQA%3D%3D; rpdid=|(k|YumYuluu0J'u~|Yk)|)Y~; home_feed_column=4; CURRENT_QUALITY=0; bp_video_offset_3493136064056111=908667290013139012; browser_resolution=1327-756; FEED_LIVE_VERSION=V_WATCHLATER_PIP_WINDOW3; b_lsid=49482795_18E8D87D57B; bsource=search_bing; SESSDATA=094fd50b%2C1727323475%2C61487%2A31CjDpL5Za4XTa-9OrvC3naXRPD2ZyX-9bnJPyF4EIjc3YtdUdUsfdS6luEyQNGAMsbTMSVkd2dDNHZDdIaUJ6bkh0RTJIV0UyZUlFSjVXbHlsR1ZlOGFfYWpoeFJWUTd1SzhJV2c5WG5ScmFpU2J1M3VqN1d6Wk4wMEdTbFhSVDBqZzUxUzlJTHNnIIEC; bili_jct=3a03a34244cb1923cf32fb1f863a81c5; sid=78gn4u1u; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTIwMzA2NzYsImlhdCI6MTcxMTc3MTQxNiwicGx0IjotMX0.n5HBM6pi3-OwuOVBIyd94eiD6eUwnOqhGvuhuEPlBks; bili_ticket_expires=1712030616",
    'origin': 'https://www.bilibili.com',
    'referer': 'https://www.bilibili.com/video/BV1FG4y1Z7po/?spm_id_from=333.337.search-card.all.click&vd_source=69a50ad969074af9e79ad13b34b1a548',
    'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47'
}


def calculate_similarity(sentence1, sentence2,method):
    # 分词
    if method =='标签':
        seg_list1 = sentence1.split()
        seg_list2 = sentence2.split()
    else:
        seg_list1 = jieba.lcut(sentence1)
        seg_list2 = jieba.lcut(sentence2)

    # 构建TF-IDF向量
    corpus = [' '.join(seg_list1), ' '.join(seg_list2)]
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(corpus)

    # 计算余弦相似性
    similarity = cosine_similarity(tfidf)[0][1]
    return similarity


def related_sort(data,method,sentence2):
    score=[]
    #data.loc[len(data)] = data.columns
    sours = data[method]
    for sentence in sours:
        similarity = calculate_similarity(sentence, sentence2,method)
        score.append(similarity)
    return score

def video_select(data,title,tag,intro):
    data.drop(data[data['标题'] == title].index, inplace=True)
    data_score1 = related_sort(data, '标题', title)
    data_score2 = related_sort(data, '标签', tag)
    data['标题分数'] = data_score1
    data['标签分数'] = data_score2
    data_title = data.sort_values('标题分数', ascending=False).iloc[:3]
    data_tag = data.sort_values('标签分数', ascending=False).iloc[:3]
    if intro == '-':
        data = data[data['简介'] == '-']
        data_intro = data.iloc[:3]
    else:
        data_score3 = related_sort(data, '简介', tag)
        data['简介分数'] = data_score3
        data_intro = data.sort_values('简介分数', ascending=False).iloc[:3]

    data_video = pd.concat([data_title, data_tag, data_intro])
    return data_video

def data_crawler(aid_list):

    data=pd.DataFrame(columns=['urls','标题','标签','简介'])
    url = 'https://api.bilibili.com/x/web-interface/view'
    url_tag='https://api.bilibili.com/x/tag/archive/tags'
    for i in range(0,len(aid_list)):
        time.sleep(1)
        params = {
                'bvid': str(aid_list[i])
            }
        response = requests.get(url, params=params, headers=headers)
        response.encoding = 'utf-8-sig'
        videos = json.loads(response.text)
        video=videos['data']
        title = video['title']
        try:
            intro1 = video['desc_v2'][0]['raw_text']
            intro = intro1.replace('\n', ' ')
        except:
            intro='-'

        tag=''
        response2 = requests.get(url_tag, params=params, headers=headers)
        response2.encoding = 'utf-8-sig'
        tags = json.loads(response2.text)['data']
        for k in tags:
            tag=tag+k['tag_name']+' '

        data.loc[i] = [aid_list[i], title, tag, intro]
    return data


def vector_get(video_urls):
    cluster = []
    fans = []
    play = []
    hot = []

    for url_related in video_urls:
        bv_num = re.findall(r'BV\w+', url_related)
        BV2 = ''.join(bv_num)
        time.sleep(0.1)
        api = 'https://api.bilibili.com/x/web-interface/view'
        params = {
            'bvid': BV2
        }
        response2 = requests.get(api, params=params, headers=headers)
        response2.encoding = 'utf-8-sig'
        videos2 = json.loads(response2.text)
        video2 = videos2['data']

        view = video2['stat']['view']
        danmaku = video2['stat']['danmaku']
        reply = video2['stat']['reply']
        favorite = video2['stat']['favorite']
        coin = video2['stat']['coin']
        share = video2['stat']['share']
        like = video2['stat']['like']

        mid = video2['owner']['mid']
        users = requests.get(f'https://api.bilibili.com/x/relation/stat?vmid={mid}', headers=headers)
        users.encoding = 'utf-8-sig'
        users = json.loads(users.text)['data']
        user_fans = users['follower']

        cluster.append(like + reply)
        fans.append(user_fans)
        play.append(view)
        hot.append(0.4 * coin + 0.2 * favorite + 0.2 * share + 0.2 * danmaku)

    vector_list = []

    for h in range(0, len(cluster), 3):
        group = cluster[h:h + 3]
        average = sum(group) / 3
        vector_list.append(average)
    for h in range(0, len(fans), 3):
        group = fans[h:h + 3]
        average = sum(group) / 3
        vector_list.append(average)
    for h in range(0, len(play), 3):
        group = play[h:h + 3]
        average = sum(group) / 3
        vector_list.append(average)
    for h in range(0, len(hot), 3):
        group = hot[h:h + 3]
        average = sum(group) / 3
        vector_list.append(average)

    return vector_list

def model_read(vector_list):
    loaded_model = xgb.XGBClassifier()
    loaded_model.load_model("xgb_model.model")
    y_pred = loaded_model.predict(vector_list)
    return y_pred

def reason_confer(vector_list):
    loaded_model = xgb.XGBClassifier()
    loaded_model.load_model("xgb_model.model")
    y_pred = loaded_model.predict(vector_list)
    feature_importances = loaded_model.feature_importances_
    author=[0, 1, 2, 9, 10, 11, 18, 19, 20, 27, 28, 29]
    rec=[3, 4, 5, 12, 13, 14, 21, 22, 23, 30, 31, 32]
    key=[6, 7, 8, 15, 16, 17, 24, 25, 26, 33, 34, 35]
    title=[0, 3, 6, 9, 12, 15, 21, 24, 27, 30, 33, 18]
    tag=[1, 4, 7, 10, 13, 16, 22, 25, 28, 31, 34, 19]
    intro=[2, 5, 8, 11, 14, 17, 23, 26, 29, 32, 35, 20]
    cluster=[0, 1, 2, 3, 4, 5, 6, 7, 8]
    fans=[9, 10, 11, 12, 13, 14, 15, 16, 17]
    play=[18, 19, 20, 21, 22, 23, 24, 25, 26]
    hot=[27, 28, 29, 30, 31, 32, 33, 34, 35]
    feature_list=[]
    k=np.argmax(feature_importances)
    if k in author:
        feature_list.append('上下文相关')
    if k in rec:
        feature_list.append('大数据相关')
    if k in key:
        feature_list.append('内容相关')
    if k in title:
        feature_list.append('标题')
    if k in tag:
        feature_list.append('标签')
    if k in intro:
        feature_list.append('简介')
    if k in cluster:
        feature_list.append('集群密度')
    if k in fans:
        feature_list.append('粉丝数')
    if k in play:
        feature_list.append('播放量')
    if k in hot:
        feature_list.append('热度')
    return feature_list,y_pred

def keyword_bv(keyword,BV):
    keyword_bvid = []
    for k in range(1, 4):
        b_url = f"https://search.bilibili.com/video?keyword={keyword}&duration=0&page={k}"
        driver.get(b_url)
        driver.implicitly_wait(10)
        for j in range(1, 30):
            try:
                key_video_url = driver.find_element(By.XPATH,
                                                    f"/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]/div[{j}]/div/div[2]/div/div/a").get_attribute(
                    'href')

                bv_num = re.findall(r'BV\w+', key_video_url)
                x = ''.join(bv_num)
                if x == '' or x == BV:
                    continue
                else:
                    keyword_bvid.append(x)
            except:
                break
    return keyword_bvid


def publisher_bv(BV,params):
    publisher_bvid = []
    video_api = 'https://api.bilibili.com/x/web-interface/view'
    response = requests.get(video_api, params=params, headers=headers)
    response.encoding = 'utf-8-sig'
    videos = json.loads(response.text)
    video = videos['data']
    mid = video['owner']['mid']
    driver.get('https://space.bilibili.com/' + str(mid) + '/video')
    time.sleep(20)
    page = int(driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div/div/div[2]/div[2]/a[1]/span").text) // 30
    for p in range(1, page + 1):
    #for p in range(1,5):
        driver.get('https://space.bilibili.com/{}/video?tid=0&pn={}&keyword=&order=pubdate'.format(mid,p))
        driver.implicitly_wait(10)
        for v in range(0, 30):
            url_publisher_video = driver.find_element(By.XPATH,
                                                      "/html/body/div[2]/div[4]/div/div/div[2]/div[4]/div/div/ul[2]/li[{}]/a[2]".format(
                                                          v + 1)).get_attribute('href')
            match = re.findall(r'BV\w+', url_publisher_video)
            if BV==''.join(match):
                continue
            else:
                publisher_bvid.append(''.join(match))
    return publisher_bvid