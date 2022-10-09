from qt_core import *
from gui.widgets import *
from time import *

from gui.widgets.py_list_widget.py_list_widget import PyListWidget
from gui.uis.windows.main_window.functions_main_window import *

# IMPORT SETTINGS
# ///////////////////////////////////////////////////////////////
from gui.core.json_settings import Settings

# IMPORT THEME COLORS
# ///////////////////////////////////////////////////////////////
from gui.core.json_themes import Themes

import os, threading, inspect, ctypes, youtube_dl, webbrowser, json
from concurrent.futures import ThreadPoolExecutor

class DownLoader(QThread):
    """docstring for DownLoader"""
    infoSignal = Signal(dict)
    downloadSignal = Signal(dict)
    def __init__(self, max_add_workers = 1,max_download_workers = 3):
        super().__init__()
        self.add_workers = ThreadPoolExecutor(max_add_workers)
        self.download_workers = ThreadPoolExecutor(max_download_workers)
        self.run_task_list = list()
        self.wait_task_dict = dict()

    def _async_stop(self, tid, exctype):
        print("_async_raise: ", tid)
        if not inspect.isclass(exctype):  # 检查exctype对象，是不是类。是类返回True，不是类返回False
            exctype = type(exctype)
        res=ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def getIdent(self, url):
        for i in range(len(self.run_task_list)):
            if self.run_task_list[i]["data"]["url"] == url:
                if self.run_task_list[i]["ident"] > 0:
                    return i, self.run_task_list[i]["ident"]
        return None

    def stopTask(self, taskParam):
        result = self.getIdent(taskParam['url'])
        if result:
            self._async_stop(result[1], SystemExit)
            del self.run_task_list[result[0]]
        else:
            if taskParam['url'] in self.wait_task_dict.keys():
                future = self.wait_task_dict[taskParam['url']]
                if future:
                    future.cancle()
                    del(self.wait_task_dict[taskParam['url']])

    def runTask(self, taskType, taskParam):
        if taskType == 0:
            future = self.add_workers.submit(self.extract_info, taskParam)
            future.add_done_callback(self.get_result)
        else:
            future = self.download_workers.submit(self.download, taskParam)
            future.add_done_callback(self.get_result)

        if not self.getIdent(taskParam['url']):
            self.wait_task_dict[taskParam['url']] = future

    def get_result(self, future):
        for i in range(len(self.run_task_list)):
            if self.run_task_list[i]["ident"] == future.result():
                del self.run_task_list[i]

    def hook(self, d):
        save_path = "./iToolDownload/video"
        if d["status"] == "finished":
            precent_value = 100.0
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            os.rename(d["filename"], os.path.join(save_path, d["filename"]))
        else:
            precent_value = float(d['_percent_str'].strip("%"))

            # {'status': 'downloading', 'downloaded_bytes': 8069343, 'total_bytes': 18819771, 'tmpfilename': 'VUOAszEiR8I.mp4.part', 'filename': 'VUOAszEiR8I.mp4', 'eta': 201, 'speed': 53334.97284900934, 'elapsed': 0.717207670211792, '_eta_str': '03:21', '_percent_str': ' 42.9%', '_speed_str': '52.08KiB/s', '_total_bytes_str': '17.95MiB'}
        self.downloadSignal.emit({"value": precent_value, "filepath": save_path})

    def download(self, taskParam):
        task = {"ident": threading.current_thread().ident, "data": taskParam}
        print("download  ident:",threading.current_thread().ident, ", param: ", taskParam)

        self.run_task_list.append(task)

        # 定义某些下载参数
        ydl_opts = {
            'format' : 'best',
            'progress_hooks': [self.hook],
            'outtmpl': '%(id)s.%(ext)s',
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            # 下载给定的URL列表
            result = ydl.download([taskParam["url"]])

        return result

    def extract_info(self, taskParam):
        task = {"ident": threading.current_thread().ident, "data": taskParam}
        print("extract_info  ident:",threading.current_thread().ident, ", param: ", taskParam)

        self.run_task_list.append(task)

        ydl_opts = {}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            # extract_info 提取信息  id, title(标题), duration(时长), webpage_url(视频地址), thumbnail(缩略图), upload_date(上传日期)
            result = ydl.extract_info(taskParam["url"], download=False)
            data = {"id": result["id"], "title": result["title"], "duration": result["duration"], "webpage_url": result["webpage_url"], "thumbnail": result["thumbnail"], "upload_date": result["upload_date"], "process": 0}

        self.infoSignal.emit(data)
        return threading.current_thread().ident

class Card(QWidget):
    def __init__(self, data, parent, list_item):
        super(Card, self).__init__()
        self.data = data
        self.themes = parent.themes
        self.central_widget = parent.central_widget
        self.downloader = parent.downloader
        self.parent = parent
        self.list_item = list_item
        self.initUI()

    def initUI(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5,0,5,0)

        self.logo_svg = QSvgWidget()
        self.logo_svg.setMaximumWidth(24)
        self.logo_svg.setMaximumHeight(24)
        self.logo_svg.load(Functions.set_svg_image("logo_top_100x22.svg"))
        self.layout.addWidget(self.logo_svg)

        self.title_label = QLabel()
        self.title_label.setContentsMargins(5,0,5,0)
        self.title_label.setMaximumWidth((self.width() - 200) * 0.5)
        self.title_label.setAlignment(Qt.AlignVCenter)
        self.title_label.setStyleSheet(f'font: 12pt "Segoe UI"')
        metrics = QFontMetrics(self.title_label.font())
        show_title = metrics.elidedText(self.data["title"] ,Qt.ElideMiddle, self.title_label.width())
        self.title_label.setText(show_title)
        self.layout.addWidget(self.title_label)

        self.duration_label = QLabel()
        self.duration_label.setContentsMargins(5,0,5,0)
        self.duration_label.setMaximumWidth(70)
        self.duration_label.setAlignment(Qt.AlignVCenter)
        self.duration_label.setStyleSheet(f'font: 10pt "Segoe UI"')
        self.duration_label.setText(strftime("%H:%M:%S", gmtime(self.data["duration"])))
        self.layout.addWidget(self.duration_label)

        self.progress = PyCircularProgress(
            value = self.data["process"],
            progress_width = 4,
            is_rounded = False,
            progress_color = self.themes["app_color"]["pink"],
            text_color = self.themes["app_color"]["white"],
            font_size = 6,
            bg_color = self.themes["app_color"]["bg_three"]
        )
        self.title_label.setMaximumWidth((self.width() - 120) * 0.5)
        self.layout.addWidget(self.progress)

        icon_path = Functions.set_svg_icon("icon_download.svg") if self.data["process"] < 100.0 else Functions.set_svg_icon("icon_dir.svg")
        self.download_button = PyIconButton(
            icon_path = icon_path,
            parent = self.central_widget,
            app_parent = self.central_widget,
            tooltip_text = "DownLoad",
            width = 32,
            height = 32,
            radius = 16,
            dark_one = self.themes["app_color"]["dark_one"],
            icon_color = self.themes["app_color"]["icon_color"],
            icon_color_hover = self.themes["app_color"]["icon_hover"],
            icon_color_pressed = self.themes["app_color"]["icon_active"],
            icon_color_active = self.themes["app_color"]["icon_active"],
            bg_color = self.themes["app_color"]["dark_four"],
            bg_color_hover = self.themes["app_color"]["dark_three"],
            bg_color_pressed = self.themes["app_color"]["white"],
            is_original = True
        )
        self.download_button.clicked.connect(lambda :self.download({"url": str(self.data["webpage_url"]),}))

        self.download_button.setMaximumWidth(32)
        self.download_button.setMaximumHeight(32)
        self.layout.addWidget(self.download_button)

        self.delete_button = PyIconButton(
            icon_path = Functions.set_svg_icon("icon_del.svg"),
            parent = self.central_widget,
            app_parent = self.central_widget,
            tooltip_text = "Delete",
            width = 32,
            height = 32,
            radius = 16,
            dark_one = self.themes["app_color"]["dark_one"],
            icon_color = self.themes["app_color"]["icon_color"],
            icon_color_hover = self.themes["app_color"]["icon_hover"],
            icon_color_pressed = self.themes["app_color"]["icon_active"],
            icon_color_active = self.themes["app_color"]["icon_active"],
            bg_color = self.themes["app_color"]["dark_four"],
            bg_color_hover = self.themes["app_color"]["dark_three"],
            bg_color_pressed = self.themes["app_color"]["white"],
            is_original = True
        )
        self.delete_button.clicked.connect(lambda :self.delete({"url": str(self.data["webpage_url"]),}))

        self.delete_button.setMaximumWidth(32)
        self.delete_button.setMaximumHeight(32)
        self.layout.addWidget(self.delete_button)

        self.link_button = PyIconButton(
            icon_path = Functions.set_svg_icon("icon_link.svg"),
            parent = self.central_widget,
            app_parent = self.central_widget,
            tooltip_text = "Link",
            width = 32,
            height = 32,
            radius = 16,
            dark_one = self.themes["app_color"]["dark_one"],
            icon_color = self.themes["app_color"]["icon_color"],
            icon_color_hover = self.themes["app_color"]["icon_hover"],
            icon_color_pressed = self.themes["app_color"]["icon_active"],
            icon_color_active = self.themes["app_color"]["icon_active"],
            bg_color = self.themes["app_color"]["dark_four"],
            bg_color_hover = self.themes["app_color"]["dark_three"],
            bg_color_pressed = self.themes["app_color"]["white"],
            is_original = True
        )
        self.link_button.clicked.connect(lambda :self.link({"url": str(self.data["webpage_url"]),}))

        self.link_button.setMaximumWidth(32)
        self.link_button.setMaximumHeight(32)
        self.layout.addWidget(self.link_button)

    def link(self, data):
        webbrowser.open(data['url'])

    def delete(self, data):
        if self.download_button._set_icon_path == Functions.set_svg_icon("icon_pause.svg"):
            self.download()
        self.parent.del_card(self.list_item, self.data["webpage_url"])

    def update_process(self, data):
        self.progress.set_value(data['value'])
        self.data["process"] = data['value']
        if data['value'] == 100.0:
            self.download_button.set_icon(Functions.set_svg_icon("icon_dir.svg"))
            self.data["filepath"] = data['filepath']

    def download(self, data):
        if self.download_button._set_icon_path == Functions.set_svg_icon("icon_pause.svg"):
            self.download_button.set_icon(Functions.set_svg_icon("icon_download.svg"))
            self.downloader.stopTask(data)
        elif self.download_button._set_icon_path == Functions.set_svg_icon("icon_download.svg"):
            self.download_button.set_icon(Functions.set_svg_icon("icon_pause.svg"))
            self.downloader.downloadSignal.connect(self.update_process)
            self.downloader.runTask(1, {"url": self.data["webpage_url"]})
        elif self.download_button._set_icon_path == Functions.set_svg_icon("icon_dir.svg"):
            print(self.data['filepath'])
            cmd = "start explorer " + self.data['filepath']
            os.system(cmd.replace("/", "\\"))

class HomePage(object):
    """docstring for HomePage"""
    def __init__(self, page_name):
        print("HomePage")
        self.page_name = page_name

        # LOAD SETTINGS
        # ///////////////////////////////////////////////////////////////
        settings = Settings()
        self.settings = settings.items

        # LOAD THEME COLOR
        # ///////////////////////////////////////////////////////////////
        themes = Themes()
        self.themes = themes.items

        self.setupUi()

        self.downloader = DownLoader(1, 3)

        self.card_list = list()
        self.download_task_list = list()
        self.path = './data/download.json'
        self.load_download_file()

    def load_download_file(self):
        if os.path.exists(self.path) and os.path.getsize(self.path):
            with open(self.path,'r',encoding='utf8')as fp:
                result = json.load(fp)
                for data in result:
                    self.add_card(data, False)

    def save_download_file(self):
        if not os.path.exists(os.path.dirname(self.path)):
            os.mkdir(os.path.dirname(self.path))

        save_data = []
        for card in self.card_list:
            save_data.append(card.data)
        with open(self.path, "w", encoding='utf-8') as f:
            f.write(json.dumps(save_data, ensure_ascii=False, indent=4, separators=(',', ':')))

    def setupUi(self):
        self.page = QWidget()
        self.page.setObjectName(self.page_name)
        self.page.setStyleSheet(u"QFrame { font-size: 16pt;}")

        self.page_layout = QVBoxLayout(self.page)
        self.page_layout.setSpacing(5)
        self.page_layout.setObjectName(u"page_2_layout")
        self.page_layout.setContentsMargins(5, 5, 5, 5)

        self.scroll_area = QScrollArea(self.page)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setStyleSheet(u"background: transparent;")
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)

        self.contents = QWidget()
        self.contents.setObjectName(u"contents")
        self.contents.setGeometry(QRect(0, 0, 840, 580))
        self.contents.setStyleSheet(u"background: transparent;")

        self.verticalLayout = QVBoxLayout(self.contents)
        self.verticalLayout.setSpacing(15)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)

        self.row_1_layout = QHBoxLayout()
        self.row_1_layout.setObjectName(u"row_1_layout")
        self.verticalLayout.addLayout(self.row_1_layout)

        self.row_2_layout = QVBoxLayout()
        self.row_2_layout.setObjectName(u"row_2_layout")
        self.verticalLayout.addLayout(self.row_2_layout)

        self.scroll_area.setWidget(self.contents)
        self.page_layout.addWidget(self.scroll_area)

        # PY LINE EDIT
        self.line_edit = PyLineEdit(
            text = "",
            place_holder_text = "place enter download url",
            radius = 8,
            border_size = 2,
            color = self.themes["app_color"]["text_foreground"],
            selection_color = self.themes["app_color"]["white"],
            bg_color = self.themes["app_color"]["dark_one"],
            bg_color_active = self.themes["app_color"]["dark_three"],
            context_color = self.themes["app_color"]["context_color"]
        )
        self.line_edit.setMinimumHeight(30)

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet(f'''
            font: {self.settings["font"]["text_size"]}pt "{self.settings["font"]["family"]}";
            color: {self.themes["app_color"]["text_foreground"]};
        ''')

        self.search_button = PyIconButton(
            icon_path = Functions.set_svg_icon("icon_search.svg"),
            parent = self.central_widget,
            app_parent = self.central_widget,
            tooltip_text = "Add Task",
            width = 32,
            height = 32,
            radius = 16,
            dark_one = self.themes["app_color"]["dark_one"],
            icon_color = self.themes["app_color"]["icon_color"],
            icon_color_hover = self.themes["app_color"]["icon_hover"],
            icon_color_pressed = self.themes["app_color"]["icon_active"],
            icon_color_active = self.themes["app_color"]["icon_active"],
            bg_color = self.themes["app_color"]["dark_four"],
            bg_color_hover = self.themes["app_color"]["dark_three"],
            bg_color_pressed = self.themes["app_color"]["pink"],
            is_original = True
        )

        self.search_button.clicked.connect(self.add_task)

        self.list_widget = PyListWidget(
            radius = 12,
            color = self.themes["app_color"]["bg_one"],
            selection_color = self.themes["app_color"]["bg_three"],
            bg_color = self.themes["app_color"]["bg_two"],
            bottom_line_color = self.themes["app_color"]["bg_three"],
            grid_line_color = self.themes["app_color"]["bg_one"],
            scroll_bar_bg_color = self.themes["app_color"]["bg_one"],
            scroll_bar_btn_color = self.themes["app_color"]["dark_four"],
            context_color = self.themes["app_color"]["context_color"]
        )

        self.row_1_layout.addWidget(self.line_edit)
        self.row_1_layout.addWidget(self.search_button)
        self.row_2_layout.addWidget(self.list_widget)

    def close_all_task(self):
        for card in self.card_list:
            card.downloader.stopTask({"url": card.data["webpage_url"]})
        self.save_download_file()

    def del_card_list(self, webpage_url):
        for i in range(len(self.card_list)):
            if self.card_list[i].data["webpage_url"] == webpage_url:
                del self.card_list[i]
        self.save_download_file()

    def del_card(self, item, webpage_url):
        self.list_widget.takeItem(self.list_widget.row(item))
        self.del_card_list(webpage_url)

    def add_card(self, data, save = True):
        # id, title(标题), duration(时长), webpage_url(视频地址), thumbnail(缩略图), upload_date(上传日期)
        if save:
            self.downloader.infoSignal.disconnect(self.add_card)

        item = QListWidgetItem()
        item.setSizeHint(QSize(300, 60))
        card = Card(data, self, item)
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, card)
        self.card_list.append(card)
        self.save_download_file()

    def add_task(self):
        # url = self.line_edit.text()
        url = "https://www.bilibili.com/video/BV1Jd4y167xF/?spm_id_from=333.1007.tianma.1-2-2.click&vd_source=749832a882249f9f0a54602e4b308808"
        self.downloader.infoSignal.connect(self.add_card)
        self.downloader.runTask(0, {"url": url})
