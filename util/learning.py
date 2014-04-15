import numpy as np
import case, linguistics, data

from sklearn.feature_extraction import DictVectorizer
#v = DictVectorizer(sparse=False) #Decision_function not supported for sparse SVM
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
        #Don't even add unimportant sentences
        """
        for i, sentence in enumerate(caseSentences):
            if i not in importantIndices:
                ret.append((i, 0))
        """
        return ret
    labeledTraining = []
    unlabeledTraining = []
    for cas in trainingData:
        folderName = cas.googleURL
        try:
            with open('cases/' + cas.googleURL + '/referenceSummary.txt', 'r') as f:
                summary = f.read() #Labeled
                lbls = processLabels(summary, cas.sentences)
                for line, label in lbls:
                    cas.summary[label].append(line)
        except IOError: #Not labeled
            pass
    return None

def findLabels(trainingData):
    labeledData = []
    for cas in trainingData:
        folderName = cas.googleURL
        try:
            with open('cases/' + cas.googleURL + '/referenceSummary.txt', 'r') as f:
                labeledData.append(cas)
        except IOError:
            pass
    return labeledData

def getFeaturesCompact(srlSentences):
    def normalizeFeature(value, mn, mx):
        return (value-mn)/(mx-mn)
    featureDicts = []
    for (srlSentence, indicators) in srlSentences:
        featureDict = {}
        #featureDict['sentenceComplexity'] = normalizeFeature(len(srlSentence), 0, 5)
        for clause in srlSentence:
        #for clause in [srlSentence[0]]:
            index = str(srlSentence.index(clause))
            if 'A0' in clause and 'V' in clause:
                a0 = clause['A0'].lower()
                if a0 in indicators[1]:
                    #featureDict['appellant', index] = 1
                    featureDict['appellant'] = normalizeFeature(1, 0, 1)
                if a0 in indicators[2]:
                    #featureDict['respondent', index] = 1
                    featureDict['respondent'] = normalizeFeature(1, 0, 1)
                if a0 in indicators[3]:
                    #featureDict['trial court', index] = 1
                    featureDict['trial court'] = normalizeFeature(1, 0, 1)
                if a0 in indicators[4]:
                    #featureDict['we', index] = 1
                    featureDict['we'] = normalizeFeature(1, 0, 1)
                v = clause['V'].lower()
                featureDict[('V', v)] = normalizeFeature(1, 0, 1)
        featureDicts.append(featureDict)
    return featureDicts

def makeSVM(labeledSrlSentences, prob=False):
    def getXAndY():
        srlSentences = []
        Y = []
        #print labeledSrlSentences
        for (casNum, label, srlSentence, cas) in labeledSrlSentences:
            #print label
            #print srlSentence
            srlSentences.append((cas.srlSentences[srlSentence], cas.indicators))
            Y.append(label)
        XDicts = getFeaturesCompact(srlSentences)
        X = v.fit_transform(XDicts)
        return (X, Y)
    from sklearn import svm
    (X, Y) = getXAndY()
    clf = svm.SVC(probability=prob) #one against one
    clf.fit(X, Y)
    return clf

def makeNeuron(labeledSrlSentences, regParam=10, pnlty='l1', tolerance=0.01):
    def getXAndY():
        srlSentences = []
        Y = []
        #print labeledSrlSentences
        for (casNum, label, srlSentence, cas) in labeledSrlSentences:
            #print label
            #print srlSentence
            srlSentences.append((cas.srlSentences[srlSentence], cas.indicators))
            Y.append(label)
        XDicts = getFeaturesCompact(srlSentences)
        X = v.fit_transform(XDicts)
        return (X, Y)
    from sklearn.linear_model import LogisticRegression
    (X, Y) = getXAndY()
    clf = LogisticRegression(C=regParam, penalty=pnlty, tol=tolerance)
    clf.fit(X, Y)
    return clf

def votingAlgorithm(dfResults, numClasses=4):
    votes = np.zeros((len(dfResults), numClasses))
    for k in range(len(dfResults)):
        dfResult = dfResults[k]
        p = 0
        for i in range(numClasses):
            for j in range(i + 1, numClasses):
                if dfResult[p] > 0:
                    #votes[k, i] += 1
                    votes[k, i] += dfResult[p]
                else:
                    #votes[k, j] += 1
                    votes[k, j] -= dfResult[p]
                p += 1
    #return (np.argmax(votes, axis=0), np.amax(votes, axis=0))
    return np.argmax(votes, axis=0)

def compressLabeledCases(cases):
    ret = []
    for i, cas in enumerate(cases):
        for person, summarySentences in cas.summary.iteritems():
            for summarySentence in summarySentences:
                ret.append((i, person, summarySentence, cas))
    return ret

def getTestingFeatures(cases):
    def normalizeFeature(value, mn, mx):
        return (value-mn)/(mx-mn)
    featureDicts = []
    caseMap = []
    for cas in cases:
        for i, srlSentence in enumerate(cas.srlSentences):
            featureDict = {}
            add = True
            for person, summarySentences in cas.summary.iteritems():
                for summarySentence in summarySentences:
                    if i == summarySentence:
                        add = False
            if add:
                featureDict['sentenceComplexity'] = normalizeFeature(len(srlSentence), 0, 5)
                for clause in srlSentence:
                    index = str(srlSentence.index(clause))
                    if 'A0' in clause and 'V' in clause:
                        a0 = clause['A0'].lower()
                        if a0 in cas.indicators[1]:
                            #featureDict['appellant', index] = 1
                            featureDict['appellant'] = normalizeFeature(1, 0, 1)
                        if a0 in cas.indicators[2]:
                            #featureDict['respondent', index] = 1
                            featureDict['respondent'] = normalizeFeature(1, 0, 1)
                        if a0 in cas.indicators[3]:
                            #featureDict['trial court', index] = 1
                            featureDict['trial court'] = normalizeFeature(1, 0, 1)
                        if a0 in cas.indicators[4]:
                            #featureDict['we', index] = 1
                            featureDict['we'] = normalizeFeature(1, 0, 1)
                        v = clause['V'].lower()
                        featureDict[('V', v)] = normalizeFeature(1, 0, 1)
                featureDicts.append(featureDict)
                caseMap.append((cas, i))
    return (featureDicts, caseMap)

def labelCases(labeledTraining, unlabeledTraining, testing, numIterations=1000, numSummarySentences=10, debug=False):
    print('Using ' + str(len(labeledTraining)) + ' labeled cases and ' + str(len(unlabeledTraining)) + 
        ' unlabeled cases to label ' + str(len(testing)) + ' test cases')
    training = labeledTraining + unlabeledTraining
    for unused in range(numIterations):
        if unused % 100 == 0:
            print 'Iteration ' + str(unused)
        neuronTraining = compressLabeledCases(training)
        clf = makeNeuron(neuronTraining)
        neuronTesting, caseMap = getTestingFeatures(unlabeledTraining)
        votes = clf.decision_function(v.transform(neuronTesting))
        for i, winner in enumerate(np.argmax(votes, axis=0)):
            winningCase, winningLine = caseMap[winner]
            winningCase.summary[i+1].append(winningLine)
    for cas in testing:
        for unused in range(numSummarySentences):
            neuronTraining = compressLabeledCases(training)
            clf = makeNeuron(neuronTraining)
            neuronTesting, caseMap = getTestingFeatures([cas])
            votes = clf.decision_function(v.transform(neuronTesting))
            for i, winner in enumerate(np.argmax(votes, axis=0)):
                winningCase, winningLine = caseMap[winner]
                winningCase.summary[i+1].append(winningLine)
        if debug:
            print str(cas.name)
            print cas.indicators
            for person, summarySentences in cas.summary.iteritems():
                print person
                for summarySentence in summarySentences:
                    print cas.sentences[summarySentence]

if __name__ == "__main__":
    cases = data.getAllSavedCases()
    labeledTraining = findLabels(cases)
    readLabels(labeledTraining)
    unlabeledCases = filter(lambda x:x not in labeledTraining, cases)
    unlabeledTraining = unlabeledCases[:-2]
    testing = [unlabeledCases[-2], unlabeledCases[-1]]
    labelCases(labeledTraining, unlabeledTraining, testing, debug=True)
