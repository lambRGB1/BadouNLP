import random
import json
import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt

class TorchModel(nn.Module):
    def __init__(self, vector_dim, sentence_length, vocab):
        super(TorchModel, self).__init__()
        self.embedding = nn.Embedding(len(vocab), vector_dim)
        self.rnn = nn.RNN(vector_dim, vector_dim, batch_first=True)
        self.classify = nn.Linear(vector_dim, sentence_length + 1)
        self.loss = nn.CrossEntropyLoss()

    def forward(self, x, y=None):
        x = self.embedding(x)
        rnn_out, hidden = self.rnn(x)
        x=rnn_out[:, -1, :]

        y_pred = self.classify(x)
        if y is not None:
            return self.loss(y_pred, y)
        else:
            return y_pred

def build_vocab():
    chars = "qwertyuioplkjhgfdsazxcvbnm"
    vocab_file = {"pad":0}
    for index, char in enumerate(chars):
        vocab_file[char] = index+1
    vocab_file["unk"] = len(vocab_file)
    return vocab_file

def build_sample(vocab_file, sentence):
    x = random.sample(list(vocab_file), sentence)
    if "w" in x:
        y = x.index("w")
    else:
        y = sentence
    x = [vocab_file.get(word, vocab_file['unk']) for word in x]
    return x, y

def build_dataset(sample_length, vocab_file, sentence):
    dataset_x = []
    dataset_y = []
    for i in range(sample_length):
        x, y = build_sample(vocab_file, sentence)
        dataset_x.append(x)
        dataset_y.append(y)
    return torch.LongTensor(dataset_x), torch.LongTensor(dataset_y)


def build_model(vocab_file, char_dim, sentence):
    model = TorchModel(char_dim, sentence, vocab_file)
    return model

def evaluate(model, vocab_file, sentence):
    model.eval()
    x, y = build_dataset(100, vocab_file, sentence)
    print("预测集中有%d个样本"%(len(y)))
    correct = 0
    wrong = 0
    with torch.no_grad():
        y_pred = model(x)
        for y_p, y_t in zip(y_pred, y):
            if int(y_t) == int(torch.argmax(y_p)):
                correct += 1
            else:
                wrong += 1
    print("正确率%f"%(correct/(correct + wrong)))
    return correct/(correct + wrong)

def main():
    epoch_num = 20        #训练轮数
    batch_size = 40       #每次训练样本个数
    train_sample = 1000    #每轮训练总共训练的样本总数
    char_dim = 30         #每个字的维度
    sentence_length = 10   #样本文本长度
    learning_rate = 0.001 #学习率
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
    torch.save(model.state_dict(), "model.pth")
    # 保存词表
    writer = open("vocab.json", "w", encoding="utf8")
    writer.write(json.dumps(vocab, ensure_ascii=False, indent=2))
    writer.close()
    return


def predict(model_path, vocab_path, input_strings):
    char_dim = 30  # 每个字的维度
    sentence_length = 10  # 样本文本长度
    vocab = json.load(open(vocab_path, "r", encoding="utf8")) #加载字符表
    model = build_model(vocab, char_dim, sentence_length)     #建立模型
    model.load_state_dict(torch.load(model_path))             #加载训练好的权重
    x = []
    for input_string in input_strings:
        x.append([vocab[char] for char in input_string])  #将输入序列化
    model.eval()   #测试模式
    with torch.no_grad():  #不计算梯度
        result = model.forward(torch.LongTensor(x))  #模型预测
    for i, input_string in enumerate(input_strings):
        print("输入：%s, 预测类别：%s, 概率值：%s" % (input_string, torch.argmax(result[i]), result[i])) #打印结果

if __name__ == "__main__":
    main()
    test_strings = ["ertyuiosdf", "plmjuytfds", "wertyujnbv", "pokhvcxwer"]
    predict("model.pth", "vocab.json", test_strings)
