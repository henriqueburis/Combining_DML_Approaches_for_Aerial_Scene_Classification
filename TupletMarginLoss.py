import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision.models as models
import argparse
from torchvision import datasets, transforms
from pytorch_metric_learning import distances, losses, miners, reducers, testers
from pytorch_metric_learning.utils.accuracy_calculator import AccuracyCalculator
import os

parser = argparse.ArgumentParser(description="Train TupletMarginLoss")
parser.add_argument("--data_dir", required=True, type=str, help="Path to data parent directory.")
parser.add_argument("--test", required=True, type=str, help="Path to data parent directory.")
parser.add_argument("--max_epochs", default=200, type=int, help="Maximum training length (epochs).")
parser.add_argument("--batch_size", default=32, type=int, help="Batch size.")
parser.add_argument("--input_size", default=32, type=int, help="input size img.")
parser.add_argument("--name", default=" ", required=True, type=str, help="informação.")
args = parser.parse_args()

seed = "TupletMarginLoss_"+args.name
print('seed==>',seed)

result_model = list()
result_model.append("SEED::  "+str(seed)+ "\n")
result_model.append("============================= \n")

### MNIST code originally from https://github.com/pytorch/examples/blob/master/mnist/main.py ###
def train(model, loss_func, device, train_loader, optimizer, epoch):
    model.train()
    for batch_idx, (data, labels) in enumerate(train_loader):
        data, labels = data.to(device), labels.to(device)
        optimizer.zero_grad()
        embeddings = model(data)
        loss = loss_func(embeddings, labels)
        loss.backward()
        optimizer.step()
        if batch_idx % 20 == 0:
            print(
                "Epoch {} Iteration {}: Loss = {} ".format(
                    epoch, batch_idx, loss
                )
            )


### convenient function from pytorch-metric-learning ###
def get_all_embeddings(dataset, model):
    tester = testers.BaseTester()
    return tester.get_all_embeddings(dataset, model)


### compute accuracy using AccuracyCalculator from pytorch-metric-learning ###
def test(train_set, test_set, model, accuracy_calculator):
    train_embeddings, train_labels = get_all_embeddings(train_set, model)
    test_embeddings, test_labels = get_all_embeddings(test_set, model)
    train_labels = train_labels.squeeze(1)
    test_labels = test_labels.squeeze(1)
    print("Computing accuracy")
    accuracies = accuracy_calculator.get_accuracy(
        test_embeddings, train_embeddings, test_labels, train_labels, False
    )
    print("Test set accuracy (Precision@1) = {}".format(accuracies["precision_at_1"]))
    return accuracies["precision_at_1"]


device = torch.device("cuda")

transform = transforms.Compose(
    [transforms.Resize((args.input_size,args.input_size)), transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))]
)



path_train_xl = os.path.abspath(args.data_dir)
path_test = os.path.abspath(args.test)


dataset1 = datasets.ImageFolder(path_train_xl, transform=transform)
train_loader = torch.utils.data.DataLoader(dataset1,
                                          batch_size=args.batch_size,
                                          shuffle=True)


dataset2 = datasets.ImageFolder(path_test, transform=transform)
test_loader = torch.utils.data.DataLoader(dataset2, batch_size=args.batch_size,
                                         shuffle=False)

net = models.resnet50(pretrained=True)
#Remove fully connected layer
modules = list(net.children())[:-1]
modules.append(nn.Flatten())
net = nn.Sequential(*modules)


model = net.to(device)
optimizer = optim.Adam(model.parameters(), lr=0.001) #original 0.01 
num_epochs = args.max_epochs


### pytorch-metric-learning stuff ###
#loss_func = losses.TupletMarginLoss(margin=5.73, scale=64)

main_loss = losses.TupletMarginLoss()
var_loss = losses.IntraPairVarianceLoss()
loss_func = losses.MultipleLosses([main_loss, var_loss], weights=[1, 0.5])

accuracy_calculator = AccuracyCalculator(include=("precision_at_1",), k=1)
### pytorch-metric-learning stuff ###

for epoch in range(1, num_epochs + 1):
    train(model, loss_func, device, train_loader, optimizer, epoch)
    #test(dataset1, dataset2, model, accuracy_calculator)

print("Teste")
acc = test(dataset1, dataset2, model, accuracy_calculator)


#result_model.append("============================= \n")
result_model.append("ACC_Test::  "+str(acc)+ "\n")

arquivo = open(seed+".txt", "a")
arquivo.writelines(result_model)
arquivo.close()
