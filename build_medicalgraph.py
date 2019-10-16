import os
import json
from py2neo import Graph,Node

class MedicalGraph:
    def __init__(self):
        cur_dir = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        self.data_path = os.path.join(cur_dir, 'data/disease.json')
        self.g = Graph(
            host="localhost",  # neo4j 搭载服务器的ip地址，ifconfig可获取到
            http_port=7474,  # neo4j 服务器监听的端口号
            user="neo4j",  # 数据库user name，如果没有更改过，应该是neo4j
            password="bioknow")

    '''读取文件'''
    def read_nodes(self):
        # 共７类节点
        drugs = [] # 药品
        foods = [] #　食物
        checks = [] # 检查
        departments = [] #科室
        producers = [] #药品大类
        diseases = [] #疾病
        symptoms = []#症状

        drug_infos = []#疾病信息

        # 构建节点实体关系
        rels_disease = [] # 疾病－通用药品关系
        rels_check = [] # 疾病－检查关系
        rels_drug_producer = [] # 厂商－药物关系

        rels_symptom = [] #疾病症状关系
        rels_acompany = [] # 疾病并发关系
        rels_category = [] #　疾病与科室之间的关系


        count = 0
        #print(json.load(open(self.data_path,encoding='UTF-8')))
        for data_json in json.load(open(self.data_path,encoding='UTF-8')):
            drug_dict = {}
            count += 1
            print(count)
            #data_json = json.loads(data)
            drug = data_json['name']
            drug_dict['name'] = drug
            drugs.append(drug)
            drug_dict['dosage'] = ''
            drug_dict['prevent'] = ''
            drug_dict['gene'] = ''
            drug_dict['easy_get'] = ''
            drug_dict['cure_department'] = ''
            drug_dict['cure_way'] = ''
            drug_dict['cure_lasttime'] = ''
            drug_dict['symptom'] = ''
            drug_dict['cured_prob'] = ''
            drug_dict['indication'] = ''
            drug_dict['contraindication'] = ''
            drug_dict['pharmacological_study'] = ''
            drug_dict['toxicological_study'] = ''
            drug_dict['pharmacokinetic_profile'] = ''
            drug_dict['storage'] = ''

            if 'symptom' in data_json:
                symptoms += data_json['symptom']
                for symptom in data_json['symptom']:
                    rels_symptom.append([disease, symptom])
            if 'dosage' in data_json:
                drug_dict['dosage'] = data_json['dosage']
            if 'gene' in data_json:
                drug_dict['gene'] = data_json['gene']
            if 'contraindication' in data_json:
                drug_dict['contraindication'] = data_json['contraindication']
            if 'pharmacological_study' in data_json:
                drug_dict['pharmacological_study'] = data_json['pharmacological_study']
            if 'toxicological_study' in data_json:
                drug_dict['toxicological_study'] = data_json['toxicological_study']
            if 'pharmacokinetic_profile' in data_json:
                drug_dict['pharmacokinetic_profile'] = data_json['pharmacokinetic_profile']
            if 'pharmacokinetic_profile' in data_json:
                drug_dict['pharmacokinetic_profile'] = data_json['pharmacokinetic_profile']
            if 'storage' in data_json:
                drug_dict['storage'] =  data_json['storage']
            if 'validity' in data_json:
                drug_dict['gene'] = data_json['validity']
            if 'indication' in data_json:
                drug_dict['indication'] =  data_json['indication']
            if 'disease' in data_json:
                recommand_disease = data_json['disease']
                diseases += recommand_disease
                for disease in recommand_disease:
                    rels_disease.append([drug, disease])
            drug_infos.append(drug_dict)
        print(drug_infos)
        print(rels_disease)
        return set(drugs), set(foods), set(checks), set(departments), set(producers), set(symptoms),set(diseases),drug_infos,\
             set(rels_disease),\

    '''建立节点'''
    def create_node(self, label, nodes):
        count = 0
        for node_name in nodes:
            node = Node(label, name=node_name)
            self.g.create(node)
            count += 1
            print(count, len(nodes))
        return

    '''创建知识图谱中心疾病的节点'''
    def create_drugs_nodes(self, drug_infos):
        count = 0
        for drug_dict in drug_infos:
            node = Node("Drug", name=drug_dict['name'], dosage=drug_dict['dosage'],
                        gene=drug_dict['gene'],indication=drug_dict['indication'],contraindication=drug_dict['contraindication'],pharmacological_study=drug_dict['pharmacological_study'],
                        toxicological_study=drug_dict['toxicological_study'],pharmacokinetic_profile=drug_dict['pharmacokinetic_profile'],storage=drug_dict['storage'],validity=drug_dict['validity']
                        ,cure_way=drug_dict['cure_way'] , cured_prob=drug_dict['cured_prob'])
            self.g.create(node)
            count += 1
            print(count)
        return

    '''创建知识图谱实体节点类型schema'''
    def create_graphnodes(self):
        Drugs, Foods, Checks, Departments, Producers, Symptoms, Diseases, disease_infos,rels_check, rels_recommandeat, rels_noteat, rels_doeat, rels_department, rels_commonddrug, rels_drug_producer, rels_recommanddisease,rels_symptom, rels_acompany, rels_category = self.read_nodes()
        self.create_drugs_nodes()
        self.create_node('Disease', Diseases)
        print(len(Diseases))
        self.create_node('Food', Foods)
        print(len(Foods))
        self.create_node('Check', Checks)
        print(len(Checks))
        self.create_node('Department', Departments)
        print(len(Departments))
        self.create_node('Producer', Producers)
        print(len(Producers))
        self.create_node('Symptom', Symptoms)
        return


    '''创建实体关系边'''
    def create_graphrels(self):
        Drugs, Foods, Checks, Departments, Producers, Symptoms, Diseases, disease_infos, rels_check, rels_recommandeat, rels_noteat, rels_doeat, rels_department, rels_commonddrug, rels_drug_producer, rels_recommanddrug,rels_symptom, rels_acompany, rels_category = self.read_nodes()
        self.create_relationship('Department', 'Department', rels_department, 'belongs_to', '属于')
        self.create_relationship('Drug', 'Disease', rels_recommanddrug, 'recommand_disease', '好评药品')
        self.create_relationship('Disease', 'Check', rels_check, 'need_check', '诊断检查')
        self.create_relationship('Disease', 'Symptom', rels_symptom, 'has_symptom', '症状')
        self.create_relationship('Disease', 'Disease', rels_acompany, 'acompany_with', '并发症')
        self.create_relationship('Disease', 'Department', rels_category, 'belongs_to', '所属科室')

    '''创建实体关联边'''
    def create_relationship(self, start_node, end_node, edges, rel_type, rel_name):
        count = 0
        # 去重处理
        set_edges = []
        for edge in edges:
            set_edges.append('###'.join(edge))
        all = len(set(set_edges))
        for edge in set(set_edges):
            edge = edge.split('###')
            p = edge[0]
            q = edge[1]
            query = "match(p:%s),(q:%s) where p.name='%s'and q.name='%s' create (p)-[rel:%s{name:'%s'}]->(q)" % (
                start_node, end_node, p, q, rel_type, rel_name)
            try:
                self.g.run(query)
                count += 1
                print(rel_type, count, all)
            except Exception as e:
                print(e)
        return

    '''导出数据'''
    def export_data(self):
        #Drugs, Diseases= self.read_nodes()
        Drugs = self.read_nodes()
        Diseases = self.read_nodes()
        drug_infos = self.read_nodes()
        f_drug = open(r'dict/drug1.txt', 'w+')
        f_disease = open(r'dict/disease1.txt', 'w+')
        f_drug.write('\n'.join(list(Drugs)))
        f_disease.write('\n'.join(list(Diseases)))
        f_drug.close()
        f_disease.close()

        return



if __name__ == '__main__':
    handler = MedicalGraph()
    handler.export_data()
