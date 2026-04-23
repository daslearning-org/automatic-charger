from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.utils import platform

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDFillRoundFlatIconButton
from kivy.parser import parse_color


Builder.load_string('''

<MainAppBox>:
    orientation: 'vertical'
    spacing: dp(4)
    padding: 0, 0, 0, self.bottom_pad

    MDGridLayout: # control buttons
        cols: 2
        size_hint_y: 0.2
        spacing: dp(4)
        padding: 14, 14, 14, 0 # left, top, right, bottom

        MDFillRoundFlatIconButton:
            id: start_listener_btn
            text: "Start Auto Mode"
            icon: "play"
            font_size: sp(18)
            md_bg_color: 'gray'
            #pos_hint: {"center_x": .5, "center_y": .5}
            size_hint_x: 0.5
            #size_hint_y: 0.7
            on_release: app.toggle_auto_mode()

    BoxLayout: # result display
        size_hint_y: 0.4
        id: result_box
        orientation: 'vertical'
        spacing: dp(4)
        padding: dp(4)

        MDLabel:
            id: btn_text
            halign: "center"
            valign: "top"
            markup: True
            text: ""
            adaptive_height: True

        MDLabel:
            id: result_text
            halign: "center"
            valign: "top"
            markup: True
            text: "Battery details will be shown here (if auto mode is on)"
            adaptive_height: True

''')

class MainAppBox(MDBoxLayout):
    top_pad = NumericProperty(0)
    bottom_pad = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "app_main_bx"
        if platform == "android":
            try:
                from android.display_cutout import get_height_of_bar
                self.top_pad = int(get_height_of_bar('status'))
                self.bottom_pad = int(get_height_of_bar('navigation'))
            except Exception as e:
                print(f"Failed android 15 padding: {e}")
                self.top_pad = 32
                self.bottom_pad = 48
