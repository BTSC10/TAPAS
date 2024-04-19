import math

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

#ICON_RED_LED = QPixmap("icons/red-led-on.png")


class update_manager():
    def __init__(self):
        self.param_sliders = []

    def add_slider(self, slider_obj):
        self.param_sliders.append(slider_obj)

    def update_sliders(self):
        for slider_obj in self.param_sliders:
            slider_obj.update_limits()
            slider_obj.update_param_value()

class simple_number_box():
    def __init__(self, cam_obj, update_obj, name):
        self.cam_obj = cam_obj
        self.updater = update_obj
        self.name = name

        self.widget = QWidget()
        self.line_edit = QSpinBox()

        self.line_edit.setMinimum(0)
        self.line_edit.setSingleStep(1)
        self.line_edit.setValue(10)
        self.line_edit.setMaximum(1000000)


        self.widget.setStyleSheet("background:white")

        grid = QHBoxLayout()
        grid.addWidget(QLabel(name))
        grid.addWidget(self.line_edit)

        self.widget.setLayout(grid)
        self.widget.setFixedHeight(50)

    def get(self):
        try:
            return self.line_edit.value()
        except Exception as e:
            print(e)
            return 0

class simple_line_edit():
    def __init__(self, name):
        self.name = name

        self.widget = QWidget()
        self.line_edit = QLineEdit()

        self.widget.setStyleSheet("background:white")

        grid = QHBoxLayout()
        grid.addWidget(QLabel(name))
        grid.addWidget(self.line_edit)

        self.widget.setLayout(grid)
        self.widget.setFixedHeight(50)

    def get(self):
        try:
            return self.line_edit.text()
        except Exception as e:
            print("line edit get error")
            print(e)
            return 0

class simple_text_edit():
    def __init__(self, name):
        self.name = name

        self.widget = QWidget()
        self.line_edit = QLineEdit()

        self.widget.setStyleSheet("background:white")

        grid = QHBoxLayout()
        grid.addWidget(QLabel(name))
        grid.addWidget(self.line_edit)

        self.widget.setLayout(grid)
        self.widget.setFixedHeight(50)

    def get(self):
        try:
            return self.line_edit.value()
        except Exception as e:
            print("line edit get error")
            print(e)
            return 0

class simple_tick_box():
    def __init__(self, cam_obj, update_obj, name):
        self.cam_obj = cam_obj
        self.updater = update_obj
        self.name = name

        self.widget = QWidget()
        self.box = QCheckBox()

        self.widget.setStyleSheet("background:white")

        grid = QHBoxLayout()
        grid.addWidget(QLabel(name))
        grid.addWidget(self.box)

        self.widget.setLayout(grid)
        self.widget.setFixedHeight(50)

"""class simple_indicator():
    def __init__(self, cam_obj, update_obj, name):
        self.cam_obj = cam_obj
        self.updater = update_obj
        self.name = name
        self._state = False

        self.widget = QWidget()
        self.light = QLabel()

        self.light.setPixmap(ICON_RED_LED)

        self.widget.setStyleSheet("background:white")

        grid = QHBoxLayout()
        grid.addWidget(QLabel(name))
        grid.addWidget(self.light)

        self.widget.setLayout(grid)
        self.widget.setFixedHeight(50)

    def get(self):
        return self._state

    def set(self, state):
        self._state = state
        if self._state:
            self.light.setPixmap(ICON_RED_LED)
        else:
            self.light.setPixmap(ICON_RED_LED)
        return self._state"""

class simple_indicator():
    def __init__(self, cam_obj, update_obj, name):
        self.cam_obj = cam_obj
        self.updater = update_obj
        self.name = name
        self._state = False

        self.widget = QWidget()
        self.light = QLabel()


        self.widget.setStyleSheet("background:white")
        self.light.setStyleSheet("background:gray")

        grid = QHBoxLayout()
        grid.addWidget(QLabel(name))
        grid.addWidget(self.light)

        self.widget.setLayout(grid)
        self.widget.setFixedHeight(50)

    def get(self):
        return self._state

    def set(self, state):
        self._state = state
        if self._state:
            self.light.setStyleSheet("background:red")
        else:
            self.light.setStyleSheet("background:gray")
        return self._state


    
class simple_param_slider():
    def __init__(self, cam_obj, update_obj, name, param_name):
        self.cam_obj = cam_obj
        self.updater = update_obj
        self.name = name
        self.param = param_name

        self.min_value = 200
        self.max_value = 20000
        self.inc = 100


        self.widget = QWidget()
        self.__slidebar = QSlider(Qt.Horizontal)
        self.__spinbox = QDoubleSpinBox()
        self.__min_widget = QLabel(str(self.min_value))
        self.__max_widget = QLabel(str(self.max_value))
        

        self.widget.setStyleSheet("background:white")

        self.update_limits()
        #self.update_param_value()
        """self.__slidebar.value = int(self.max_value)
        self.__slidebar.sliderPosition = int(self.max_value)
        """
        #self.__slidebar.update()
        #self.__slidebar.repaint()
        self.__slidebar.valueChanged.connect(lambda value: self.slider_prescale(value))  #lambda value: self.cam_obj.set_param(self.param, value)

        self.__spinbox.setKeyboardTracking(False)
        self.__spinbox.valueChanged.connect(lambda value: self.on_update(value))
        
        slide_grid = QGridLayout()
        slide_grid.addWidget(QLabel(name), 0, 0, 1, 1) #maybe 0,0,2,1
        slide_grid.addWidget(self.__spinbox, 0, 1)
        slide_grid.addWidget(self.__slidebar, 0, 2, 1, 2)
        slide_grid.addWidget(self.__min_widget, 1, 2, alignment=Qt.AlignmentFlag.AlignLeft)
        slide_grid.addWidget(self.__max_widget, 1, 3, alignment=Qt.AlignmentFlag.AlignRight)

        slide_grid.setColumnStretch(0, 3)
        slide_grid.setColumnStretch(1, 1)
        slide_grid.setColumnStretch(2, 10)

        self.widget.setLayout(slide_grid)
        self.widget.setFixedHeight(70)


        self.update_param_value()
        print("Slider:\tInitialised, Starting value", self.__slidebar.value())

        self.updater.add_slider(self)


    def update_limits(self):
        
        self.min_value, self.current_value, self.max_value, self.inc = self.cam_obj.get_param_info(self.param)

        self.min_value = self.min_value
        self.max_value = self.max_value

        self.__min_widget.setText(str(round(self.min_value, 2)))
        self.__max_widget.setText(str(round(self.max_value, 2)))
        
        self.__slidebar.setRange(0, int((self.max_value - self.min_value)/self.inc))
        
        self.__spinbox.setRange(self.min_value, self.max_value)
        self.__spinbox.setSingleStep(self.inc)

    def update_param_value(self):
        
        self.current_value = self.cam_obj.get_param(self.param)

        self.__slidebar.blockSignals(True)
        self.__slidebar.setValue(self.value_to_slider(self.current_value))
        self.__slidebar.blockSignals(False)

        self.__spinbox.blockSignals(True)
        self.__spinbox.setValue(self.current_value)
        self.__spinbox.blockSignals(False)

    def slider_to_value(self, value):
        return self.min_value + value * self.inc
    def value_to_slider(self, value):
        return int((value - self.min_value) / self.inc)

    def slider_prescale(self, value):
        self.on_update(self.slider_to_value(value))

    def on_update(self, value):
        #print("new value demand:", value)
        self.cam_obj.set_param(self.param, value, v=0)
        self.updater.update_sliders()
        #self.update_limits()
        #self.update_param_value()

if __name__ == "__main__":
    print("qt modules")
