    def formatData(self, data, minSeq, maxSeq):
        nData = sum([(min(maxSeq + 1, len(x)) - minSeq) + (len(x) - maxSeq - 1) for x in data])# * 2
        fData = np.zeros((nData, maxSeq))
        fLabels = np.zeros((nData, 1))
        p = 0
        for i in data:
            for j in range(minSeq, min(maxSeq + 1, len(i))):
                fData[p, :j] = i[:j]
                fLabels[p] = i[j]
                #fData[p + 1, :j] = [x for x in reversed(i[-j:])]
                #fLabels[p + 1] = i[-j - 1]
                p += 1
            for j in range(len(i) - maxSeq - 1):
                fData[p] = i[j + 1 : maxSeq + j + 1]
                fLabels[p] = i[maxSeq + j + 1]
                p += 1
        fLabels = to_categorical(fLabels.astype('int'), len(self.vocab))
        return (fData, fLabels)

    def genModel(self):
        model = Sequential()
        model.add(Embedding(len(self.vocab), 64, mask_zero = True))
        model.add(LSTM(128))
        model.add(Dense(128))
        model.add(Dense(len(self.vocab)))
        model.add(Activation('softmax'))
        rms = RMSprop(lr = 0.001)
        model.compile(optimizer = rms, loss = 'categorical_crossentropy', metrics = ['accuracy'])
        return model
