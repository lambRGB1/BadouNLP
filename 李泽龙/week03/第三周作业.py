#coding:utf8
import os

os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
import torch
import torch.nn as nn
import numpy as np
import random
import json
import matplotlib.pyplot as plt

"""

基于pytorch的网络编写
实现一个网络完成一个简单nlp任务
判断文本中是否有某些特定字符出现

"""

class TorchModel(nn.Module):
    def __init__(self, vector_dim, sentence_length, vocab):
        super(TorchModel, self).__init__()
        self.embedding = nn.Embedding(len(vocab), vector_dim, padding_idx=0)  #embedding层
        self.pool = nn.AdaptiveAvgPool1d(1)   #池化层
        self.rnn = nn.RNN(vector_dim, 7, bias=False, batch_first = True)     #线性层
        self.fc = nn.Linear(7,7)                                  
        #self.activation = torch.sigmoid     #sigmoid归一化函数
        self.loss = nn.CrossEntropyLoss()  #loss函数采用均方差损失

    #当输入真实标签，返回loss值；无真实标签，返回预测值
    def forward(self, x, y=None):
        x = self.embedding(x)                      #(batch_size, sen_len) -> (batch_size, sen_len, vector_dim)
        x = x.transpose(1, 2)                      #(batch_size, sen_len, vector_dim) -> (batch_size, vector_dim, sen_len)
        x = self.pool(x)                           #(batch_size, vector_dim, sen_len)->(batch_size, vector_dim, 1)
        x = x.squeeze(2)                            #(batch_size, vector_dim, 1) -> (batch_size, vector_dim)
        x, _ = self.rnn(x.unsqueeze(1))
        x = x[:, -1, :]
        y_pred = self.fc(x)                             #(batch_size, vector_dim) -> (batch_size, 1) 3*5 5*1 -> 3*1
        #y_pred = self.activation(x)                #(batch_size, 1) -> (batch_size, 1)
        if y is not None:
            return self.loss(y_pred, y)   #预测值和真实值计算损失
        else:
            return y_pred                 #输出预测结果

#字符集随便挑了一些字，实际上还可以扩充
#为每个字生成一个标号
#{"a":1, "b":2, "c":3...}
#abc -> [1,2,3]
def build_vocab():
    chars = "你我他defghijklmnopqrstuvwxyz"  #字符集
    vocab = {"pad":0}
    for index, char in enumerate(chars):
        vocab[char] = index+1   #每个字对应一个序号
    vocab['unk'] = len(vocab) #26
    return vocab

#随机生成一个样本
#从所有字中选取sentence_length个字
#反之为负样本
def build_sample(vocab, sentence_length):
    #随机从字表选取sentence_length个字，可能重复
    x = [random.choice(list(vocab.keys())) for _ in range(sentence_length)]
    y = None
    #指定哪些字出现时为正样本
    for index, word in enumerate(x):
        if word == "你":
            y = index
            break
        if y is None:
            y = 6    
    x = [vocab.get(word, vocab['unk']) for word in x]   #将字转换成序号，为了做embedding
    return x, y

#建立数据集
#输入需要的样本数量。需要多少生成多少
def build_dataset(sample_length, vocab, sentence_length):
    dataset_x = []
    dataset_y = []
    for i in range(sample_length):
        x, y = build_sample(vocab, sentence_length)
        dataset_x.append(x)
        dataset_y.append(y)
    return torch.LongTensor(dataset_x), torch.LongTensor(dataset_y)

#建立模型
def build_model(vocab, char_dim, sentence_length):
    model = TorchModel(char_dim, sentence_length, vocab)
    return model

#测试代码
#用来测试每轮模型的准确率
def evaluate(model, vocab, sample_length):
    model.eval()
    x, y = build_dataset(200, vocab, sample_length)   #建立200个用于测试的样本
    counts = torch.bincount(y, minlength=7)
    print(y)
    print("本次测试样本中第一类样本为:%d\t第二类样本为:%d\t第三类样本为:%d\t第四类样本为:%d\t第五类样本为:%d\t第六类样本为:%d\t特殊类样本为:%d\t" % (counts[0],counts[1],counts[2],counts[3],counts[4],counts[5],counts[6]))
    correct, error = 0, 0
    with torch.no_grad():
        y_pred = model(x)
        #print("y_pred is:", y_pred)
        #模型预测
        z = zip(y_pred, y)
        #print("z is :", z)
        for y_p, y_t in zip(y_pred, y):  #与真实标签进行对比
            #print(y_p)
            #print("y_t is ", y_t)
            if np.argmax(y_p) == y_t:
                correct += 1
            else:
                error += 1
    print("正确预测个数：%d, 正确率：%f"%(correct, correct/(correct+error)))
    return correct/(correct+error)


def main():
    #配置参数
    epoch_num = 100        #训练轮数
    batch_size = 50       #每次训练样本个数
    train_sample = 500    #每轮训练总共训练的样本总数
    char_dim = 20         #每个字的维度
    sentence_length = 7   #样本文本长度
    learning_rate = 0.008 #学习率
    # 建立字表
    vocab = build_vocab()
    # 建立模型
    model = build_model(vocab, char_dim, sentence_length)
    # 选择优化器
    optim = torch.optim.Adam(model.parameters(), lr=learning_rate)
    log = []
    # 训练过程
    for epoch in range(epoch_num):
        model.train()
        watch_loss = []
        for batch in range(int(train_sample / batch_size)):
            x, y = build_dataset(batch_size, vocab, sentence_length) #构造一组训练样本
            optim.zero_grad()    #梯度归零
            loss = model(x, y)   #计算loss
            loss.backward()      #计算梯度
            optim.step()         #更新权重
            watch_loss.append(loss.item())
        print("=========\n第%d轮平均loss:%f" % (epoch + 1, np.mean(watch_loss)))
        acc = evaluate(model, vocab, sentence_length)   #测试本轮模型结果
        log.append([acc, np.mean(watch_loss)])
    #画图
    plt.plot(range(len(log)), [l[0] for l in log], label="acc")  #画acc曲线
    plt.plot(range(len(log)), [l[1] for l in log], label="loss")  #画loss曲线
    plt.legend()
    plt.show()
    #保存模型
    torch.save(model.state_dict(), "model_1.pth")
    # 保存词表
    writer = open("vocab.json", "w", encoding="utf8")
    writer.write(json.dumps(vocab, ensure_ascii=False, indent=2))
    writer.close()
    return

#使用训练好的模型做预测
def predict(model_path, vocab_path, input_strings):
    char_dim = 20  # 每个字的维度
    sentence_length = 6+1  # 样本文本长度
    vocab = json.load(open(vocab_path, "r", encoding="utf8")) #加载字符表
    model = build_model(vocab, char_dim, sentence_length)     #建立模型
    model.load_state_dict(torch.load(model_path))             #加载训练好的权重
    model.eval()   #测试模式
    x = []
    for input_string in input_strings:
        x.append([vocab.get(char, vocab['unk']) for char in input_string])  #将输入序列化，使用vocab.get避免KeyError
    x = torch.LongTensor(x)  # 确保输入是 LongTensor
    with torch.no_grad():  #不计算梯度
        result = model(x, None)  #模型预测，注意这里传入 None 作为 y 参数
    for i, input_string in enumerate(input_strings):
        # 使用softmax函数将logits转换为概率值
        probabilities = torch.nn.functional.softmax(result[i], dim=0)
        predicted_class = torch.argmax(probabilities)
        print("输入：%s, 预测类别：%d, 概率值：%f" % (input_string, predicted_class.item(), probabilities[predicted_class].item())) #打印结果



if __name__ == "__main__":
    main()
    test_strings = ["fnvfee", "w你sdfg", "aqw你eg", "a我kwww"]
    predict("model_1.pth", "vocab.json", test_strings)

