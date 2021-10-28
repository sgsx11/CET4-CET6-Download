# -*- coding: utf-8 -*-
# 导入程序运行必须模块
import ctypes
import sys
# PyQt5中使用的基本控件都在PyQt5.QtWidgets模块中

import win32con
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
# 导入designer工具生成的login模块
from dialog import Ui_Dialog
from download import Ui_MainWindow
import os
import requests
import time
from lxml import etree
headers={
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3877.400 QQBrowser/10.8.4506.400'
}


# 继承QThread
class Runthread(QThread):
    # 通过类成员对象定义信号对象
    _signal = pyqtSignal(int)

    def __init__(self,textBrowser,pushButton):
        self.textBrowser = textBrowser
        self.pushButton = pushButton
        super(Runthread, self).__init__()

    def __del__(self):
        self.wait()

    def setUrlAndPresentPath(self,url,presentPath):
        self.url = url
        self.presentPath = presentPath

    def getData(self,url,name,filepath):
        try:
            start = time.time()  # 下载开始时间
            response = requests.get(url=url, headers=headers, stream=True, timeout=5)
            size = 0
            chunk_size = 10240 # 每次下载的数据大小
            content_size = int(response.headers['content-length'])  # 下载文件总大小
            if response.status_code == 200: #判断是否响应成功
                if not os.path.exists(filepath):
                    self.textBrowser.append('开始下载'+name+',[File size]:{size:.2f} MB'.format(size=content_size / 1024 / 1024))  # 开始下载，显示下载文件大小
                    self.textBrowser.moveCursor(self.textBrowser.textCursor().End)  # 文本框显示到底部
                    with open(filepath, 'wb') as fp:
                        for data in response.iter_content(chunk_size=chunk_size):
                            fp.write(data)
                            size += len(data)
                            proess = size / int(content_size) * 100
                            self._signal.emit(int(proess))
                    end = time.time()
                    self.textBrowser.append(name+'下载完成!,times: %.2f秒' % (end - start))#输出下载用时时间
                    self.textBrowser.moveCursor(self.textBrowser.textCursor().End)  # 文本框显示到底部
                else:
                    self.textBrowser.append('下载失败！'+name+'已存在。')
                    self.textBrowser.moveCursor(self.textBrowser.textCursor().End)  # 文本框显示到底部
        except:
            self.textBrowser.append('Error! 请使用稳定的网络进行下载')
            self.textBrowser.moveCursor(self.textBrowser.textCursor().End)  # 文本框显示到底部

    def get(self,url, count, presentPath):
        #textBrowser.append("这里是get方法!")
        #time.sleep(0.2)
        cet6Text = requests.get(url=url, headers=headers, timeout=5).text
        tree = etree.HTML(cet6Text)
        liList = tree.xpath('//*[@id="file-list"]/li')
        temp = 0
        if count == 0:
            n = 3
        else:
            n = 1
        for li in liList:
            if temp <= n:
                temp = temp + 1
                continue
            judge = li.xpath('./div[2]')  # 如果li标签下的div[2]存在，说明是可以直接下载的文件
            if not judge:  # 目录文件
                fileName = li.xpath('./div/a/div[1]/span/text()')[0].strip(' ')#python中的strip()可以去除头尾指定字符
                fileUrl = url + fileName + '/'
                if not os.path.exists(presentPath + '/' + fileName):
                    os.mkdir(presentPath + '/' + fileName)
                # 递归爬取
                self.get(fileUrl, count + 1, presentPath + '/' + fileName)
            else:  # 可下载文件
                downLoadName = li.xpath('./div[1]/div[1]/a[1]/span/text()')[0].strip(' ')
                downLoadUrl = url + downLoadName
                # print(dic)
                self.getData(downLoadUrl, downLoadName, presentPath + '/' + downLoadName)


    def run(self):
        try:
            # 这个目前我没弄明白这里写法
            self.handle = ctypes.windll.kernel32.OpenThread(  # @UndefinedVariable
                win32con.PROCESS_ALL_ACCESS, False, int(QThread.currentThreadId()))
        except Exception as e:
            print('get thread handle failed', e)
        #开始下载
        self.get(self.url,0,self.presentPath)
        #time.sleep(2)
        #下载完成
        self.textBrowser.append("===============================下载完成！==============================")
        self.textBrowser.moveCursor(self.textBrowser.textCursor().End)  # 文本框显示到底部
        #下载完成放开下载按钮
        self.pushButton.setEnabled(True)


class MyMainForm(QMainWindow, Ui_MainWindow):
    _signal = pyqtSignal(int)

    def __init__(self, parent=None):
        super(MyMainForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('CET4_CET6真题一键下载(2016-2021)V1.1.0')
        # 设置单选按钮初始状态
        self.CET4.setChecked(True)
        #主进程id
        #print('main id', int(QThread.currentThreadId()))
        # 添加开始下载按钮信号和槽。注意display函数不加小括号()
        self.pushButton.clicked.connect(self.download)
        # 添加取消下载按钮信号和槽
        self.cancelDownload.clicked.connect(self.cancel)
        # 添加退出按钮信号和槽。调用close函数
        self.cancelButton.clicked.connect(self.close)
        # 添加about按钮信号和槽。调用about函数
        self.about.triggered.connect(self.openDialog)

    def download(self):
            # 创建线程
            self.thread = Runthread(self.textBrowser, self.pushButton)
            # 设置取消线程
            self.thread.finished.connect(self.thread.deleteLater)
            # 连接信号
            self.thread._signal.connect(self.set_progressbar_value)  # 进程连接回传到GUI的事件
            # 添加单选按钮
            self.pushButton.setEnabled(False)

            if self.CET4.isChecked() == True:
                url = 'https://pan.uvooc.com/Learn/CET/CET4/'
                presentPath = './CET4'
                if not os.path.exists(presentPath):
                    os.mkdir(presentPath)
                self.textBrowser.append("CET4真题(2016-2021)即将开始下载，文件将保存在" + os.path.abspath('.') + '\CET4')
                self.textBrowser.append("downloading...下载资源由友沃可（UVOOC.COM）提供\n")
                #self.textBrowser.repaint()

                try:
                    '''
                    myThread = threading.Thread(target=self.get,
                                                args=(url, 0, presentPath,self.textBrowser))  # 必须要用线程做这件事，不然主程序会卡死。
                    myThread.setDaemon(True)#设为保护线程，主进程结束会关闭线程
                    myThread.start()
                    '''
                    #给线程设置url和presentPath
                    self.thread.setUrlAndPresentPath(url, presentPath)
                    # 开始线程
                    self.thread.start()
                except:
                    self.textBrowser.append("下载失败！")
            if self.CET6.isChecked() == True:
                url = 'https://pan.uvooc.com/Learn/CET/CET6/'
                presentPath = './CET6'
                if not os.path.exists(presentPath):
                    os.mkdir(presentPath)
                self.textBrowser.append("CET6真题(2016-2021)即将开始下载，文件将保存在" + os.path.abspath('.') + '\CET6')
                self.textBrowser.append("downloading...下载资源由友沃可（UVOOC.COM）提供\n")
                #self.textBrowser.repaint()
                #time.sleep(2)
                try:
                    #给线程设置url和presentPath
                    self.thread.setUrlAndPresentPath(url, presentPath)
                    # 开始线程
                    self.thread.start()
                except:
                    self.textBrowser.append("下载失败！")

    # 设置进度条
    def set_progressbar_value(self, value):
        self.progressBar.setValue(value)

    def cancel(self):
        ctypes.windll.kernel32.TerminateThread(  # @UndefinedVariable
            self.thread.handle, 0)
        self.textBrowser.append("下载已取消！")
        self.pushButton.setEnabled(True)

    def enablePushBotton(self):
        self.pushButton.setEnabled(True)

    def openDialog(self):
        dialog = AboutWindow(self)
        dialog.show()



class AboutWindow(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super(AboutWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('详细信息')



if __name__ == "__main__":
    # 固定的，PyQt5程序都需要QApplication对象。sys.argv是命令行参数列表，确保程序可以双击运行
    app = QApplication(sys.argv)
    # 初始化
    myWin = MyMainForm()
    # 将窗口控件显示在屏幕上
    myWin.show()
    # 程序运行，sys.exit方法确保程序完整退出。
    sys.exit(app.exec_())
