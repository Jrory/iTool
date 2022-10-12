import requests, re, json, datetime

temp_date = datetime.datetime.now()  # 获取当前时间 年月日时分秒
print(temp_date, type(temp_date))

for i in range(1):
    date = (temp_date + datetime.timedelta(days=-1745)).strftime("%Y-%m-%d")  # 获取当前日期的前一天日期

    url = "http://sentence.iciba.com/index.php?callback=jQuery19002826870162613464_1665562221583&c=dailysentence&m=getdetail&title=" + date + "&_=1665562221597"
    r = requests.get(url)
    result_list = re.findall(r"[(](.*?)[)]", r.text)
    result = json.loads(result_list [0])

    print(result["title"], ":", result["content"], "->" , result["note"])
