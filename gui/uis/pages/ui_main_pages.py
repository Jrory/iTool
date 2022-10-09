# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.0
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# There are limitations on Qt licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtforpython/licenses.html
#
# ///////////////////////////////////////////////////////////////

# IMPORT QT CORE
# ///////////////////////////////////////////////////////////////
from qt_core import *
from .home_page import *
import re

class Ui_MainPages(object):
    def __init__(self, left_pages):
        self.left_pages = left_pages
        self.page_list = list()
        self.page_obj_list = list()

    def setupUi(self, MainPages):
        if not MainPages.objectName():
            MainPages.setObjectName(u"MainPages")
        MainPages.resize(860, 600)
        self.main_pages_layout = QVBoxLayout(MainPages)
        self.main_pages_layout.setSpacing(0)
        self.main_pages_layout.setObjectName(u"main_pages_layout")
        self.main_pages_layout.setContentsMargins(5, 5, 5, 5)
        self.pages = QStackedWidget(MainPages)
        self.pages.setObjectName(u"pages")

        for left_page in self.left_pages:
            if not left_page["show_top"]:
                continue

            if left_page["page_name"] == "home_page":
                page_obj = HomePage(left_page["page_name"])

            self.pages.addWidget(page_obj.page)
            self.page_list.append(page_obj.page)
            self.page_obj_list.append(page_obj)

        self.main_pages_layout.addWidget(self.pages)

        self.retranslateUi(MainPages)
        self.pages.setCurrentIndex(0)
        QMetaObject.connectSlotsByName(MainPages)
    # setupUi

    def getPage(self, pageName):
        for page in self.page_list:
            if page.objectName() == pageName:
                return page

    def getPageObj(self, pageName):
        for obj in self.page_obj_list:
            if obj.page_name == pageName:
                return obj

    def retranslateUi(self, MainPages):
        MainPages.setWindowTitle(QCoreApplication.translate("MainPages", u"Form", None))


