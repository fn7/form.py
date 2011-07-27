# coding: utf-8

"""
Copyright (c) 2011, nobuyuki fukuda <fn7.bitbucket at gmail.com>
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of the nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""




import sys, traceback
from lxml import html
from time import sleep
import re

class Input():
    def __init__(self, form_element, name):
        self.form_element = form_element
        self.name = name

    def input(self, value):
        """
        webdriver用の関数名と引数を返す
        getattr関数を用いて、関数名からメソッドを取得し実行するためのもの。
        """
        return [['send_keys', self.xpath, value]]

class ChoiceInput(Input):
    def __init__(self, form_element, name, input_list):
        Input.__init__(self, form_element, name)
        self.input_list = input_list

    def choice(self, n):
        return self.input_list[n]

        
class Form():

    class Textfield(Input):
        @staticmethod
        def xpath():
            return '//input[@type="text"]'
        def __init__(self, form_element, name):
            self.xpath = '//input[@type="text" and @name="%s"]' % name
            Input.__init__(self, form_element, name)

    class Textarea(Input):
        @staticmethod
        def xpath():
            return '//textarea'
        def __init__(self, form_element, name):
            self.xpath = '//textarea[@name="%s"]' % name
            Input.__init__(self, form_element, name)


    class Radiobutton(ChoiceInput):
        @staticmethod
        def xpath():
            return '//input[@type="radio"]'
        def __init__(self, form_element, name):
            self.xpath = '//input[@type="radio" and @name="%s" and @value="%%s"]' % (name)
            input_list = []
            for elem in form_element.xpath('//input[@type="radio" and @name="%s"]' % name):
                if len(elem.get('value')) > 0:
                    input_list.append( elem.get('value') )
            if len(input_list) < 1:
                raise Exception, "input_list is empty"
            ChoiceInput.__init__(self, form_element, name, input_list)
            
        def input(self, value):
            return [['click', self.xpath % value, None]]

    class Checkbox(ChoiceInput):
        @staticmethod
        def xpath():
            return '//input[@type="checkbox"]'
        def __init__(self, form_element, name):
            self.xpath = '//input[@type="checkbox" and @name="%s" and @value="%%s"]' % (name)
            input_list = []
            for elem in form_element.xpath('//input[@type="checkbox" and @name="%s"]' % name):
                if len(elem.get('value')) > 0:
                    input_list.append( elem.get('value') )
            if len(input_list) < 1:
                raise Exception, "input_list is empty"
            ChoiceInput.__init__(self, form_element, name, input_list)

        def input(self, value):
            v = value if isinstance(value, list) or isinstance(value, tuple) else [value]
            r = []
            for i in v:
                r.append(['click', self.xpath % i, None])
            return r


    class Pulldown(ChoiceInput):
        @staticmethod
        def xpath():
            return '//select'
        def __init__(self, form_element, name):
            self.xpath = '//select[@name="%s"]/option[@value="%%s"]' % (name)
            input_list = []
            for elem in form_element.xpath('//select[@name="%s"]/option' % name):
                if len(elem.get('value')) > 0:
                    input_list.append( elem.get('value') )
            if len(input_list) < 1:
                raise Exception, "input_list is empty: %s" % self.xpath
            ChoiceInput.__init__(self, form_element, name, input_list)

        def input(self, value):
            return [['click', self.xpath % value, None]]


    def __init__(self, browser, xpath):
        self.xpath = xpath
        self.browser = browser

        try:
            self.elem = html.fromstring(browser.page_source).xpath(xpath)[0];
            
        except Exception, e:
            traceback.print_exc()
            self.browser.close()
            exit()
        
        # 入力項目の取得
        self.inputs = {}
        for elem in self.elem.xpath(Form.Textfield.xpath()):
            name = elem.get('name')
            if 0 < len(name):
                self.inputs[name] = Form.Textfield(self.elem, name)
        for elem in self.elem.xpath(Form.Textarea.xpath()):
            name = elem.get('name')
            if 0 < len(name):
                self.inputs[name] = Form.Textarea(self.elem, name)
        for elem in self.elem.xpath(Form.Radiobutton.xpath()):
            name = elem.get('name')
            if 0 < len(name):
                self.inputs[name] = Form.Radiobutton(self.elem, name)
        for elem in self.elem.xpath(Form.Checkbox.xpath()):
            name = elem.get('name')
            if 0 < len(name):
                self.inputs[name] = Form.Checkbox(self.elem, name)
        for elem in self.elem.xpath(Form.Pulldown.xpath()):
            name = elem.get('name')
            if 0 < len(name):
                self.inputs[name] = Form.Pulldown(self.elem, name)

    def fill(self, params):
        try:
            print >> sys.stderr, yaml.dump(self.inputs.keys())
            keys = sorted(self.inputs.keys())
            for k in keys:
                if not params.has_key(k):
                    continue
                val = params[k]

                cmds = self.inputs[k].input(val)
                for cmd in cmds:
                    print >> sys.stderr, "%s: %s" % (cmd[1], val)
                    exec_input = getattr(self.browser.find_element_by_xpath(cmd[1]), cmd[0])
                    if cmd[2] or cmd[2] == 0 or cmd[2] == '':
                        exec_input(cmd[2])
                    else:
                        exec_input()
                    sleep(0.05) # waitいれとかないとちゃんと入力してくれない
        except Exception, e:
            traceback.print_exc()
