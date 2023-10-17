import torch

from models import GAT


class SGDTimeOnParticlePos():
    def __init__(self,listOfParameters):
        torch.cuda.empty_cache()
        torch.set_grad_enabled(True)
        self.criterion = torch.nn.CrossEntropyLoss()
        self.model = GAT
        self.model = self.model(nfeat=listOfParameters[0],
                                nhid=listOfParameters[1],
                                nclass=listOfParameters[2],
                                dropout=listOfParameters[3],
                                nheads=listOfParameters[8],
                                alpha=listOfParameters[9]
                                )
        self.features = listOfParameters[4]
        self.adj = listOfParameters[5]
        self.train_lst = listOfParameters[6]
        self.target = listOfParameters[7]
        # self.optimizer = torch.optim.SGD(self.model.parameters(),lr=0.02, momentum=0.9)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.02)
        # args = parameter_parser()
        # args.dataset = self.dataset
        # self.predata = PrepareData(args)


    def accuracy(self,pred_y, y):
        return (pred_y == y).sum() / len(y)

    def train(self):
        self.model.train()
        self.optimizer.zero_grad()  # Clear gradients.

        # out, h = self.model(data.x, data.edge_index)  # Perform a single forward pass.
        # loss = self.criterion(out, data.y)
        output = self.model(self.features, self.adj)
        loss = self.criterion(output[self.train_lst],
                              self.target[self.train_lst])
        loss.backward()  # Derive gradients.

        self.optimizer.step()  # Update parameters based on gradients.



        return loss

    def changeWeights(self,newWeights):
        for i in range(len(newWeights)):
            for j in range(len(self.optimizer.param_groups[i]['params'])):
                self.optimizer.param_groups[i]['params'][j].data = newWeights[i]['params'][j].data

    def itsTimeIthink(self):
        l = ""
        for epoch in range(50):
            loss = self.train()
        return self.optimizer.param_groups
    
