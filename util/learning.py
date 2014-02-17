import re
import numpy as np
import case, linguistics, data

from sklearn.feature_extraction import DictVectorizer
v = DictVectorizer(sparse=True)

def readLabels(trainingData):
    def convertWordToLabel(word):
        conversion = {'Appellant':1, 'Respondent':2, 'Trial':3, 'We':4} #Save 0 for unimportant
        return conversion[word]
    def processLabels(summary, caseSentences):
        ret = []
        importantIndices = []
        for lineAndLabel in summary.split('\n'):
            line, englishLabel = lineAndLabel.split(' ')
            label = convertWordToLabel(englishLabel)
            line = int(line)
            importantIndices.append(line)
            ret.append((line, label))
        for i, sentence in enumerate(caseSentences):
            if i not in importantIndices:
                ret.append((i, 0))
        return ret
    labeledTraining = []
    unlabeledTraining = []
    for cas in trainingData:
        folderName = cas.googleURL
        try:
            with open('cases/' + cas.googleURL + '/referenceSummary.txt', 'r') as f:
                summary = f.read() #Labeled
                cas.labels = processLabels(summary, cas.sentences)
        except IOError: #Not labeled
            cas.labels = None
    return None

def getFeatures(sentence, srlSentence):
    featureDict = {}
    for clause in srlSentence:
        """
        if 'A0' in clause:
            featureDict[('A0', clause['A0'])] = 1
        if 'V' in clause:
            featureDict[('V', clause['V'])] = 1
        """
        if 'A0' in clause and 'V' in clause:
            featureDict[(clause['A0'], clause['V'])] = 1
    return featureDict

def makeSVM(trainingData):
    def getXAndY():
        XDicts = []
        Y = []
        for cas in trainingData:
            for i, label in cas.labels:
                XDicts.append(getFeatures(cas.sentences[i], cas.srlSentences[i]))
                Y.append(label)
        X = v.fit_transform(XDicts)
        return (X, Y)
    from sklearn import svm
    readLabels(trainingData) #All trainingData should be labeled
    (X, Y) = getXAndY()
    clf = svm.SVC(class_weight={0:1, 1:500, 2:500, 3:500, 4:500}) #one against one
    clf.fit(X, Y)
    return clf

def votingAlgorithm(dfResult, numClasses=5):
    votes = np.zeros(numClasses)
    p = 0
    for i in range(numClasses):
        for j in range(i + 1, numClasses):
            if result[p] > 0:
                votes[i] += 1
            else:
                votes[j] += 1
            p += 1
    winner = -1
    bestCount = -1
    for i, count in enumerate(votes):
        if count > bestCount:
            winner = i
            bestCount = count
    return (winner, bestCount)

def labelAllTraining(labeledTraining, unlabeledTraining):
    if len(unlabeledTraining) == 0:
        return labeledTraining
    else:
        pass #finish

if __name__ == "__main__":
    cases = data.getAllSavedCases()
    training = [cases[0]]
    test = cases[1:]
    clf = makeSVM(training)
    for cas in test:
        for sentence, srlSentence in zip(cas.sentences, cas.srlSentences):
            featureDict = getFeatures(sentence, srlSentence)
            prediction = clf.predict(v.transform(featureDict))
            if prediction[0] != 0:
                print sentence
                print prediction
    #for i, sentence in enumerate(cases[0].sentences):
    #    print str(i) + ': ' + str(sentence)
