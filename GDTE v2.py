#coding=utf-8

"""
This project is too tiny to push to Github,
Any issues/pull requests please directly contact me:
Discord: Naxrin#6957
Bilibili: https://space.bilibili.com/25982878
"""

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont, QPixmap, QImage
from PyQt5.QtCore import QCoreApplication, Qt, QSortFilterProxyModel, pyqtSignal

from xml.etree import ElementTree
import cv2
import numpy as np
import re
import json
import sys
import os
from datetime import datetime
import traceback

DST = os.path.dirname(__file__) + '/TextureLab'

def tree_to_dict(tree):
    """解析xml树生成dict"""
    d = {}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
    for index, item in enumerate(tree, 1):  
        if item.tag == 'key':
            if tree[index].tag == 'string':  
                d[item.text] = tree[index].text
            elif tree[index].tag == 'true':  
                d[item.text] = True  
            elif tree[index].tag == 'false':  
                d[item.text] = False  
            elif tree[index].tag == 'dict':
                d[item.text] = tree_to_dict(tree[index])  
    return d

def to_data(temp:str):
    """从字符串获取数值列表"""
    temp = temp.replace('{','')
    temp = temp.replace('}','')
    datas = list(int(digit) for digit in temp.split(','))
    return datas

def Read_Plist(name):
    """读取plist文件，返回属性信息"""
    root = ElementTree.fromstring(open(name, 'r', encoding='utf-8').read())

    pngfile = tree_to_dict(root[0])['metadata']['textureFileName']
    plist_dict = tree_to_dict(root[0])['frames']
    result = {}
    # polish string to data
    for png, pps in plist_dict.items():
        result[png]= {'rect':to_data(pps['textureRect'])[:2] + to_data(pps['spriteSize']), 'rotate':pps['textureRotated']}
    return result, pngfile

def Read_Fnt(name):
    """读取fnt文件，返回属性信息"""
    with open(name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    pngname = re.match(r'page id=0 file="(.+\.png)"', lines[2]).group(1)
    width = int(re.search(r'scaleW=(\d+)', lines[1]).group(1))
    height = int(re.search(r'scaleH=(\d+)', lines[1]).group(1))

    prop = {}
    for line in lines[4:]:
        m = re.match(r'char id=(\d+)\s+x=(\d+)\s+y=(\d+)\s+width=(\d+)\s+height=(\d+)\s+xoffset=-?\d+\s+yoffset=-?\d+\s+xadvance=-?\d+\s+page=0\s+chnl=15', line)
        if m:
            prop[m.group(1)] = [int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))]
    return pngname, width, height, prop

class QLabelCheckBox():
    """QLabel和QCheckBox的组合
    构造参数：
        parent:构造所在的界面
        text:文本内容
        x, y:横纵坐标
        textwidth:QLabel的占用长度
        initcheck:初始化勾选状态
        tipline:要显示多少行提示        
        tip:提示"""
        
    def __init__(self, parent, text, x, y, textwidth, initcheck, tip=None):
        self.check = initcheck
        
        self.checkbox = QCheckBox(parent)
        self.checkbox.setGeometry(x, y, 24, 24)
        self.checkbox.setChecked(initcheck)
        self.checkbox.clicked.connect(self.edit)

        self.label = QLabel(parent)
        self.label.setGeometry(x+20, y , textwidth, 24)
        self.label.setText(text)

        if tip != None:
            self.tip = QLabel(parent)
            self.tip.setGeometry(x, y+20, textwidth, 16)
            self.tip.setText(tip)
            self.tip.setStyleSheet('color:blue')

            font = QFont()
            font.setFamily('SimHei')
            font.setPointSize(8)
            self.tip.setFont(font)

    def edit(self):
        self.check = not self.check

class ComboText(QComboBox):
    """ComboBox和LineEdit的复合选框
    构造参数：
        parent:构造所在的界面
        items:选项
        x, y, width, height:位置和尺寸
        scroll:最多下拉选项"""
    def __init__(self, parent, x, y, width, height, scroll=20):
        super(ComboText, self).__init__(parent)
        
        #combobox
        self.setGeometry(x,y,width,height)
        self.setMaxVisibleItems(scroll)
        self.setEditable(True)
 
        # 添加筛选器模型来筛选匹配项
        self.pFilterModel = QSortFilterProxyModel(parent)
        self.pFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)  # 大小写不敏感
        self.pFilterModel.setSourceModel(self.model())
        # 添加一个使用筛选器模型的QCompleter
        self.completer = QCompleter(self.pFilterModel, parent)
        # 始终显示所有(过滤后的)补全结果
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)  # 不区分大小写
        self.setCompleter(self.completer)

        # Qcombobox编辑栏文本变化时对应的槽函数
        self.lineEdit().textEdited.connect(self.pFilterModel.setFilterFixedString)
        self.completer.activated.connect(self.on_completer_activated)

    def refresh_items(self, items):
        """刷新项目"""
        self.clear()
        self.addItems(items)
        
    def on_completer_activated(self, text):
        """当在Qcompleter列表选中，下拉框项目列表选择相应的子项目"""
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)
            # self.activated[str].emit(self.itemText(index))

    def setModel(self, model):
        """在模型更改时，更新过滤器和补全器的模型"""
        super(ComboText, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    def setModelColumn(self, column):
        """在模型列更改时，更新过滤器和补全器的模型列"""
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(ComboText, self).setModelColumn(column)

    def keyPressEvent(self, e):
        """回应回车按钮事件"""
        if e.key() == Qt.Key_Enter & e.key() == Qt.Key_Return:
            text = self.currentText()
            index = self.findText(text, Qt.MatchExactly | Qt.MatchCaseSensitive)
            self.setCurrentIndex(index)
            self.hidePopup()
            super(ComboText, self).keyPressEvent(e)
        else:
            super(ComboText, self).keyPressEvent(e)
            
class ImagePrev(QLabel):
    """预览图框类
    构造参数：
        parent: 所在窗口类
        x,y: 坐标"""
    def __init__(self, parent, x, y):
        super(ImagePrev, self).__init__(parent)
        self.setGeometry(x, y, 200, 200)
        self.setStyleSheet('border-width: 3px;border-style:solid;border-radius:2px;border-color:rgb(30,30,30);')
        
    def display(self, img, color=-1):
        """显示预览图
        参数：
            img: opencv图片对象
            color: 边框颜色：2红1黄0绿-1不变"""
        if color == 2:
            self.setStyleSheet('border-width: 3px;border-style:solid;border-radius:2px;border-color:rgb(255,30,30);')
        elif color == 1:
            self.setStyleSheet('border-width: 3px;border-style:solid;border-radius:2px;border-color:rgb(255,255,30);')
        elif color == 0:
            self.setStyleSheet('border-width: 3px;border-style:solid;border-radius:2px;border-color:rgb(30,255,30);')

        display_img = np.zeros([200, 200, 4], dtype=np.uint8)
        h, w, d = img.shape
        # 防止空图
        if h and w:
            factor = 180/max(h, w)
            W, H = int(w*factor), int(h*factor)
            temppng = cv2.resize(img, dsize = (W, H), interpolation = cv2.INTER_AREA)
            display_img[int(100-H/2):int(100+H/2), int(100-W/2):int(100+W/2)] = temppng

        # cv 图片转换成 qt图片
        display_img = cv2.cvtColor(display_img, cv2.COLOR_BGRA2RGBA)
        qt_img = QImage(display_img.data, # 数据源
                                    display_img.shape[1],  # 宽度
                                    display_img.shape[0],	# 高度
                                    display_img.shape[1] * 4, # 行字节数
                                    QImage.Format_RGBA8888)
	    # label 控件显示图片
        self.setPixmap(QPixmap.fromImage(qt_img))
        self.show()
    
class Rep1(QWidget):
    """单图替换确认界面
    构造参数：
        name: 子贴图名字
        img0: 旧图片opencv对象
        img: 新图片opencv对象"""
    signal = pyqtSignal(list)
    def __init__(self, name, img0, img):
        QWidget.__init__(self)
        
        font = QFont()
        font.setFamily('SimHei')
        font.setPointSize(10)
        self.setFont(font)
        
        self.setFixedSize(480, 330)
        self.move(560, 240)
        self.setWindowTitle('是否确认使用本图片替换？')
        self.setWindowIcon(QIcon('icon.png'))
        
        self.label = QLabel(self)
        self.label.setGeometry(20, 20, 460, 40)
        
        h, w, d = img0.shape
        H, W, D = img.shape
        if h*W != H*w:
            img = cv2.resize(img, (w, h), interpolation = cv2.INTER_AREA)
            code = 2
            self.label.setText(f'{name}\n注：两图片宽高比不相等，可能会伸缩变换导致很丑！')
        elif H != h or W != w:
            img = cv2.resize(img, (w, h), interpolation = cv2.INTER_AREA)
            code = 1
            self.label.setText(f'{name}\n注：两图片等宽高比不等大，或将导致图片观感不符合预期！')
        else:
            code = 0
            self.label.setText(name)
        self.label.setAlignment(Qt.AlignCenter)
        
        self.name = name
        self.img = img
        
        self.lab_arrow = QLabel(self)
        self.lab_arrow.setGeometry(225, 155, 30, 30)
        self.lab_arrow.setStyleSheet('border-image: url(arrowr.png)')
        
        self.lab_img0 = ImagePrev(self, 20, 70)
        self.lab_img0.display(img0)
        
        self.lab_img = ImagePrev(self, 260, 70)
        self.lab_img.display(img, code)
        
        # 确认
        self.btn1 = QPushButton(self)
        self.btn1.setGeometry(140, 280, 80, 30)
        self.btn1.setText('确认')
        self.btn1.clicked.connect(self.yes)
        
        # 取消
        self.btn1 = QPushButton(self)
        self.btn1.setGeometry(260, 280, 80, 30)
        self.btn1.setText('取消')
        self.btn1.clicked.connect(self.no)
        
    def yes(self):
        """确认替换"""
        self.signal.emit([{self.name:self.img}, False, {self.name:True}])
        self.close()
            
    def no(self):
        """取消替换"""
        self.close()
        
class RepAll(QWidget):
    """批量替换操作界面
    构造参数：
        prop: plist控制信息表
        img: 名字和opencv图片对象的键值对表
        setup:初始化设置选项"""
    signal = pyqtSignal(list)
    tole = pyqtSignal(int)
    def __init__(self, prop, img, setup):
        QWidget.__init__(self)
        
        font = QFont()
        font.setFamily('SimHei')
        font.setPointSize(10)
        self.setFont(font)
        
        self.setFixedSize(660, 580)
        self.move(560, 240)
        self.setWindowTitle('批量替换')
        self.setWindowIcon(QIcon('icon.png'))
        
        self.imgs = {}
        self.info = {}
        self.png = img
        self.prop = prop
        self.subname = None
        
        self.lab_arrow = QLabel(self)
        self.lab_arrow.setGeometry(475, 205, 30, 30)
        self.lab_arrow.setStyleSheet('border-image: url(arrowd.png)')

        # 列表
        self.list = QListWidget(self)
        self.list.setGeometry(20, 70, 300, 450)
        self.list.itemClicked.connect(self.pick)
        
        # 不同大小图片的替换策略
        self.lab_fit = QLabel(self)
        self.lab_fit.setGeometry(20, 10, 200, 30)
        self.lab_fit.setText('异尺寸贴图替换策略')
        self.lab_fit.setToolTip('''仅允许完全等大图片可能导致泛用性差
                                容忍所有等宽高比的图片会导致贴图变糊
                                接受任意尺寸的图片会导致宽高比不等的图片被伸缩变换''')
        
        self.cbx_fit = QComboBox(self)
        self.cbx_fit.setGeometry(20, 40, 200, 30)
        self.cbx_fit.addItems(['仅完全等尺寸图片', '等宽高比的图片', '任意尺寸的图片'])
        self.cbx_fit.setCurrentIndex(setup)
        # 图框
        self.lab_img0 = ImagePrev(self, 390, 20)
        self.lab_img = ImagePrev(self, 390, 260)
        
        # 添加
        self.btn_add = QPushButton(self)
        self.btn_add.setGeometry(60, 530, 90, 30)
        self.btn_add.setText('添加项目')
        self.btn_add.clicked.connect(self.add)
        
        # 删除
        self.btn_rmv = QPushButton(self)
        self.btn_rmv.setGeometry(210, 530, 90, 30)
        self.btn_rmv.setText('删除项目')
        self.btn_rmv.clicked.connect(self.rmv)
        
        # 确认
        self.btn_confirm = QPushButton(self)
        self.btn_confirm.setGeometry(360, 530, 90, 30)
        self.btn_confirm.setText('确认替换')
        self.btn_confirm.clicked.connect(self.confirm)
        
        # 取消
        self.btn_cancel = QPushButton(self)
        self.btn_cancel.setGeometry(510, 530, 90, 30)
        self.btn_cancel.setText('放弃替换')
        self.btn_cancel.clicked.connect(self.cancel)

    def pick(self, item):
        """选中icon时调取信息生成预览"""
        self.subname = item.text()
        rect = self.prop[self.subname]['rect']
        if self.prop[self.subname]['rotate']:
            png0 = self.png[rect[1]:rect[1]+rect[2], rect[0]:rect[0]+rect[3]]
            png0 = np.rot90(png0)
        else:
            png0 = self.png[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]]
            
        self.lab_img0.display(png0)
        self.lab_img.display(self.imgs[self.subname], self.info[self.subname])
    
    def add(self):
        """添加项目"""
        path = DST if os.path.exists(DST) else '.'
        filelist, no = QFileDialog.getOpenFileNames(self, '添加图片用于替换', path, "Png(*.png)")
        # 尝试批量添加项目，但是扔掉不是四通道的，无法正常读取的以及文件名不在待替列表里的
        for it in filelist:
            try:
                # 获取单文件名
                it_path = os.path.dirname(it)
                filename = it[len(it_path)+1:]
                temp_img = cv2.imdecode(np.fromfile(it, dtype=np.uint8), -1)
                if len(temp_img.shape) != 3 or temp_img.shape[-1] != 4:
                    print('图像需要是RGBA8888图')
                elif not filename in self.prop.keys():
                    print('文件名不对')
                else:
                    self.imgs[filename] = temp_img
                    if not filename in self.info.keys():
                        self.list.addItem(filename)
                    # 分辨率分类
                    x, y, w, h = self.prop[filename]['rect']
                    H, W, D = temp_img.shape
                    if h*W != H*w:
                        self.info[filename] = 2
                    elif H != h or W != w:
                        self.info[filename] = 1
                    else:
                        self.info[filename] = 0
            except:
                traceback.print_exc()
        
    def rmv(self):
        """删除项目"""
        if self.subname:
            selected_row = self.list.currentRow()
            del self.imgs[self.subname]
            del self.info[self.subname]
            item = self.list.takeItem(selected_row)        
            del item
            self.subname = None
        
    def confirm(self):
        """确认替换"""
        entry = {}
        for item in self.imgs.keys():
            if self.info[item] > self.cbx_fit.currentIndex():
                entry[item] = False
            else:
                entry[item] = True
        result = QMessageBox.question(self, '确认替换',"是否确认替换全部？虽然确认后还可以撤回", QMessageBox.Yes | QMessageBox.No)
        if result == QMessageBox.Yes:
            self.signal.emit([self.imgs, True, entry])
        self.close()
            
    def cancel(self):
        """取消替换"""
        result = QMessageBox.question(self, '确认放弃',"是否确认放弃本窗口的全部操作？没有后悔药吃哦！", QMessageBox.Yes | QMessageBox.No)
        if result == QMessageBox.Yes:
            self.close()
            
    def closeEvent(self, event):
        """重写关闭事件发送设置"""
        self.tole.emit(self.cbx_fit.currentIndex())

class GetIcon(QWidget):
    """从2.11提取icon"""
    def __init__(self):
        QWidget.__init__(self)

        font = QFont()
        font.setFamily('SimHei')
        font.setPointSize(10)
        self.setFont(font)

        self.setFixedSize(480, 410)
        self.move(560, 240)
        self.setWindowTitle('2.11→2.2 Icon搬运')
        self.setWindowIcon(QIcon('icon.png'))

        # 导入Gamesheet02
        self.btn_gs2 = QPushButton(self)
        self.btn_gs2.setGeometry(20, 20, 240, 30)
        self.btn_gs2.setText('选择icon文件GJ_Gamesheet02')
        
        self.lab_gs2 = QLabel(self)
        self.lab_gs2.setGeometry(20, 60, 240, 30)
        self.lab_gs2.setText('未选择')

        # 导入GamesheetGlow
        self.box_glow = QLabelCheckBox(self, '添加描边', 20, 100, 120, True, '在导出文件中添加描边')
                                  
        self.btn_glow = QPushButton(self)
        self.btn_glow.setGeometry(20, 160, 240, 30)
        self.btn_glow.setText('选择描边文件GJ_GamesheetGlow')
        
        self.lab_glow = QLabel(self)
        self.lab_glow.setGeometry(20, 200, 240, 30)
        self.lab_glow.setText('未选择')

        # 形态
        self.lab_status = QLabel(self)
        self.lab_status.setGeometry(20, 240, 50, 30)
        self.lab_status.setText('预览形态')
        
        self.cbx_status = QComboBox(self)
        self.cbx_status.setGeometry(80, 240, 60, 30)
        self.cbx_status.addItems(['cube', 'ship', 'ball', 'ufo', 'wave', 'robot', 'spider'])

        # 序号2.11
        self.lab_code0 = QLabel(self)
        self.lab_code0.setGeometry(170, 240, 30, 30)
        self.lab_code0.setText('序号')
        
        self.cbx_code0 = QComboBox(self)
        self.cbx_code0.setGeometry(200, 240, 60, 30)

class Window(QMainWindow):
    """主窗口"""
    def __init__(self):
        QMainWindow.__init__(self)
            
        font = QFont()
        font.setFamily('SimHei')
        font.setPointSize(10)
        self.setFont(font)

        self.setFixedSize(900, 600)
        self.move(560, 240)
        self.setWindowTitle('Geometry Dash Texture Edit Tool v2')
        self.setWindowIcon(QIcon('icon.png'))

        # 标题
        self.lab_title = QLabel(self)
        self.lab_title.setGeometry(20, 8, 230, 38)
        self.lab_title.setStyleSheet('border-image: url(title2.png)')
        
        # 选择母贴图文件
        self.btn_select = QPushButton(self)
        self.btn_select.setGeometry(20, 45, 100, 30)
        self.btn_select.setText('选择大贴图')
        self.btn_select.setToolTip('''同一文件夹下需要有其控制的png文件''')
        self.btn_select.clicked.connect(self.select_file)

        # 撤退
        self.btn_undo = QPushButton(self)
        self.btn_undo.setGeometry(210, 50, 50, 25)
        self.btn_undo.setText('撤销')
        self.btn_undo.clicked.connect(self.undo)
        self.btn_undo.setEnabled(False)

        # 重做
        self.btn_redo = QPushButton(self)
        self.btn_redo.setGeometry(270, 50, 50, 25)
        self.btn_redo.setText('重做')
        self.btn_redo.clicked.connect(self.redo)
        self.btn_redo.setEnabled(False)         
        
        # 挑选框
        self.pick_combo = ComboText(self, 20, 85, 230, 30)
        
        self.btn_focus = QPushButton(self)
        self.btn_focus.setGeometry(260, 85, 60, 30)
        self.btn_focus.setText('选中')
        self.btn_focus.clicked.connect(self.focus)
        
        # 列表
        self.sublist = QListWidget(self)
        self.sublist.setGeometry(20, 125, 300, 405)
        self.sublist.itemClicked.connect(self.display_item)

        # 预览画面
        self.lab_prevttl = QLabel(self)
        self.lab_prevttl.setGeometry(340, 10, 200, 30)
        self.lab_prevttl.setText('预览窗口')
        self.lab_prevttl.setAlignment(Qt.AlignCenter) # 居中对齐

        self.lab_prev = ImagePrev(self, 340, 40)

        self.lab_stats = QLabel(self)
        self.lab_stats.setGeometry(340, 240, 200, 30)
        self.lab_stats.setAlignment(Qt.AlignCenter)

        #——————————————————仓库——————————————————
        # 查看仓库
        self.btn_folder = QPushButton(self)
        self.btn_folder.setGeometry(90, 540, 160, 30)
        self.btn_folder.setText('查看仓库')
        self.btn_folder.clicked.connect(self.openfolder)

        #——————————————————特色——————————————————
        # 画质转换
        self.btn_rep1 = QPushButton(self)
        self.btn_rep1.setGeometry(360, 300, 160, 30)
        self.btn_rep1.setText('画质转换')
        self.btn_rep1.clicked.connect(self.uhd2hd)

        # 提取icon
        self.btn_rep1 = QPushButton(self)
        self.btn_rep1.setGeometry(360, 340, 160, 30)
        self.btn_rep1.setText('icon提取')
        self.btn_rep1.clicked.connect(self.get_icon)        

        # 单图替换
        self.btn_rep1 = QPushButton(self)
        self.btn_rep1.setGeometry(360, 380, 160, 30)
        self.btn_rep1.setText('单图替换')
        self.btn_rep1.clicked.connect(self.rep1)
        
        # 批量替换
        self.btn_repall = QPushButton(self)
        self.btn_repall.setGeometry(360, 420, 160, 30)
        self.btn_repall.setText('批量替换')
        self.btn_repall.clicked.connect(self.repall)
        
        # 导出小图
        self.btn_exp1 = QPushButton(self)
        self.btn_exp1.setGeometry(360, 460, 160, 30)
        self.btn_exp1.setText('导出小图')
        self.btn_exp1.clicked.connect(self.exp1)
        
        # 导出全部
        self.btn_expall = QPushButton(self)
        self.btn_expall.setGeometry(360, 500, 160, 30)
        self.btn_expall.setText('导出全部')
        self.btn_expall.clicked.connect(self.expall)
        
        # 导出大图
        self.btn_expbig = QPushButton(self)
        self.btn_expbig.setGeometry(360, 540, 160, 30)
        self.btn_expbig.setText('导出大图')
        self.btn_expbig.clicked.connect(self.expbig)

        # 输出框
        self.lab_output = QLabel(self)
        self.lab_output.setText('运行报告')
        self.lab_output.setGeometry(560, 10, 320, 20)
        self.lab_output.setAlignment(Qt.AlignCenter)

        self.textBrowser = QTextBrowser(self)
        self.textBrowser.setGeometry(560, 30, 320, 550)
        self.textBrowser.setFrameShape(QFrame.Box)
        self.textBrowser.setFrameShadow(QFrame.Raised)
        self.textBrowser.setStyleSheet('background-color:rgba(30,30,30,0);border-left:1px solid')

        self.subname = None # 选中的子贴图名字
        self.imgs = []   # 每一步的png样貌
        self.steps = []  # 每一步的更改操作
        self.p = 0
        self.warning = False
        # 初始化
        try:
            config = json.load(open('config.json', 'r', encoding='utf-8'))
            self.tolerance = config['tolerance']            
            self.plistfile = config['initfile']

            if os.path.exists(self.plistfile):
                # 获取该有的plist文件名
                path = os.path.dirname(self.plistfile)
                self.prop, pngfile_raw = Read_Plist(self.plistfile)
                self.pngfile = path + '/' + re.split('/', pngfile_raw)[-1]
                # 读取png文件
                img = cv2.imdecode(np.fromfile(self.pngfile, dtype=np.uint8), -1)
                self.imgs = [img]
                self.steps = ['start']
                self.p = 1
                # 添加列表
                self.sublist.addItems(self.prop.keys())
                self.pick_combo.refresh_items(self.prop.keys())
                self.printf('成功导入图片！', 'green')
            else:
                self.pngfile = ''
                self.plistfile = ''
                return

        except:
            self.pngfile = ''
            self.plistfile = ''
            self.prop = None
            self.sublist.clear()
            self.tolerance = 0
        
    def select_file(self):
        """选择大贴图"""
        if self.warning:
            result = QMessageBox.question(self, '读取文件',"尚未保存当前图片,确认重选文件?此前所有操作无法恢复!", QMessageBox.Yes | QMessageBox.No)
            if result == QMessageBox.No:
                return
        default_path = '.' # 默认位置
        plistfile, file_type = QFileDialog.getOpenFileName(self, "选择贴图的plist文件", default_path, "Plist(*.plist)")
        pngfile = ''
        # 防止没选择文件导致闪退
        if plistfile:
            # 获取其控制的png文件名
            path = os.path.dirname(plistfile)
            try:
                # 读取plist文件
                prop, pngfile_raw = Read_Plist(plistfile)
                pngfile = path + '/' + re.split('/', pngfile_raw)[-1]
            except:
                self.printf('Plist文件读取失败！', 'red')                  
                traceback.print_exc()

            # png文件在场
            if os.path.exists(pngfile):
                try:
                    # 读取png文件
                    img = cv2.imdecode(np.fromfile(pngfile, dtype=np.uint8), -1)
                    if len(img.shape) == 3 or img.shape[-1] == 4:
                        # 添加列表
                        self.sublist.clear()
                        self.sublist.addItems(prop.keys())
                        self.pick_combo.refresh_items(prop.keys())
                        self.printf('成功导入图片！', 'green')
                        # 官宣
                        self.pngfile, self.plistfile = pngfile, plistfile
                        self.prop = prop
                        self.imgs = [img]
                        self.steps = ['start']
                        self.p = 1
                    else:
                        self.printf('需要四通道RGBA8888图片！，', 'red')
                        return
                except:
                    self.printf('这图片可能有毒！', 'red')
                    return

            # 没有png文件在场
            else:
                self.printf('无法选择此文件组！', 'red')
                self.printf('原因：找不到其控制的png文件。', 'red')
        
    def focus(self):
        """点击选中按键的效果，选中图片生成预览"""
        if self.imgs:
            text = self.pick_combo.currentText()
            for index, label in enumerate(self.prop.keys()):
                if text == label:
                    self.sublist.setCurrentRow(index)
                    self.display_item(label)
                    break

    def display_item(self, item):
        """生成预览的实现"""
        self.subname = item if type(item) == str else item.text()
        rect = self.prop[self.subname]['rect']
        img = self.imgs[self.p-1]
        if self.prop[self.subname]['rotate']:
            self.temppng = img[rect[1]:rect[1]+rect[2], rect[0]:rect[0]+rect[3]]
            self.temppng = np.rot90(self.temppng)
        else:
            self.temppng = img[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]]
            
        self.lab_prev.display(self.temppng)
        self.lab_stats.setText(f'X={rect[0]} Y={rect[1]} W={rect[2]} H={rect[3]}')
    
    def rep1(self):
        """替换单个图片"""
        if self.subname:
            new_file, file_type = QFileDialog.getOpenFileName(self, "选择贴图文件", '.', "Png(*.png)")
            # 选择了文件才进行后续步骤
            if new_file:
                new_png = cv2.imdecode(np.fromfile(new_file, dtype=np.uint8), -1)
                if len(new_png.shape) == 3 and new_png.shape[-1] == 4:
                    # 构造并显示确认窗口
                    self.confirm = Rep1(self.subname, self.temppng, new_png)
                    self.confirm.signal.connect(self.replace)
                    self.confirm.show()
                else:
                    self.printf('请选择一张RGBA8888图片！', 'red')
                    return
    
    def repall(self):
        """批量替换图片"""
        if self.imgs:
            self.widget = RepAll(self.prop, self.imgs[self.p-1], self.tolerance) #plist定位和大图
            self.widget.signal.connect(self.replace)
            self.widget.tole.connect(self.tole)
            self.widget.show()
    
    def exp1(self):
        """导出一个图片"""
        if self.subname:
            files = os.listdir(DST)
            name = re.split('/', self.subname)[-1]
            if self.subname in files:
                result = QMessageBox.question(self, '文件已存在！',"选Yes创建副本\n选No直接覆盖", QMessageBox.Yes | QMessageBox.No)
                if result == QMessageBox.Yes:
                    i = 1
                    while f'Copy-{i} ' + name in files:
                        i += 1
                    name = f'Copy-{i} ' + name
            try:
                cv2.imencode(".png", self.temppng)[1].tofile(os.path.join(DST, name))
                self.printf('导出贴图成功！', 'green')
                os.startfile(DST)
            except:
                self.printf(traceback.format_exc())
                self.printf('导出贴图失败！是在点炒饭吗？', 'red')
        
    
    def expall(self):
        """导出所有图片"""
        if self.imgs:
            folder = os.path.join(DST, 'export_' + datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
            if not os.path.exists(folder):
                os.mkdir(folder)
            img = self.imgs[self.p-1]
            fails = {}
            for name, prop in self.prop.items():
                rect = prop['rect']
                try:                
                    if prop['rotate']:
                        temppng = img[rect[1]:rect[1]+rect[2], rect[0]:rect[0]+rect[3]]
                        temppng = np.rot90(temppng)
                    else:
                        temppng = img[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]]
                except:
                    fails[name] = '位置或尺寸异常，可能超出了图像边界'
                try:
                    cv2.imencode(".png", temppng)[1].tofile(os.path.join(folder, name))
                except:
                    fails[name] = '写入文件失败'
            if fails:
                self.printf('以下贴图导出失败！')
                for item, reason in fails.items():
                    self.printf(item, 'red')
                    self.printf(reason, 'red')
            else:
                self.printf('导出全部成功！', 'green')
                
            os.startfile(folder)
     
    def expbig(self):
        """导出大图片"""
        if self.imgs:
            name = os.path.basename(self.pngfile)
            if os.path.exists(os.path.join(DST, name)):
                result = QMessageBox.question(self, '文件已存在！',"选Yes创建副本\n选No直接覆盖", QMessageBox.Yes | QMessageBox.No)
                if result == QMessageBox.Yes:
                    i = 0
                    new_name = ''
                    while True:
                        new_name = f'Copy-{i} {name}'
                        if os.path.exists(os.path.join(DST, new_name)):
                            i += 1
                        else:
                            name = new_name
                            break
            try:
                cv2.imencode(".png", self.imgs[self.p-1])[1].tofile(os.path.join(DST, name))
                self.printf('导出大图成功！', 'green')
                self.warning = False
                os.startfile(DST)
            except:
                self.printf('导出大图失败！是在点炒饭吗？', 'red')
                self.printf(traceback.format_exc())
    
    def replace(self, signal):
        """执行单次或多次替换"""
        texs, multi, entry = signal # 子贴图们，替换类型单次多次，可行性分析结果
        img = self.imgs[self.p-1]
        for key, value in texs.items():
            if entry[key]:
                if self.prop[key]['rotate']:
                    rot_value = np.rot90(value, -1) # 旋转
                else:
                    rot_value = value
                rect = self.prop[key]['rect']
                try:
                    if self.prop[key]['rotate']:
                        img[rect[1]:rect[1]+rect[2], rect[0]:rect[0]+rect[3]] = rot_value
                    else:
                        img[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]] = rot_value
                except:
                    self.printf(f'{key}替换失败！为什么捏', 'red')                    
                    self.printf(traceback.format_exc())
            else:
                self.printf(f'该子贴图不满足要求：{key}', 'red')

        # 结算
        self.imgs = self.imgs[:self.p] + [img]
        self.steps = self.steps[:self.p] + ['Multi' if multi else f'Single {key}']
        self.p += 1
        self.btn_undo.setEnabled(True)
        self.btn_redo.setEnabled(False)
        self.warning = True
        # 刷新预览
        if self.subname:
            self.display_item(self.subname)

    #——————————————————特色功能——————————————————
    def uhd2hd(self):
        """画质转换（UHD转HD）"""
        # 修改plist的正则规则 
        def reg(m):
            if m.group(1) in ['size','lineHeight','base','scaleW','scaleH','x','y','width','height','xoffset','yoffset','xadvance','amount','x', 'y']:
                #print([m.group(0), m.group(1), m.group(2)])
                return f'{m.group(1)}={int(m.group(2)) // 2}'
            return m.group(0)
        
        def fontname(m):
            return f'page id=0 file="{m.group(1)}-hd.png"'
        
        def plistname(m):
            return f'<string>{m.group(1)}-hd.png</string>'

        def f1(m):
            return f'<string>{{{str(int(m.group(1))//2)},{str(int(m.group(2))//2)}}}</string>'

        def f2(m):
            return f'<string>{{{{{str((int(m.group(1))+1)//2)},{str((int(m.group(2))+1)//2)}}},{{{str(int(m.group(3))//2)},{str(int(m.group(4))//2)}}}}}</string>'
        
        src = QFileDialog.getExistingDirectory(self, "选择UHD材质文件夹", '.')
        src.replace('\\', '/')
        dst = os.path.join(DST, 'convert_' + datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
        if not os.path.exists(dst):
            os.mkdir(dst)

        included = [] # 被指定的png和字体文件
        failures = [] # 修改出错的文件

        # 遍历修改plist和fnt
        for root, paths, files in os.walk(src):
            # create folder
            for path in paths:
                if not os.path.exists(dst + root[len(src):] + '/' + path):
                    os.mkdir(dst + root[len(src):] + '/' + path)

            for file in files:
                # FNT
                if 'uhd.fnt' in file:
                    # 初始化
                    pngf, width, height, prop = '', 0, 0, {}

                    # 读取png名
                    try:
                        pngf, width, height, prop = Read_Fnt(root + '/' + file)
                        included.append(src + '/' + pngf)
                    except:
                        failures.append(root + '/' + file)

                    if not root + '/' + file in failures:
                        # 修改png
                        try:
                            # 读取
                            img = cv2.imdecode(np.fromfile(src+ '/' +pngf, dtype=np.uint8), -1)
                            # 尺寸
                            width, height = img.shape[1], img.shape[0]
                            # 创建HD图片
                            img_new = np.zeros([(height+1)//2, (width+1)//2, 4], dtype=np.uint8)
                            # 粘贴
                            for value in prop.values():
                                x, y, w, h = value
                                if w>1 and h>1:
                                    clip = img[y : y+h, x : x+w]
                                    new_clip = cv2.resize(clip, [w//2, h//2])
                                    img_new[(y+1)//2 : (y+1)//2 + h//2, (x+1)//2 : (x+1)//2 + w//2] = new_clip
                            # 保存到文件
                            cv2.imencode(".png", img_new)[1].tofile(dst + '/' + pngf[:-7] + 'hd.png')
                        except:
                            traceback.print_exc()
                            failures.append(src + '/' + pngf)

                        # 修改plist
                        try:
                            with open(root + '/' + file, 'r', encoding='utf-8') as f:
                                text = f.read()
                            text = re.sub(r'(\w+)=(-?\d+)', reg, text)
                            text = re.sub(r'page id=0 file="(.*)-uhd\.png"', fontname, text, count=1)

                            with open(dst + root[len(src):] + '/' + file[:-7] + 'hd.fnt', 'w', encoding='utf-8') as f:
                                f.write(text)
                        except:
                            failures.append(root + '/' + file)

                # PLIST
                if 'uhd.plist' in file:
                    # 初始化
                    pngf = ''
                    prop = {}

                    # 读取png名字
                    try:
                        prop, pngf = Read_Plist(root + '/' + file)
                        included.append(src + '/' + pngf)
                    except:
                        failures.append(root + '/' + file)

                    if not root + '/' + file in failures:
                        # 修改png
                        try:
                            # 读取
                            img = cv2.imdecode(np.fromfile(src + '/' + pngf, dtype=np.uint8), -1)
                            # 尺寸
                            width, height = img.shape[1], img.shape[0]
                            # 创建HD图片
                            img_new = np.zeros([(height+1)//2, (width+1)//2, 4], dtype=np.uint8)
                            # 粘贴
                            for value in prop.values():
                                x, y, w, h = value['rect']                                
                                if value['rotate']:
                                    x, y, h, w = value['rect']
                                if w>1 and h>1:
                                    clip = img[y : y+h, x : x+w]
                                    new_clip = cv2.resize(clip, (w//2, h//2))
                                    img_new[(y+1)//2 : (y+1)//2 + h//2, (x+1)//2 : (x+1)//2 + w//2] = new_clip
                            # 保存到文件
                            cv2.imencode(".png", img_new)[1].tofile(dst + '/' + pngf[:-7] + 'hd.png')
                        except:
                            print([x, y, w, h])
                            traceback.print_exc()
                            failures.append(src + '/' + pngf)

                        # 修改plist本体
                        try:
                            with open(root + '/' + file, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                            for i, line in enumerate(lines):
                                if re.search(r'<key>textureFileName</key>', line) or re.search(r'<key>realTextureFileName</key>', line):
                                    lines[i+1] = re.sub(r'<string>(.*)-uhd\.png</string>\n', plistname, lines[i+1], count=1)

                                elif re.search(r'<key>spriteOffset</key>', line) or re.search(r'<key>spriteSize</key>', line) or re.search(r'<key>spriteSourceSize</key>', line):
                                    lines[i+1] = re.sub(r'<string>{(-?\d+),(-?\d+)}</string>', f1, lines[i+1])

                                elif re.search('<key>textureRect</key>', line):
                                    lines[i+1] = re.sub(r'<string>{{(-?\d+),(-?\d+)},{(-?\d+),(-?\d+)}}</string>', f2, lines[i+1])

                                elif re.search('<key>size</key>', line):
                                    lines[i+1] = re.sub(r'<string>{(-?\d+),(-?\d+)}</string>', f1, lines[i+1])
                            # 写入文件
                            with open(dst + root[len(src):] + '/' + file[:-9] + 'hd.plist', 'w', encoding='utf-8') as f:
                                for li in lines:
                                    f.write(li)
                        except:
                            failures.append(root + '/' + file)
                            
        # 再次遍历修改剩下的文件
        for root, paths, files in os.walk(src):
            for file in files:
                # PNG
                if 'uhd.png' in file and not root + '/' + file in included:
                    try:
                        img = cv2.imdecode(np.fromfile(root + '/' + file, dtype=np.uint8), -1)
                        width, height = img.shape[1], img.shape[0]
                        img_new = cv2.resize(img, (int(width / 2), int(height / 2)))
                        cv2.imencode(".png", img_new)[1].tofile(dst + root[len(src):] + '/' + file[:-7] + 'hd.png')
                    except:
                        failures.append(root + '/' + file)
                            
                # 其他文件直接复制粘贴
                elif not 'uhd.plist' in file and not 'uhd.fnt' in file:
                    command = 'copy ' + root + '/' + file + ' ' + dst + root[len(src):] + '/' + file
                    os.popen(command.replace('\\', '/'))

        # 上报运行结果
        if failures:
            self.printf('以下文件导出失败：', 'red')
            for fail in failures:
                self.printf('  ' + fail)

        elif src: # 没选就不报成功
            self.printf('导出完美成功！', 'green')

    def get_icon(self):
        self.IconKit = GetIcon()
        self.IconKit.show()
    
    #————————————————————基础支撑————————————————
    def openfolder(self):
        """打开文件夹"""
        os.startfile(DST)
        
    def tole(self, signal):
        """响应批替窗口信号更改tolerance设置"""
        self.tolerance = signal

    def undo(self):
        self.p -= 1
        self.refresh()

    def redo(self):
        self.p += 1
        self.refresh()

    def refresh(self):
        self.btn_undo.setEnabled(not self.p == 1)
        self.btn_redo.setEnabled(not self.p == len(self.steps))
        # 刷新预览
        if self.subname:
            self.display_item(self.subname)
        
    def printf(self, text, color = 'black'):
        """UI界面输出
        参数：
            text:要输出到textBrowser的文本和颜色"""
        self.textBrowser.append(f'<font color={color}>{text}<font>')
        
    def closeEvent(self, event):
        """关闭前行为"""
        if self.warning:
            result = QMessageBox.question(self, '关闭工具',"尚未保存当前图片,确认退出工具?此前所有操作无法恢复!", QMessageBox.Yes | QMessageBox.No)
            if result == QMessageBox.No:
                event.ignore()
                return
            
        config = {'initfile':self.plistfile, 'tolerance':self.tolerance}
        json.dump(config, open('config.json', 'w', encoding='utf-8'), indent=4, ensure_ascii=False)

if __name__ == '__main__':
    # 补文件夹
    if not os.path.exists(DST):
        os.mkdir(DST)
        
    # 适配选项
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    # 主程序
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())