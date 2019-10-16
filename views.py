# python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'lht'
__mtime__ = '2019/10/10'
"""
from django.shortcuts import render

import json
import requests
from rest_framework.views import APIView
from dss.Serializer import serializer
from django.http import HttpResponse

import csv
import re
import time
from py2neo import Node, Relationship, Graph
import csv
import sys, getopt
import json
from collections import defaultdict
import random

test_graph = Graph('http://39.98.161.93:7474', username='neo4j', password='bioknow')

sys.path.append('')
# from question_classifier import *
# from question_parser import *
# from answer_search import *

import os
import ahocorasick


class QuestionClassifier:
    def __init__(self):
        cur_dir = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        #　特征词路径
        self.disease_path = os.path.join(cur_dir, 'dict/disease.txt')
        self.department_path = os.path.join(cur_dir, 'dict/department.txt')
        self.check_path = os.path.join(cur_dir, 'dict/check.txt')
        self.drug_path = os.path.join(cur_dir, 'dict/drug.txt')
        self.food_path = os.path.join(cur_dir, 'dict/food.txt')
        self.producer_path = os.path.join(cur_dir, 'dict/producer.txt')
        self.symptom_path = os.path.join(cur_dir, 'dict/symptom.txt')
        self.deny_path = os.path.join(cur_dir, 'dict/deny.txt')
        # 加载特征词
        self.disease_wds= [i.strip() for i in open(self.disease_path, encoding='UTF-8') if i.strip()]
        self.department_wds= [i.strip() for i in open(self.department_path, encoding='UTF-8') if i.strip()]
        self.check_wds= [i.strip() for i in open(self.check_path, encoding='UTF-8') if i.strip()]
        self.drug_wds= [i.strip() for i in open(self.drug_path, encoding='UTF-8') if i.strip()]
        self.food_wds= [i.strip() for i in open(self.food_path, encoding='UTF-8') if i.strip()]
        self.producer_wds= [i.strip() for i in open(self.producer_path, encoding='UTF-8') if i.strip()]
        self.symptom_wds= [i.strip() for i in open(self.symptom_path, encoding='UTF-8') if i.strip()]
        self.region_words = set(self.department_wds + self.disease_wds + self.check_wds + self.drug_wds + self.food_wds + self.producer_wds + self.symptom_wds)
        self.deny_words = [i.strip() for i in open(self.deny_path, encoding='UTF-8') if i.strip()]



        # 构造领域actree
        self.region_tree = self.build_actree(list(self.region_words))
        # 构建词典
        self.wdtype_dict = self.build_wdtype_dict()

        # 问句疑问词
        self.symptom_qwds = ['introduce']
        self.dosage_qwds = ['dosage','给药剂量','用量','用法','使用','给药剂量','时间']
        self.indication_qwds = ['indication','哪些疾病']
        self.contraindication_qwds = ['contraindication']
        self.disease_qwds = ['不良反应']
        self.pharmacological_study_qwds = ['pharmacological','药理研究','肝肾功能不全']
        self.toxicological_study_qwds = ['toxicological']
        self.pharmacokinetic_profile_qwds = ['pharmacokinetic']
        self.storage_qwds = ['storage']
        self.drug_qwds = []
        self.prevent_qwds = ['预防', '防范', '抵制', '抵御', '防止','躲避','逃避','避开','免得','逃开','避开','避掉','躲开','躲掉','绕开',
                             '怎样才能不', '怎么才能不', '咋样才能不','咋才能不', '如何才能不',
                             '怎样才不', '怎么才不', '咋样才不','咋才不', '如何才不',
                             '怎样才可以不', '怎么才可以不', '咋样才可以不', '咋才可以不', '如何可以不',
                             '怎样才可不', '怎么才可不', '咋样才可不', '咋才可不', '如何可不']
        self.lasttime_qwds = ['周期', '多久', '多长时间', '多少时间', '几天', '几年', '多少天', '多少小时', '几个小时', '多少年']
        self.cureway_qwds = ['怎么治疗', '如何医治', '怎么医治', '怎么治', '怎么医', '如何治', '医治方式', '疗法', '咋治', '怎么办', '咋办', '咋治']
        self.cureprob_qwds = ['多大概率能治好', '多大几率能治好', '治好希望大么', '几率', '几成', '比例', '可能性', '能治', '可治', '可以治', '可以医']
        self.easyget_qwds = ['易感人群', '容易感染', '易发人群', '什么人', '哪些人', '感染', '染上', '得上']
        self.check_qwds = ['检查', '检查项目', '查出', '检查', '测出', '试出']
        self.belong_qwds = ['属于什么科', '属于', '什么科', '科室']
        self.cure_qwds = ['治疗什么', '治啥', '治疗啥', '医治啥', '治愈啥', '主治啥', '主治什么', '有什么用', '有何用', '用处', '用途',
                          '有什么好处', '有什么益处', '有何益处', '用来', '用来做啥', '用来作甚', '需要', '要']
        self.cause_qwds = ['原因', '成因', '为什么', '怎么会', '怎样才', '咋样才', '怎样会', '如何会', '为啥', '为何', '如何才会', '怎么才会', '会导致',
                           '会造成']
        self.acompany_qwds = ['并发症', '并发', '一起发生', '一并发生', '一起出现', '一并出现', '一同发生', '一同出现', '伴随发生', '伴随', '共现']
        self.food_qwds = ['饮食', '饮用', '吃', '食', '伙食', '膳食', '喝', '菜', '忌口', '补品', '保健品', '食谱', '菜谱', '食用', '食物', '补品']
        print('model init finished ......')

        return

    '''分类主函数'''
    def classify(self, question):
        data = {}
        medical_dict = self.check_medical(question)
        if not medical_dict:
            return {}
        data['args'] = medical_dict
        #收集问句当中所涉及到的实体类型
        types = []
        for type_ in medical_dict.values():
            types += type_
        question_type = 'others'

        question_types = []

        # 症状
        if self.check_words(self.symptom_qwds, question) and ('disease' in types):
            question_type = 'disease_symptom'
            question_types.append(question_type)

        if self.check_words(self.symptom_qwds, question) and ('symptom' in types):
            question_type = 'symptom_disease'
            question_types.append(question_type)

        # 原因
        if self.check_words(self.dosage_qwds, question) and ('drug' in types):
            question_type = 'drug_dosage'
            question_types.append(question_type)
        # 并发症
        if self.check_words(self.indication_qwds, question) and ('drug' in types):
            question_type = 'drug_indication'
            question_types.append(question_type)
        if self.check_words(self.contraindication_qwds, question) and ('drug' in types):
            question_type = 'drug_contraindication'
            question_types.append(question_type)
        if self.check_words(self.pharmacological_study_qwds, question) and ('drug' in types):
            question_type = 'drug_pharmacological_study'
            question_types.append(question_type)
        if self.check_words(self.toxicological_study_qwds, question) and ('drug' in types):
            question_type = 'drug_toxicological_study'
            question_types.append(question_type)
        if self.check_words(self.pharmacokinetic_profile_qwds, question) and ('drug' in types):
            question_type = 'drug_pharmacokinetic_profile'
            question_types.append(question_type)
        if self.check_words(self.storage_qwds, question) and ('drug' in types):
            question_type = 'drug_storage'
            question_types.append(question_type)
            #推荐药品
        if self.check_words(self.drug_qwds, question) and 'disease' in types:
            question_type = 'disease_drug'
            question_types.append(question_type)
        # 药品治啥病
        if self.check_words(self.disease_qwds, question) and 'drug' in types:
            question_type = 'drug_disease'
            question_types.append(question_type)

        # 疾病接受检查项目
        if self.check_words(self.check_qwds, question) and 'disease' in types:
            question_type = 'disease_check'
            question_types.append(question_type)

        # 已知检查项目查相应疾病
        if self.check_words(self.check_qwds+self.cure_qwds, question) and 'check' in types:
            question_type = 'check_disease'
            question_types.append(question_type)

        #　症状防御

        # 疾病医疗周期
        if self.check_words(self.lasttime_qwds, question) and 'disease' in types:
            question_type = 'disease_lasttime'
            question_types.append(question_type)

        # 疾病治疗方式
        if self.check_words(self.cureway_qwds, question) and 'disease' in types:
            question_type = 'disease_cureway'
            question_types.append(question_type)

        # 疾病治愈可能性
        if self.check_words(self.cureprob_qwds, question) and 'disease' in types:
            question_type = 'disease_cureprob'
            question_types.append(question_type)

        # 疾病易感染人群
        if self.check_words(self.easyget_qwds, question) and 'disease' in types :
            question_type = 'disease_easyget'
            question_types.append(question_type)

        # 若没有查到相关的外部查询信息，那么则将该疾病的描述信息返回
        if question_types == [] and 'disease' in types:
            question_types = ['disease_desc']

        # 若没有查到相关的外部查询信息，那么则将该疾病的描述信息返回
        if question_types == [] and 'symptom' in types:
            question_types = ['symptom_disease']

        # 将多个分类结果进行合并处理，组装成一个字典
        data['question_types'] = question_types

        return data

    '''构造词对应的类型'''
    def build_wdtype_dict(self):
        wd_dict = dict()
        for wd in self.region_words:
            wd_dict[wd] = []
            if wd in self.disease_wds:
                wd_dict[wd].append('disease')
            if wd in self.department_wds:
                wd_dict[wd].append('department')
            if wd in self.check_wds:
                wd_dict[wd].append('check')
            if wd in self.drug_wds:
                wd_dict[wd].append('drug')
            if wd in self.food_wds:
                wd_dict[wd].append('food')
            if wd in self.symptom_wds:
                wd_dict[wd].append('symptom')
            if wd in self.producer_wds:
                wd_dict[wd].append('producer')
        return wd_dict

    '''构造actree，加速过滤'''
    def build_actree(self, wordlist):
        actree = ahocorasick.Automaton()
        for index, word in enumerate(wordlist):
            actree.add_word(word, (index, word))
        actree.make_automaton()
        return actree

    '''问句过滤'''
    def check_medical(self, question):
        region_wds = []
        for i in self.region_tree.iter(question):
            wd = i[1][1]
            region_wds.append(wd)
        stop_wds = []
        for wd1 in region_wds:
            for wd2 in region_wds:
                if wd1 in wd2 and wd1 != wd2:
                    stop_wds.append(wd1)
        final_wds = [i for i in region_wds if i not in stop_wds]
        final_dict = {i:self.wdtype_dict.get(i) for i in final_wds}

        return final_dict

    '''基于特征词进行分类'''
    def check_words(self, wds, sent):
        for wd in wds:
            if wd in sent:
                return True
        return False

class Anwser_list():
    a = "艾瑞卡可以用于哪些疾病的治疗？"
    b = "艾瑞卡的给药剂量是多少？"
    c = "艾瑞卡的主要不良反应是什么？"

class AnswerSearcher:
    def __init__(self):
        self.g = Graph(
            host="localhost",
            http_port=7474,
            user="neo4j",
            password="bioknow")
        self.num_limit = 200000

    '''执行cypher查询，并返回相应结果'''
    def search_main(self, sqls):
        final_answers = []
        for sql_ in sqls:
            question_type = sql_['question_type']
            queries = sql_['sql']
            answers = []
            for query in queries:
                ress = self.g.run(query).data()
                answers += ress
            final_answer = self.answer_prettify(question_type, answers)
            if final_answer:
                final_answers.append(final_answer)
        return final_answers

    '''根据对应的qustion_type，调用相应的回复模板'''
    def answer_prettify(self, question_type, answers):
        final_answer = []
        if not answers:
            return ''
        if question_type == 'disease_symptom':
            desc = [i['n.name'] for i in answers]
            subject = answers[0]['m.name']
            final_answer = '{0}\'s description：{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'symptom_disease':
            desc = [i['m.name'] for i in answers]
            subject = answers[0]['n.name']
            final_answer = '症状{0}可能染上的疾病有：{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_cause':
            desc = [i['m.cause'] for i in answers]
            subject = answers[0]['m.name']
            final_answer = '{0}可能的成因有：{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'drug_indication':
            desc = [i['m.name'] for i in answers]
            subject = answers[0]['n.name']
            final_answer = '{1}的适应症包括：{0}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_lasttime':
            desc = [i['m.cure_lasttime'] for i in answers]
            subject = answers[0]['m.name']
            final_answer = '{0}治疗可能持续的周期为：{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_cureway':
            desc = [';'.join(i['m.cure_way']) for i in answers]
            subject = answers[0]['m.name']
            final_answer = '{0}可以尝试如下治疗：{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_cureprob':
            desc = [i['m.cured_prob'] for i in answers]
            subject = answers[0]['m.name']
            final_answer = '{0}治愈的概率为（仅供参考）：{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_easyget':
            desc = [i['m.easy_get'] for i in answers]
            subject = answers[0]['m.name']

            final_answer = '{0}的易感人群包括：{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_desc':
            desc = [i['m.desc'] for i in answers]
            subject = answers[0]['m.name']
            final_answer = '{0},熟悉一下：{1}'.format(subject,  '；'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_acompany':
            desc1 = [i['n.name'] for i in answers]
            desc2 = [i['m.name'] for i in answers]
            subject = answers[0]['m.name']
            desc = [i for i in desc1 + desc2 if i != subject]
            final_answer = '{0}的症状包括：{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_not_food':
            desc = [i['n.name'] for i in answers]
            subject = answers[0]['m.name']
            final_answer = '{0}忌食的食物包括有：{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_do_food':
            do_desc = [i['n.name'] for i in answers if i['r.name'] == '宜吃']
            recommand_desc = [i['n.name'] for i in answers if i['r.name'] == '推荐食谱']
            subject = answers[0]['m.name']
            final_answer = '{0}宜食的食物包括有：{1}\n推荐食谱包括有：{2}'.format(subject, ';'.join(list(set(do_desc))[:self.num_limit]), ';'.join(list(set(recommand_desc))[:self.num_limit]))

        elif question_type == 'food_not_disease':
            desc = [i['m.name'] for i in answers]
            subject = answers[0]['n.name']
            final_answer = '患有{0}的人最好不要吃{1}'.format('；'.join(list(set(desc))[:self.num_limit]), subject)

        elif question_type == 'food_do_disease':
            desc = [i['m.name'] for i in answers]
            subject = answers[0]['n.name']
            final_answer = '患有{0}的人建议多试试{1}'.format('；'.join(list(set(desc))[:self.num_limit]), subject)

        elif question_type == 'disease_drug':
            desc = [i['n.name'] for i in answers]
            subject = answers[0]['m.name']
            final_answer = '{0}\'s related drugs include：{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'drug_disease':
            desc = [i['m.name'] for i in answers]
            subject = answers[0]['n.name']
            final_answer = '{1}不良反应有{0}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'drug_pharmacological_study':
            desc = [i['n.name'] for i in answers]
            subject = answers[0]['m.name']
            final_answer = '{0}对于肝肾功能不全的患者{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))
        elif question_type == 'drug_dosage':
            desc = [i['n.name'] for i in answers]
            subject = answers[0]['m.name']
            final_answer = '{0}的用法：{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))
        elif question_type == 'check_disease':
            desc = [i['m.name'] for i in answers]
            subject = answers[0]['n.name']
            final_answer = '通常可以通过{0}检查出来的疾病有{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))

        return final_answer




class QuestionPaser:
    '''构建实体节点'''
    def build_entitydict(self, args):
        entity_dict = {}
        for arg, types in args.items():
            for type in types:
                if type not in entity_dict:
                    entity_dict[type] = [arg]
                else:
                    entity_dict[type].append(arg)

        return entity_dict

    '''解析主函数'''
    def parser_main(self, res_classify):
        args = res_classify['args']
        entity_dict = self.build_entitydict(args)
        question_types = res_classify['question_types']
        sqls = []
        for question_type in question_types:
            sql_ = {}
            sql_['question_type'] = question_type
            sql = []
            if question_type == 'disease_symptom':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'symptom_disease':
                sql = self.sql_transfer(question_type, entity_dict.get('symptom'))

            elif question_type == 'drug_pharmacological_study':
                sql = self.sql_transfer(question_type, entity_dict.get('drug'))

            elif question_type == 'drug_dosage':
                sql = self.sql_transfer(question_type, entity_dict.get('drug'))

            elif question_type == 'disease_not_food':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'disease_do_food':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'food_not_disease':
                sql = self.sql_transfer(question_type, entity_dict.get('food'))

            elif question_type == 'food_do_disease':
                sql = self.sql_transfer(question_type, entity_dict.get('food'))

            elif question_type == 'disease_drug':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'drug_disease':
                sql = self.sql_transfer(question_type, entity_dict.get('drug'))

            elif question_type == 'disease_check':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'check_disease':
                sql = self.sql_transfer(question_type, entity_dict.get('check'))

            elif question_type == 'drug_indication':
                sql = self.sql_transfer(question_type, entity_dict.get('drug'))

            elif question_type == 'disease_lasttime':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'disease_cureway':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'disease_cureprob':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'disease_easyget':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'disease_desc':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            if sql:
                sql_['sql'] = sql

                sqls.append(sql_)

        return sqls

    '''针对不同的问题，分开进行处理'''

    def sql_transfer(self, question_type, entities):
        if not entities:
            return []

        # 查询语句
        sql = []
        # 查询疾病的原因
        if question_type == 'disease_cause':
            sql = ["MATCH (m:disease) where m.name = '{0}' return m.name, m.cause".format(i) for i in entities]

        # 查询疾病的防御措施
        elif question_type == 'disease_prevent':
            sql = ["MATCH (m:disease) where m.name = '{0}' return m.name, m.prevent".format(i) for i in entities]

        # 查询疾病的持续时间
        elif question_type == 'disease_lasttime':
            sql = ["MATCH (m:disease) where m.name = '{0}' return m.name, m.cure_lasttime".format(i) for i in entities]

        # 查询疾病的治愈概率
        elif question_type == 'disease_cureprob':
            sql = ["MATCH (m:disease) where m.name = '{0}' return m.name, m.cured_prob".format(i) for i in entities]

        # 查询疾病的治疗方式
        elif question_type == 'disease_cureway':
            sql = ["MATCH (m:disease) where m.name = '{0}' return m.name, m.cure_way".format(i) for i in entities]

        # 查询疾病的易发人群
        elif question_type == 'disease_easyget':
            sql = ["MATCH (m:disease) where m.name = '{0}' return m.name, m.easy_get".format(i) for i in entities]

        # 查询疾病的相关介绍
        elif question_type == 'disease_desc':
            sql = ["MATCH (m:disease) where m.name = '{0}' return m.name, m.desc".format(i) for i in entities]

        # 查询疾病有哪些症状
        elif question_type == 'disease_symptom':
            sql = ["MATCH (m:disease)-[r:function]->(n) where m.name = '{0}' return m.name, r.name, n.name".format(i)
                   for i in entities]

        # 查询症状会导致哪些疾病
        elif question_type == 'symptom_disease':
            sql = [
                "MATCH (m:disease)-[r:has_symptom]->(n:Symptom) where n.name = '{0}' return m.name, r.name, n.name".format(
                    i) for i in entities]

        # 查询疾病的并发症
        elif question_type == 'drug_pharmacological_study':
            sql = [
                "MATCH (m:drug)-[r]->(n:pharmacological_study) where m.name = '{0}' return m.name, r.name, n.name".format(
                    i) for i in entities]
        # 查询疾病的忌口
        elif question_type == 'drug_dosage':
            sql = ["MATCH (m:drug)-[r]->(n:dosage) where m.name = '{0}' return m.name, r.name, n.name".format(i) for i
                   in entities]
        elif question_type == 'drug_indication':
            sql = ["MATCH (m:drug)-[r]-(n:indication) where m.name = '{0}' return m.name, r.name, n.name".format(i) for
                   i in entities]
        elif question_type == 'disease_not_food':
            sql = ["MATCH (m:disease)-[r:no_eat]->(n:Food) where m.name = '{0}' return m.name, r.name, n.name".format(i)
                   for i in entities]

        # 查询疾病建议吃的东西
        elif question_type == 'disease_do_food':
            sql1 = [
                "MATCH (m:disease)-[r:do_eat]->(n:Food) where m.name = '{0}' return m.name, r.name, n.name".format(i)
                for i in entities]
            sql2 = [
                "MATCH (m:disease)-[r:recommand_eat]->(n:Food) where m.name = '{0}' return m.name, r.name, n.name".format(
                    i) for i in entities]
            sql = sql1 + sql2

        # 已知忌口查疾病
        elif question_type == 'food_not_disease':
            sql = ["MATCH (m:disease)-[r:no_eat]->(n:Food) where n.name = '{0}' return m.name, r.name, n.name".format(i)
                   for i in entities]

        # 已知推荐查疾病
        elif question_type == 'food_do_disease':
            sql1 = [
                "MATCH (m:disease)-[r:do_eat]->(n:Food) where n.name = '{0}' return m.name, r.name, n.name".format(i)
                for i in entities]
            sql2 = [
                "MATCH (m:disease)-[r:recommand_eat]->(n:Food) where n.name = '{0}' return m.name, r.name, n.name".format(
                    i) for i in entities]
            sql = sql1 + sql2

        # 查询疾病常用药品－药品别名记得扩充
        elif question_type == 'disease_drug':
            sql = ["MATCH (m:disease)-[r]-(n:drug) where m.name = '{0}' return m.name, r.name, n.name".format(i) for i
                   in entities]


        # 已知药品查询能够治疗的疾病
        elif question_type == 'drug_disease':
            sql = ["MATCH (m:drug)-[r]-(n:disease) where m.name = '{0}' return m.name, r.name, n.name".format(i) for i
                   in entities]


        # 查询疾病应该进行的检查
        elif question_type == 'disease_check':
            sql = [
                "MATCH (m:disease)-[r:need_check]->(n:Check) where m.name = '{0}' return m.name, r.name, n.name".format(
                    i) for i in entities]

        # 已知检查查询疾病
        elif question_type == 'check_disease':
            sql = [
                "MATCH (m:disease)-[r:need_check]->(n:Check) where n.name = '{0}' return m.name, r.name, n.name".format(
                    i) for i in entities]

        return sql

class Entity_list:
    def entity(self, sent):
        entity_name = '艾瑞卡'
        return entity_name
    
# Initialize generator
def print_run_time(func):
    """
    装饰器：计算时间函数
    :param func:
    :return:
    """

    def wrapper(*args, **kw):
        local_time = time.time()
        f = func(*args, **kw)
        print('Function [%s] run time is %.2f' % (func.__name__, time.time() - local_time))
        return f

    return wrapper


def index(request):
    return render(request, 'index.html')


@print_run_time
def nmt_function(request):
    eid = request.POST.get('abstract')
    print(eid)
    # sentences = get_sentences(abstract)
    url = 'http://39.98.161.93:8001/api/?eid={0}'

    result_dict = requests.get(url.format(eid))
    # print(result_dict)
    # time.sleep(100)

    str1 = result_dict.json()

    #str1 = json.loads(str1)
    #print(str1)

    abstract_text_str = str1['data']
    abstr=[]
    abstr.append(abstract_text_str)    #abstract_text_str=list(abstract_text_str)
    # print(type(abstract_text_str)
    # abstract_text_str+='\n'
    # abstract_text_str+=str1['data']['graph']
    # print(type(abstract_text_str))
    # abstract_text.append(abstract_text_str)

    return render(request, 'index.html', {
        'nmt_result': abstr,
        'abstract_en': eid,
    })


def response_as_json(data, foreign_penetrate=False):
    # jsonString = serializer(data=data, output_type="json", foreign=foreign_penetrate)
    response = HttpResponse(
        # json.dumps(dataa, cls=MyEncoder),
        data,
        content_type="application/json",
    )
    response["Access-Control-Allow-Origin"] = "*"
    return response


def json_response(data, code=200, foreign_penetrate=False, **kwargs):
    data = {
        "code": code,
        "msg": "Success!",
        "data": data,
    }
    data = json.dumps(data)
    print('data:' + data)
    print(type(data))
    return response_as_json(data, foreign_penetrate=foreign_penetrate)


def json_error(error_string="", code=500, **kwargs):
    data = {
        "code": code,
        "msg": error_string,
        "data": {}
    }
    data.update(kwargs)
    return response_as_json(data)


JsonResponse = json_response
JsonError = json_error


class ReturnJson(APIView):

    def get(self, request, *args, **kwargs):
        con = ''
        query = request.query_params
        # print(query)
        eid = query['eid']
        print(eid)
        content = eid.split('+')
        print(content)
        ab_len = len(content)

        if ab_len > 2:
            return JsonError("content too much!: {0}".format(eid))
        elif ab_len == 2:
            result = handle_data(eid)
        else:
            result = handle_data(eid)
        if result == 'error':
            return JsonError("no result! :{0}".format(eid))
        # print(result)
        return JsonResponse(result)

class Question_list:

    def answer(self,sent):
        question1 = '1.艾瑞卡可以用于哪些疾病的治疗？\n2.艾瑞卡的用药剂量是多少？\n3. 艾瑞卡的主要不良反应是什么？'
        return question1
    def entity(self,sent):
        entity = '艾瑞卡'
        return entity

class ChatBotGraph:
    def __init__(self):
        self.classifier = QuestionClassifier()
        self.parser = QuestionPaser()
        self.searcher = AnswerSearcher()
        self.qt = Question_list()
        self.entity = Entity_list()

    def chat_main(self, sent):
        an = self.qt.answer(sent)
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

    def interaction(self, question_1):
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

handler =ChatBotGraph()

def handle_data(question_information, *name):
    """
    run 得到的结果格式：
    查询节点信息得到的结果：
     [{'n': (_9282:author {eid: 999998, impactFactor: '1', name_cn: '\u7c7b\u98ce\u6e7f\u6027\u5173\u8282\u708e', name_en: 'Rheumatoid', pi_cn: 'none', pid: '0', pmid_count: '0'})}]

    :param eid:
    :param name:
    :return:
    """

    

    tm = time.time()
    question_i = question_information
    question = handler.interaction(question_i)
    answer = handler.chat_main(handler.entity.entity(0) + question)
    print('百奥知智能助理:', answer)
    print(time.time() - tm)
    return answer
   
    
