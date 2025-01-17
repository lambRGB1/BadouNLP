# coding:utf8

import torch
import torch.nn as nn
import numpy as np
import random
import json
import matplotlib.pyplot as plt

"""

Task:改用交叉熵实现一个多分类任务，五维随机向量最大的数字在哪维就属于哪一类。

"""


class CrossEntropyTorchModel(nn.Module):
    def __init__(self, input_size,num_classes):
        super(CrossEntropyTorchModel, self).__init__()
        self.linear = nn.Linear(input_size, num_classes)  # 输出类别数
        #self.activation = torch.sigmoid  # sigmoid归一化函数 交叉熵实现内部有归一化
        self.loss = nn.CrossEntropyLoss()  # loss 使用交叉熵

    # 当输入真实标签，返回loss值；无真实标签，返回预测值
    def forward(self, x, y=None):
        y_pred = self.linear(x) 
        if y is not None:
            return self.loss(y_pred, y)  # 预测值和真实值计算损失
        else:
            return y_pred  # 输出预测结果


# 生成一个样本, 样本的生成方法，代表了我们要学习的规律
# 随机生成一个5维向量，最大的作为标记
def create_random_sample():
    x = np.random.random(5)
    label = np.argmax(x)
    return x , label


# 随机生成一批样本
# 正负样本均匀生成
def build_dataset(total_sample_num):
    X = []
    Y = []
    for i in range(total_sample_num):
        x, y = create_random_sample()
        X.append(x)
        Y.append(y)
    return torch.FloatTensor(X), torch.LongTensor(Y)

# 测试代码
# 用来测试每轮模型的准确率
def evaluate(model):
    model.eval()
    test_sample_num = 100
    x, y = build_dataset(test_sample_num)
    correct = 0
    with torch.no_grad():
        y_pred = torch.argmax(model(x),dim = 1) #模型预测值
        correct = (y_pred == y).sum().item()  #统计预测正确的个数

    accuracy = correct / test_sample_num
    print("正确预测个数：%d, 正确率：%f" % (correct, correct / test_sample_num))
    return accuracy


def main():
    # 配置参数
    epoch_num = 20  # 训练轮数
    batch_size = 20  # 每次训练样本个数
    train_sample = 5000  # 每轮训练总共训练的样本总数
    input_size = 5  # 输入向量维度
    num_classes = 5
    learning_rate = 0.001  # 学习率
    # 建立模型
    model = CrossEntropyTorchModel(input_size,num_classes)
    # 选择优化器
    optim = torch.optim.Adam(model.parameters(), lr=learning_rate)
    log = []
    # 创建训练集，正常任务是读取训练集
    train_x, train_y = build_dataset(train_sample)
    # 训练过程
    for epoch in range(epoch_num):
        model.train() #一定要写用来激活模型
        watch_loss = []
        for batch_index in range(train_sample // batch_size):    
            x = train_x[batch_index * batch_size : (batch_index + 1) * batch_size]
            y = train_y[batch_index * batch_size : (batch_index + 1) * batch_size]
            loss = model(x, y)  # 计算loss  model.forward(x,y)
            loss.backward()  # 计算梯度
            optim.step()  # 更新权重
            optim.zero_grad()  # 梯度归零
            watch_loss.append(loss.item())
        print("=========\n第%d轮平均loss:%f" % (epoch + 1, np.mean(watch_loss)))
        acc = evaluate(model)  # 测试本轮模型结果
        log.append([acc, float(np.mean(watch_loss))])
    # 保存模型
    torch.save(model.state_dict(), "MyCrossEntropy.pt")
    # 画图
    print(log)
    plt.plot(range(len(log)), [l[0] for l in log], label="acc")  # 画acc曲线
    plt.plot(range(len(log)), [l[1] for l in log], label="loss")  # 画loss曲线
    plt.legend()
    plt.show()
    return


# 使用训练好的模型做预测
def predict(model_path, input_vec):
    input_size, num_classes = 5, 5
    model = CrossEntropyTorchModel(input_size)
    model.load_state_dict(torch.load(model_path))  # 加载训练好的权重
    print(model.state_dict())

    model.eval()  # 测试模式
    with torch.no_grad():  # 不计算梯度
        result = model.forward(torch.FloatTensor(input_vec))  # 模型预测
        predict_classes = torch.argmax(result,dim = 1) # 预测类别
    for vec, pred in zip(input_vec, predict_classes):
        print(f"输入：{vec}, 预测类别：{pred.item()}")

if __name__ == "__main__":
    main()
    test_vec = [[0.97889086,0.15229675,0.31082123,0.03504317,0.88920843],
                [0.74963533,0.5524256,0.95758807,0.95520434,0.84890681],
                [0.00797868,0.67482528,0.13625847,0.34675372,0.19871392],
                [0.09349776,0.59416669,0.92579291,0.41567412,0.1358894]]
    predict("MyCrossEntropy.pt", test_vec)
