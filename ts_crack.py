# coding: utf-8
import time
import MySQLdb
import re
import random
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


#连接数据库
conn = MySQLdb.connect(host='localhost', user='root', passwd='123456', db='test', port=3306, charset='utf8') 
cur = conn.cursor()

BORDER = 6
INIT_LEFT = 60


class CrackGeetest():
    def __init__(self):
        self.url = 'http://www.jsgsj.gov.cn:58888/province/jiangsu.jsp'
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 10)
        
    def __del__(self):
        self.browser.close()
    
    def get_geetest_button(self):
        """
        获取初始验证按钮
        :return:
        """
        button = self.wait.until(EC.element_to_be_clickable((By.ID, 'popup-submit')))
        return button
    
    def get_position(self):
        """
        获取验证码位置
        :return: 验证码位置元组
        """
        img = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'gt_fullbg')))
        time.sleep(2)
        location = img.location
        size = img.size
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size[
            'width']
        return (int(top), int(bottom), int(left), int(right))
    
    def get_screenshot(self):
        """
        获取网页截图
        :return: 截图对象
        """
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot
    
    def get_slider(self):
        """
        获取滑块
        :return: 滑块对象
        """
        slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'gt_slider_knob')))
        return slider
    
    def get_geetest_image(self, name):
        """
        获取验证码图片
        :return: 图片对象
        """
        top, bottom, left, right = self.get_position()
        #print('验证码位置', top, bottom, left, right)
        screenshot = self.get_screenshot()
        captcha = screenshot.crop((left, top, right, bottom))
        captcha.save(name)
        return captcha
    
    def open(self):
        """
        打开网页输入企业名称
        :return: None
        """
        self.epname = EPNAME
        self.browser.maximize_window() #最大化窗口
        self.browser.get(self.url)
        epname = self.wait.until(EC.presence_of_element_located((By.ID, 'name')))
        epname.send_keys(self.epname)
    
    def get_gap(self, image1, image2):
        """
        获取缺口偏移量
        :param image1: 不带缺口图片
        :param image2: 带缺口图片
        :return:
        """
        left = 60
        for i in range(left, image1.size[0]):
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j):
                    left = i
                    return left
        return left
    
    def is_pixel_equal(self, image1, image2, x, y):
        """
        判断两个像素是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 取两个图片的像素点
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        threshold = 60
        if abs(pixel1[0] - pixel2[0]) < threshold and abs(pixel1[1] - pixel2[1]) < threshold and abs(
                pixel1[2] - pixel2[2]) < threshold:
            return True
        else:
            return False
    
    def get_track(self, distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        m1 = random.uniform(9,10)
        m2 = m1 + 4
        #减速阈值
        mid = distance * m1 / m2
        # 计算间隔
        t = random.uniform(0.1,0.2)
        # 初速度
        v = 0

        #ax = random.uniform(3,4)
        ax = 2.2
        
        while current < distance:
            if current < mid:
                # 加速度为正2
                #a = 2.2
                a = ax
            else:
                # 加速度为负3
                #a = -3.3
                a = ax - 5
            # 初速度v0
            v0 = v
            # 当前速度v = v0 + at
            v = v0 + a * t
            # 移动距离
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
        return track
    
    def move_to_gap(self, slider, track):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in track:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(1)
        ActionChains(self.browser).release().perform()
    
    def login(self):
        """
        登录
        :return: None
        """
        submit = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'login-btn')))
        submit.click()
        time.sleep(10)
        print('登录成功')

    def dboperate(self):
        pageSource = self.browser.page_source
        idsarray = re.findall(r'org=(.*?)&amp;id=(.*?)&amp;seqId=(.*?)&amp.*?detailClicLog\(\'(.*?)\',\'(.*?)\'\).*?<p class="biaozhu01 bz.*?">(.*?)<',pageSource, re.S)
        if(len(idsarray) <> 0):
            for ids in idsarray:
                orgid = ids[0]
                dataid = ids[1]
                seqid = ids[2]
                regno = ids[3]
                real_epname = ids[4]
                epstatus = ids[5]
                
                cur.execute("update js_eplist set status = 1 where id = %s  ",(idid) )
                sqlids = "insert into js_codelist(epid,epname,orgid,dataid,seqid,regno,real_epname,epstatus) values(%s,%s,%s,%s,%s,%s,%s,%s)"   
                paramids = (epid,EPNAME,orgid,dataid,seqid,regno,real_epname,epstatus)
                cur.execute(sqlids,paramids)
        else:
            cur.execute("update js_eplist set status = 2 where id = %s  ",(idid) )
    
    def crack(self,fortime):
        # 输入用户名密码
        self.open()
        time.sleep(2)
        # 点击搜索按钮
        button = self.get_geetest_button()
        button.click()
        time.sleep(1)
        # 获取验证码图片
        image1 = self.get_geetest_image('captcha1.png')
        # 点按呼出缺口
        slider = self.get_slider()
        slider.click()
        time.sleep(2)
        # 获取带缺口的验证码图片
        image2 = self.get_geetest_image('captcha2.png')
        # 获取缺口位置
        gap = self.get_gap(image1, image2)
        # 减去缺口位移
        gap -= BORDER
        # 获取移动轨迹
        track = self.get_track(gap)
        # 拖动滑块
        self.move_to_gap(slider, track)
        # 判断是否验证成功
        try:
            success = self.wait.until(EC.text_to_be_present_in_element((By.ID, 'toal'), u'用时'))
        except:
            success = False
            fortime = fortime - 1
            if(fortime > 0 ):
                self.crack(fortime)
        
        
        if(success == True):
            self.dboperate()
            print u"采集完成"
        else:
            print u"采集失败"

if __name__ == '__main__':

    #查询企业列表
    n = cur.execute("select * from js_eplist where status='0' order by area")
    crack = CrackGeetest()
    for row in cur.fetchall():
        #time.sleep(1)
        idid = row[0] #id
        epid = row[1] #id
        EPNAME = row[2] #企业名称
        fortime = 5
       # try:
        crack.crack(fortime)
        #except:
        #    continue