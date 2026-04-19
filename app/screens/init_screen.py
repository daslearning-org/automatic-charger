from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFillRoundFlatIconButton
from kivymd.uix.label import MDLabel

from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.metrics import dp, sp
from kivy.uix.widget import Widget
from kivy.utils import platform

Builder.load_string('''
<Check@MDCheckbox>:
    group: 'group'
    size_hint: None, None
    size: dp(48), dp(48)

<CheckItem@MDBoxLayout>:
    orientation: 'horizontal'
    adaptive_width: True

<ConfigInput>:
    orientation: 'vertical'
    spacing: dp(20)
    padding: 8, 0, 8, self.bottom_pad # left, top, right, bottom

    MDGridLayout: # Stearing wheel position, (for making u-turn decision)
        cols: 2
        adaptive_height: True

        MDLabel:
            text: "Stearing Position"
            halign: "left"
            font_size: sp(14)
            size_hint_x: 0.4
        MDGridLayout:
            cols: 2
            size_hint_x: 0.6
            #adaptive_height: True
            MDBoxLayout:
                orientation: 'horizontal'
                Check:
                    id: stear_check_right
                    active: True
                    pos_hint: {'center_y': .5}
                    on_active: app.set_stearing_pos("right")
                MDLabel:
                    adaptive_width: True
                    text: "Right"
                    halign: "left"
            MDBoxLayout:
                orientation: 'horizontal'
                Check:
                    id: stear_check_left
                    #active: True
                    pos_hint: {'center_y': .5}
                    on_active: app.set_stearing_pos("left")
                MDLabel:
                    adaptive_width: True
                    text: "Left"
                    halign: "left"

    MDGridLayout: # bluetooth connect
        cols: 2
        adaptive_height: True

        MDLabel:
            id: bt_list_btn_lbl
            text: "Choose ESP32 Bluetooth"
            halign: "left"
            font_size: sp(14)
            size_hint_x: 0.4
        MDFillRoundFlatIconButton:
            text: "Show Devices"
            icon: "bluetooth"
            pos_hint: {'center_x': 0.5}
            size_hint_x: 0.6
            font_size: sp(24)
            on_release: app.list_bl_devices(self)

    MDGridLayout:
        cols: 2
        adaptive_height: True
        MDLabel:
            text: "Enter Bluetooth MAC"
            halign: "left"
            font_size: sp(14)
            size_hint_x: 0.4
        MDTextField:
            id: bt_mac_inp
            text: ""
            hint_text: "XX:XX:XX:XX:XX:XX"
            mode: "rectangle"
            #helper_text_mode: "persistent"
            size_hint_x: 0.6
            font_size: sp(18)
            multiline: False

    Widget:
        size_hint_y: 1

    MDGridLayout:
        cols: 2
        spacing: dp(8)

        MDFillRoundFlatIconButton:
            text: "Connect"
            icon: "bluetooth"
            pos_hint: {'center_x': 0.5}
            size_hint_x: 0.3
            font_size: sp(24)
            #md_bg_color: 'pink'
            on_release: app.connect_esp_bt()

        MDFillRoundFlatIconButton:
            text: "Proceed"
            icon: "door-open"
            pos_hint: {'center_x': 0.5}
            size_hint_x: 0.7
            font_size: sp(24)
            md_bg_color: 'green'
            on_release: app.go_to_nav()

    Widget:
        size_hint_y: 1
''')

class ConfigInput(MDBoxLayout):
    """ Takes configuration inputs """
    top_pad = NumericProperty(0)
    bottom_pad = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if platform == "android":
            try:
                from android.display_cutout import get_height_of_bar
                self.top_pad = int(get_height_of_bar('status'))
                self.bottom_pad = int(get_height_of_bar('navigation'))
            except Exception as e:
                print(f"Failed android 15 padding: {e}")
                self.top_pad = 32
                self.bottom_pad = 48
