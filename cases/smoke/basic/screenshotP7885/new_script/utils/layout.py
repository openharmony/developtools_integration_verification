import logging
import re


class Layout:

    def __init__(self, json_data):
        self.element_list = self.parse_attribute_nodes(json_data)

    def parse_attribute_nodes(self, json_obj, attr_list=None):
        if attr_list is None:
            attr_list = []

        if isinstance(json_obj, dict):
            for key, value in json_obj.items():
                if key == 'attributes' and isinstance(value, dict):
                    attr_list.append(value)
                elif isinstance(value, (dict, list)):
                    self.parse_attribute_nodes(value, attr_list)
        elif isinstance(json_obj, list):
            for item in json_obj:
                self.parse_attribute_nodes(item, attr_list)
        return attr_list

    def get_elements_by_text(self, text):
        ems = []
        for e in self.element_list:
            if e.get('text') == text:
                ems.append(e)
        return ems

    def get_element_by_text(self, text, index=0):
        ems = self.get_elements_by_text(text)
        if not ems:
            return
        return ems[index]

    def assert_text_exist(self, text):
        element = self.get_elements_by_text(text)
        rst = '是' if element else '否'
        logging.info('检查[文本]="{}"是否存在？[{}]'.format(text, rst))
        assert element

    def get_elements_by_type(self, _type):
        ems = []
        for e in self.element_list:
            if e.get('type') == _type:
                ems.append(e)
        return ems

    def get_element_by_type(self, _type, index=0):
        ems = self.get_elements_by_type(_type)
        if not ems:
            return
        return ems[index]

    def assert_type_exist(self, _type):
        element = self.get_elements_by_type(_type)
        rst = '是' if element else '否'
        logging.info('检查[type]="{}"是否存在？[{}]'.format(_type, rst))
        assert element

    def get_elements_by_key(self, key):
        ems = []
        for e in self.element_list:
            if e.get('key') == key:
                ems.append(e)
        return ems

    def get_element_by_key(self, key, index=0):
        ems = self.get_elements_by_key(key)
        if not ems:
            return
        return ems[index]

    def assert_key_exist(self, key):
        element = self.get_elements_by_key(key)
        rst = '是' if element else '否'
        logging.info('检查[key]="{}"是否存在？[{}]'.format(key, rst))
        assert element

    @staticmethod
    def center_of_element(e):
        assert e, '控件不存在'
        bounds = e.get('bounds')
        x1, y1, x2, y2 = [int(i) for i in re.findall(r'\d+', bounds)]
        x = (x1 + x2) // 2
        y = (y1 + y2) // 2
        return x, y
