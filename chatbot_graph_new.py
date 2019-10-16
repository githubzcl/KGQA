#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# @Time    : 2019/10/16 10:46
# @Author  : Rabin Liu
# @Site    :
# @File    : 1.py
# @Software: PyCharm
from question_classifier import *
from question_parser import *
from answer_search import *
from question_list import *
from entity_list import *
from anwser_list import *
import time
'''问答类'''
class ChatBotGraph:
    def __init__(self):
        self.classifier = QuestionClassifier()
        self.parser = QuestionPaser()
        self.searcher = AnswerSearcher()
        self.qt = Question_list()
        self.entity = Entity_list()
    def chat_main(self, sent):
        an=self.qt.answer(sent)
        answer = '您好，我是百奥知智能助理，您刚才的问题我不太明白，您是不是想问：\n{0}'.format(an)
        res_classify = self.classifier.classify(sent)
        if not res_classify:
            return answer
        res_sql = self.parser.parser_main(res_classify)
        final_answers = self.searcher.search_main(res_sql)
        if not final_answers:
            return answer
        else:
            return '\n'.join(final_answers)
    def interaction(self,question_1):
        question = ''
        if question_1 == '1':
            question = Anwser_list().a
        elif question_1 == '2':
            question = Anwser_list().b
        elif question_1 == '3':
            question = Anwser_list().c
        else:
            question = question_1

        return question


if __name__ == '__main__':

    handler = ChatBotGraph()

    while 1:
        question_i = input('用户:')
        question = handler.interaction(question_i)
        answer = handler.chat_main(handler.entity.entity(0)+question)
        print('百奥知智能助理:', answer)


