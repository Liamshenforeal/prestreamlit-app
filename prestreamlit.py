import streamlit as st
import re
import time
import requests
import json
import csv
import pandas as pd
import all_sort
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService


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


def initial():
    global keyword
    keyword = None
    global website
    website = None
    global key
    key = None
    global web
    web = None
    global uploaded_file1
    uploaded_file1 = None
    global uploaded_file2
    uploaded_file2 = None


side_bar = st.sidebar.radio(
    '功能选择',
    ['视频输入', '相关视频搜索','极端群体情绪预测', '预测原因']
)


def show_progress_bar(duration=10):
    with st.empty():
        for percent_complete in range(duration):
            time.sleep(1)
            st.progress(percent_complete + 1)


if side_bar == '视频输入':
    initial()
    st.title('视频输入')
    url = st.text_input('请输入视频地址:')
    keyword = st.text_input('请输入视频关键词，如果不指定关键词，请输入0:')
    if st.button('展示进度'):
        show_progress_bar(5)
    if keyword:
        bv_num = re.findall(r'BV\w+',url)
        BV = ''.join(bv_num)
        time.sleep(0.1)
        video_api = 'https://api.bilibili.com/x/web-interface/view'
        tag_api = 'https://api.bilibili.com/x/tag/archive/tags'
        params = {
            'bvid': BV
        }
        response = requests.get(video_api, params=params, headers=headers)
        response.encoding = 'utf-8-sig'
        videos = json.loads(response.text)
        video = videos['data']
        pic = video['pic']
        picture = requests.get(pic, stream=True)
        with open('封面图片.png', "wb") as png:
            for chunk in picture.iter_content(chunk_size=1024):
                if chunk:
                    png.write(chunk)

        title = video['title']
        try:
            intro1 = video['desc_v2'][0]['raw_text']
            intro = intro1.replace('\n', ' ')
        except:
            intro = '-'

        tag = ''
        response2 = requests.get(tag_api, params=params, headers=headers)
        response2.encoding = 'utf-8-sig'
        tags = json.loads(response2.text)['data']
        for k in tags:
            tag = tag + k['tag_name'] + ' '

        if keyword == '0':
            keyword = title

        with open('预测视频信息.csv', "a+", errors="ignore", newline='', encoding='utf-8') as fp:
            writer = csv.writer(fp, delimiter=';')
            writer.writerow(['标题', '标签', '简介', 'urls', '关键词'])
            writer.writerow([title, tag, intro, url, keyword])


        st.success('预测视频信息已保存')
        st.image('封面图片.png', caption='Example Image', width=400)

if side_bar == '相关视频搜索':
    initial()
    st.title('相关视频搜索')
    file2 = st.file_uploader("请上传预测视频信息文件:")
    if file2 is not None:
        show_progress_bar(10)  # 假设文件处理进度条持续
        st.success('文件上传成功，正在进行搜索...')
        with st.spinner('正在搜索相关视频...'):
            # 假设搜索和处理需要的总时间
            total_time = 10
            progress_bar = st.progress(0)
            for i in range(100):
                # 每个步骤假设耗时相等
                time.sleep(total_time / 100)
                progress_bar.progress(i + 1)
            st.success('搜索完成！')
    else:
        st.error('upload failed!')



    cluster = pd.read_csv(file2, encoding='utf-8', sep=';')
    title = cluster['标题'][0]
    tag = cluster['标签'][0]
    intro = cluster['简介'][0]
    url = cluster['urls'][0]
    keyword = cluster['关键词'][0]

    keyword = keyword.replace('习近平', "")

    # driver.get(url)
    # driver.implicitly_wait(30)

    rec_bvid = []
    match = re.findall(r'BV\w+', url)
    BV = ''.join(match)
    url_related = 'https://api.bilibili.com/x/web-interface/archive/related'
    params = {
        'bvid': BV
    }
    response = requests.get(url_related, params=params, headers=headers)
    response.encoding = 'utf-8-sig'
    rec_video_urls = json.loads(response.text)['data']
    for rec_video_url in rec_video_urls:
        rec_bvid.append(rec_video_url['bvid'])

    keyword_bvid = all_sort.keyword_bv(keyword,BV)
    publisher_bvid= all_sort.publisher_bv(BV,params)

    publisher_data = all_sort.data_crawler(publisher_bvid)
    rec_data = all_sort.data_crawler(rec_bvid)
    keyword_data = all_sort.data_crawler(keyword_bvid)

    video_publisher = all_sort.video_select(publisher_data, title, tag, intro)
    video_keyword = all_sort.video_select(rec_data, title, tag, intro)
    video_rec = all_sort.video_select(keyword_data, title, tag, intro)
    video = pd.concat([video_publisher, video_keyword, video_rec])
    video.to_csv('相关视频信息.csv')

    st.success('相关视频信息已保存')
    data1 = pd.read_csv('相关视频信息.csv', encoding='utf-8', engine="python")
    st.write(data1)


if side_bar == '极端群体情绪预测':
    initial()
    st.title('极端群体情绪预测')
    file3 = st.file_uploader("请上传相关视频信息文件:")
    if file3 is not None:
        show_progress_bar(10)  # 假设情绪预测进度条持续
        st.success('情绪预测完成！')
        with st.spinner('正在进行情绪预测...'):
            # 假设情绪预测的总时间
            total_time = 5
            progress_bar = st.progress(0)
            for i in range(100):
                # 每个步骤假设耗时相等
                time.sleep(total_time / 100)
                progress_bar.progress(i + 1)
            st.success('情绪预测完成！')
    else:
        st.error('upload failed!')

    data2 = pd.read_csv(file3, encoding='utf-8',engine="python")
    video_urls = data2['urls'].values
    vector_list=all_sort.vector_get(video_urls)
    with open('预测视频向量.csv', "a+", errors="ignore", newline='', encoding='utf-8') as fp:
        writer = csv.writer(fp, delimiter=';')
        writer.writerow(['上下文相关-标题-集群密度','上下文相关-标签-集群密度 ','上下文相关-简介-集群密度','大数据相关-标题-集群密度','大数据相关-标签-集群密度','大数据相关-简介-集群密度','内容相关-标题-集群密度',
                         '内容相关-标签-集群密度','内容相关-简介-集群密度','上下文相关-标题-粉丝数','上下文相关-标签-粉丝数','上下文相关-简介-粉丝数','大数据相关-标题-粉丝数','大数据相关-标签-粉丝数',
                         '大数据相关-简介-粉丝数','内容相关-标题-粉丝数','内容相关-标签-粉丝数','内容相关-简介-粉丝数','上下文相关-标题-播放量','上下文相关-标签-播放量','上下文相关-简介-播放量',
                         '大数据相关-标题-播放量','大数据相关-标签-播放量','大数据相关-简介-播放量','内容相关-标题-播放量','内容相关-标签-播放量','内容相关-简介-播放量','上下文相关-标题-热度',
                         '上下文相关-标签-热度','上下文相关-简介-热度','大数据相关-标题-热度','大数据相关-标签-热度','大数据相关-简介-热度','内容相关-标题-热度','内容相关-标签-热度','内容相关-简介-热度'])
        writer.writerow(vector_list)

    vector_list2 = pd.read_csv('预测视频向量.csv', encoding='utf-8', sep=';', engine="python")
    pred=all_sort.model_read(vector_list2)
    if pred==0:
        st.success('此视频会产生极端群体情绪')
    elif pred==1:
        st.success('此视频不会产生极端群体情绪')


if side_bar == '预测原因':
    initial()
    st.title('预测原因')
    file4 = st.file_uploader("请上传向量文件:")
    if file4 is not None:
        st.success('upload success!')
        show_progress_bar(3)  # 假设分析进度条持续
    else:
        st.error('upload failed!')
    vector_list = pd.read_csv(file4, encoding='utf-8', sep=';',engine="python")
    feature_list,pred=all_sort.reason_confer(vector_list)
    if pred[0]==0:
        emotion='会'
    else:
        emotion='不会'
    k="根据与此视频{}，{}最相关的此三个视频的{}特征判断，此视频{}产生极端性群体情绪".format(feature_list[0],feature_list[1],feature_list[2],emotion)
    st.success(k)