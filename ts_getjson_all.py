# coding: utf-8
from urllib import quote
from urllib import unquote
from cookielib import CookieJar
import json
import MySQLdb
import urllib2,urllib
import httplib2
import ssl
import gzip
import StringIO
import time
import random
import requests

ssl._create_default_https_context = ssl._create_unverified_context #免验证书

#连接数据库
conn = MySQLdb.connect(host='localhost', user='root', passwd='dejaxcdb', db='test', port=3306, charset='utf8') 
cur = conn.cursor()

#head信息
header = {
        'Host': 'www.jsgsj.gov.cn:58888',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Cookie': 'JSESSIONID=WvZMhKqhvjmC0hypXQqPxG7jF3Q2qyLL1MDZM5C73QJchZlLKyQG!1707413951; BIGipServerpool_gsp=3456018624.24585.0000'
    }


#--------------------自定义函数开始-----------------------

#GET获取数据
def getRequestData(header,url):
    http = httplib2.Http()
    response,value = http.request(url, 'GET', headers=header)
    requestdata = [response,value]
    return requestdata

#解决网络阻塞问题，根据情况循环获取
#maxnum 循环获取此数据
def solveblock(maxnum,req):
    Max_Num1 = maxnum
    epvalue = ''
    for x in range(Max_Num1):
        try:
            epvalue = urllib2.urlopen(req,timeout=5).read()
            break
        except:
            if x < Max_Num1-1:
                continue
            else:
                print 'URLError: <urlopen error timed out> All times is failed '

    return epvalue

def getvaluetimes(time,req):
    Max_Num1 = time
    epvalue = ''
    for x in range(Max_Num1):
        try:
            epvalue = urllib2.urlopen(req,timeout=12).read()
            print epvalue
            valuelen = len(epvalue)
            if( valuelen > 70):
                break
            else:
                continue
        except:
            if x < Max_Num1-1:
                continue
            else:
                print 'URLError: <urlopen error timed out> All times is failed '

    if( len(epvalue) < 70 ):
        epvalue = 'gsjsb'
        
    return epvalue


#gzip数据解码
def changeToJsondata(loginResult):
    compressedstream = StringIO.StringIO(loginResult)
    gzipper = gzip.GzipFile(fileobj=compressedstream)
    eplistdata = gzipper.read()
    print eplistdata
    substart = eplistdata.find(r'[{')
    subend = eplistdata.find(r'}]')
    eplistdata = eplistdata[substart:(subend+2)]

    return eplistdata

#urlcode转换函数
def changecode(value):
    value = str(value).replace('u\'','\'')
    valuechange = value.decode("unicode-escape")
    return valuechange

#访问时间间隔，范围从a秒至b秒
def sleeplength(a,b):
    sleeplenth = random.uniform(a,b)
    time.sleep(sleeplenth)

def getReqDataTimes(maxnum,header,valueurl,msg,times):
    epvalue = ''
    for x in range(maxnum):
        sleeplength(times,times) #沉睡2秒
        try:
            requestepvalue = getRequestData(header,valueurl)
            epvalue = requestepvalue[1]
            epvaluelength = requestepvalue[0]['content-length']
            if int(epvaluelength) > 10000:
               break
        except:
            print msg
            continue
        
    return epvalue

#普通获取
def getreqValue(url,header):
    req = urllib2.Request(url,headers = header)
    value = urllib2.urlopen(req).read()
    return value

#当前日期时间
def nowDate():
    nowdate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return nowdate


#--------------------自定义函数结束-----------------------#


#查询企业列表
n = cur.execute("select * from eplistcode where status='0' and area='南京'")

#根网址
baseurl = "http://www.jsgsj.gov.cn:58888/ecipplatform/"

#循环企业列表
for row in cur.fetchall():

    sleeplength(0.2,0.5)
    
    idid = row[0] #id
    epid = row[1]  #epid
    area = row[3] #地区
    entname = row[4] #企业名称
    dataid = row[5]  #dataid
    seqid = row[6]  #seqid
    orgid = row[7]  #orgid
    corpname = row[8]  #采集到的实际企业名称
    regno = row[9]  #统一社会信用代码/注册号
    uniscid = row[10]  #注册号
    admitmain = row[17]  #Admit_main
    collecttime = nowDate() #当前时间
    print entname
    corpname = corpname.encode('utf-8') #设置utf-8编码
    
    #营业执照信息
    baseinfourl = baseurl + "publicInfoQueryServlet.json?pageView=true&org="+ orgid +"&id="+ dataid +"&seqId="+ seqid +"&abnormal=&activeTabId="
    
    baseinforeq = urllib2.Request(baseinfourl, headers = header)
    baseinfo_json = solveblock(5,baseinforeq)

    if( len(baseinfo_json) > 100 ):
        status = 1
    else:
        #如果无法采集到数据，则查询seqlist表，逐个排查，直到采集到数据，否则采集失败
        seqidlist = cur.execute("select seqid from seqidlist")
        for seqidarray in cur.fetchall():
            seqid = seqidarray[0]
            baseinfourl = baseurl + "publicInfoQueryServlet.json?pageView=true&org="+ orgid +"&id="+ dataid +"&seqId="+ seqid +"&abnormal=&activeTabId="
            baseinforeq = urllib2.Request(baseinfourl, headers = header)
            baseinfo_json = solveblock(5,baseinforeq)
            
            if( len(baseinfo_json) > 100 ):
                status = 1
                break
            else:
                status = 2
    
    if status == 2:
        continue
    
    #获取regNo
    jsonload = json.loads(baseinfo_json)
    regnocode = jsonload["REG_NO_EN"]

    #更新eplistcode标的regnocode和seqid
    cur.execute("update eplistcode set regnocode = %s,seqid = %s where id = %s  ",(regnocode,seqid,idid) )
    
    isexistdataid = cur.execute("select * from epjson where dataid = %s",(dataid)) #判断是否已存在该记录
    if isexistdataid == 0:
        #插入营业执照信息
        sqlbaseinfo = "insert into epjson(epid,area,entname,dataid,seqid,orgid,corpname,regno,uniscid,baseinfo,collecttime) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        paramcbaseinfo = (epid,area,entname,dataid,seqid,orgid,corpname,regno,uniscid,baseinfo_json,collecttime)
        cur.execute(sqlbaseinfo,paramcbaseinfo)
        #print "baseinfo got successed"
    else:
        #更新营业执照信息
        sqlbaseinfo = cur.execute("update epjson set baseinfo = %s, collecttime = %s where  dataid = %s ",(baseinfo_json,collecttime,dataid))
        #print "baseinfo update successed"
    #标记状态为1
    cur.execute("update eplistcode set status = 1 where id = %s  ",(idid))
   
    #股东及出资信息
    stockinfourl = baseurl + "publicInfoQueryServlet.json?queryGdcz=true&org="+orgid+"&id="+dataid+"&seqId="+seqid+"&abnormal=&activeTabId=&tmp=&regNo="+regnocode+"&admitMain="+admitmain+"&pageSize=200&curPage=1&sortName=&sortOrder="
    try:
        #stockinfo_json = getreqValue(stockinfourl, header)
        stockinforeq = urllib2.Request(stockinfourl, headers = header)
        stockinfo_json = solveblock(5,stockinforeq)
    except:
        print "stockinfo got failed"
        cur.execute("update eplistcode set status = 2,collectdes=if(collectdes is null,'stockinfo got failed',concat(collectdes,',','stockinfo got failed')) where id = %s  ",(idid))
        continue
    
    cur.execute("update epjson set stockinfo = %s where dataid = %s",(stockinfo_json, dataid))
    #print "stockinfo got successed"
    
    #主要人员信息
    staffinfourl = baseurl + "publicInfoQueryServlet.json?queryZyry=true&org="+orgid+"&id="+dataid+"&seqId="+seqid+"&abnormal=&activeTabId=&tmp=&regNo="+regnocode+"&admitMain=" + admitmain
    try:
        #staffinfo_json = getreqValue(staffinfourl, header)
        staffinforeq = urllib2.Request(staffinfourl, headers = header)
        staffinfo_json = solveblock(5,staffinforeq)
    except:
        print "staffinfo got failed"
        cur.execute("update eplistcode set status = 2,collectdes=if(collectdes is null,'staffinfo got failed',concat(collectdes,',','staffinfo got failed')) where id = %s  ",(idid))
        continue
    
    cur.execute("update epjson set staffinfo = %s where dataid = %s",(staffinfo_json, dataid))
    #print "staffinfo got successed"

    #分支机构信息
    branchinfourl = baseurl + "publicInfoQueryServlet.json?queryFzjg=true&org="+orgid+"&id="+dataid+"&seqId="+seqid+"&abnormal=&activeTabId=&tmp=&regNo="+regnocode+"&admitMain="+admitmain
    try:
        #branchinfo_json = getreqValue(branchinfourl, header)
        branchinforeq = urllib2.Request(branchinfourl, headers = header)
        branchinfo_json = solveblock(5,branchinforeq)
    except:
        print "branchinfo got failed"
        cur.execute("update eplistcode set status = 2,collectdes=if(collectdes is null,'branchinfo got failed',concat(collectdes,',','branchinfo got failed')) where id = %s  ",(idid))
        continue
    
    cur.execute("update epjson set branchinfo = %s where dataid = %s",(branchinfo_json, dataid))
    #print "branchinfo got successed"

    #变更信息
    changeinfourl = baseurl + "publicInfoQueryServlet.json?queryBgxx=true&org="+orgid+"&id="+dataid+"&seqId="+seqid+"&abnormal=&activeTabId=&tmp=&regNo="+regnocode+"&admitMain="+admitmain+"&pageSize=200&curPage=1&sortName=&sortOrder="
    try:
        #changeinfo_json = getreqValue(changeinfourl, header)
        changeinforeq = urllib2.Request(changeinfourl, headers = header)
        changeinfo_json = solveblock(5,changeinforeq)
    except:
        print "changeinfo got failed"
        cur.execute("update eplistcode set status = 2,collectdes=if(collectdes is null,'changeinfo got failed',concat(collectdes,',','changeinfo got failed')) where id = %s  ",(idid))
        continue
    
    cur.execute("update epjson set changeinfo = %s where dataid = %s",(changeinfo_json, dataid))
    #print "changeinfo got successed"

    #经营异常信息
    jyycinfourl = baseurl + "publicInfoQueryServlet.json?queryJyyc=true&org="+orgid+"&id="+dataid+"&seqId="+seqid+"&abnormal=&activeTabId=&tmp=&regNo="+regnocode+"&admitMain="+admitmain+"&pageSize=200&curPage=1&sortName=&sortOrder="
    try:
        #jyycinfo_json = getreqValue(jyycinfourl, header)
        jyycinforeq = urllib2.Request(jyycinfourl, headers = header)
        jyycinfo_json = solveblock(5,jyycinforeq)
    except:
        print "jyycinfo got failed"
        cur.execute("update eplistcode set status = 2,collectdes=if(collectdes is null,'jyycinfo got failed',concat(collectdes,',','jyycinfo got failed')) where id = %s  ",(idid))
        continue
    
    cur.execute("update epjson set jyycinfo = %s where dataid = %s",(jyycinfo_json, dataid))
    #print "jyycinfo got successed"

    #年报列表
    anreportlisturl = baseurl + "publicInfoQueryServlet.json?queryQynbxxYears=true&org="+orgid+"&id="+dataid+"&seqId="+seqid+"&abnormal=&activeTabId=&tmp=&regNo="+regnocode+"&admitMain="+admitmain
    try:
        #anreportlist_json = getreqValue(anreportlisturl, header)
        anreportlistreq = urllib2.Request(anreportlisturl, headers = header)
        anreportlist_json = solveblock(5,anreportlistreq)
    except:
        print "anreportlist got failed"
        cur.execute("update eplistcode set status = 2,collectdes=if(collectdes is null,'anreportlist got failed',concat(collectdes,',','anreportlist got failed')) where id = %s  ",(idid))
        continue
    
    cur.execute("update epjson set anreportlist = %s where dataid = %s",(anreportlist_json, dataid))
    #print "anreportlist got successed"
    
cur.close()
conn.close()
