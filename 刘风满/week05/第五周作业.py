#!/usr/bin/env python3
#coding: utf-8

#基于训练好的词向量模型进行聚类
#聚类采用Kmeans算法
import math
import re
import json
import jieba
import numpy as np
from gensim.models import Word2Vec
from sklearn.cluster import KMeans
from collections import defaultdict

#输入模型文件路径
#加载训练好的模型
def load_word2vec_model(path):
    model = Word2Vec.load(path)
    return model

def load_sentence(path):
    sentences = set()
    with open(path, encoding="utf8") as f:
        for line in f:
            sentence = line.strip()
            sentences.add(" ".join(jieba.cut(sentence)))
    print("获取句子数量：", len(sentences))
    return sentences

#将文本向量化
def sentences_to_vectors(sentences, model):
    vectors = []
    for sentence in sentences:
        words = sentence.split()  #sentence是分好词的，空格分开
        vector = np.zeros(model.vector_size)
        #所有词的向量相加求平均，作为句子向量
        for word in words:
            try:
                vector += model.wv[word]
            except KeyError:
                #部分词在训练中未出现，用全0向量代替
                vector += np.zeros(model.vector_size)
        vectors.append(vector / len(words))
    return np.array(vectors)


def main():
    model = load_word2vec_model(r"model.w2v") #加载词向量模型
    sentences = load_sentence("titles.txt")  #加载所有标题
    vectors = sentences_to_vectors(sentences, model)   #将所有标题向量化

    n_clusters = int(math.sqrt(len(sentences)))  #指定聚类数量
    print("指定聚类数量：", n_clusters)
    kmeans = KMeans(n_clusters)  #定义一个kmeans计算类
    kmeans.fit(vectors)          #进行聚类计算

    sentence_label_dict = defaultdict(list)
    sentence_distance_dict=defaultdict(list)
    clusters_distance=kmeans.transform(vectors)
    for sentence, label,dis_allcenter in zip(sentences, kmeans.labels_,clusters_distance):  #取出句子和标签
        sentence_label_dict[label].append(sentence)         #同标签的放到一起
        #调用kmeans的transform计算质心距离
        dis_min=np.min(dis_allcenter)
        dis_min_index=np.argmin(dis_allcenter)
        if label==dis_min_index:
            sentence_distance_dict[label].append(dis_min)
        else:
            print("计算异常，最小距离的下标与当前label不一致")
        #自定义计算点距离质心的距离
        zhixin_center=kmeans.cluster_centers_[label]



    for label, sentences in sentence_label_dict.items():
        print("cluster %s :" % label)
        print("整个聚类平均距离：%f"%np.mean(sentence_distance_dict[label]))
        sort_index=np.argsort(sentence_distance_dict[label])
        for i in range(min(10,len(sort_index))):
            print("%s ,调用kmeans的transform计算距离质心：%f"%(sentences[sort_index[i]].replace(" ",""),sentence_distance_dict[label][sort_index[i]]))
        # for i in range(min(10, len(sentences))):  #随便打印几个，太多了看不过来
        #     print(sentences[i].replace(" ", ""))
        print("---------")

if __name__ == "__main__":
    main()

