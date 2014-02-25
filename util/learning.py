import re
import numpy as np
import case, linguistics, data

from sklearn.feature_extraction import DictVectorizer
v = DictVectorizer(sparse=False) #Decision_function not supported for sparse SVM

from genderator.detector import *
d = Detector()

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

def getFeatures(cas, sentence, srlSentence):
    featureDict = {}
    appellant, respondent = linguistics.getAppellantAndRespondent(cas)
    appellantNames = [appellant.split(' ')[0].lower(), 'appellant', 'plaintiff', linguistics.getGenderPronoun(d, cas, 'appellant')]
    respondentNames = [respondent.split(' ')[0].lower(), 'respondent', 'defendant', linguistics.getGenderPronoun(d, cas, 'respondent')]
    if appellant.split(' ')[-1].lower() != respondent.split(' ')[-1].lower(): #Different last names
        appellantNames.append(appellant.split(' ')[-1].lower())
        respondentNames.append(respondent.split(' ')[-1].lower())
    for clause in srlSentence:
        if 'A0' in clause:
            a0 = clause['A0'].lower()
            if a0 in appellantNames:
                featureDict['appellant'] = 1
            if a0 in respondentNames:
                featureDict['respondent'] = 1
            if 'trial court' in a0 or 'the court' in a0:
                featureDict['trial court'] = 1
            if 'we' in a0:
                featureDict['we'] = 1
    """
    for clause in srlSentence:
        if 'A0' in clause:
            featureDict[('A0', clause['A0'])] = 1
        if 'V' in clause:
            featureDict[('V', clause['V'])] = 1
        if 'A0' in clause and 'V' in clause:
            featureDict[(clause['A0'], clause['V'])] = 1
    """
    return featureDict

def makeSVM(trainingData, prob=False):
    def getXAndY():
        XDicts = []
        Y = []
        for cas in trainingData:
            for label, lineList in cas.summary.iteritems():
                for i in lineList:
                    XDicts.append(getFeatures(cas, cas.sentences[i], cas.srlSentences[i]))
                    Y.append(label)
        X = v.fit_transform(XDicts)
        return (X, Y)
    from sklearn import svm
    readLabels(trainingData) #All trainingData should be labeled
    (X, Y) = getXAndY()
    clf = svm.SVC(probability=prob) #one against one
    clf.fit(X, Y)
    return clf

def votingAlgorithm(dfResult, numClasses=4):
    votes = np.zeros(numClasses)
    p = 0
    for i in range(numClasses):
        for j in range(i + 1, numClasses):
            if dfResult[p] > 0:
                #votes[i] += 1
                votes[i] += dfResult[p]
            else:
                #votes[j] += 1
                votes[j] -= dfResult[p]
            p += 1
    winner = -1
    bestCount = -1
    for i, count in enumerate(votes):
        if count > bestCount:
            winner = i + 1
            bestCount = count
    return (winner, bestCount)

def labelAllTraining(labeledTraining, unlabeledTraining):
    if len(unlabeledTraining) == 0:
        return
    else:
        for cas in unlabeledTraining:
            predictSummarySentences(cas, labeledTraining)
            labeledTraining.append(cas)
            print cas.summary
            for person, linenos in cas.summary.iteritems():
                print str(person)
                for lineno in linenos:
                    print cas.sentences[lineno]
            print

def predictSummarySentences(cas, labeledTraining, n=3):
    print cas.name
    clf = makeSVM(labeledTraining)
    print 'Size of labeled training: ' + str(len(labeledTraining))
    alreadyUsed = []
    for sentenceCount in range(0, n):
        bestCounts = {1:-1, 2:-1, 3:-1, 4:-1}
        bestSentences = {1:-1, 2:-1, 3:-1, 4:-1}
        for lineNumber, (sentence, srlSentence) in enumerate(zip(cas.sentences, cas.srlSentences)):
            featureDict = getFeatures(cas, sentence, srlSentence)
            dfResult = clf.decision_function(v.transform(featureDict))
            dfResult = dfResult[0] #Fix (Vectorize)
            (winner, bestCount) = votingAlgorithm(dfResult)
            if bestCount > bestCounts[winner]:
                if lineNumber not in alreadyUsed:
                    bestCounts[winner] = bestCount
                    bestSentences[winner] = lineNumber
        for cls, lineNumber in bestSentences.iteritems():
            cas.summary[cls].append(lineNumber)
            alreadyUsed.append(lineNumber)
            bestCounts = {1:-1, 2:-1, 3:-1, 4:-1}
            bestSentences = {1:-1, 2:-1, 3:-1, 4:-1}


if __name__ == "__main__":
    cases = data.getAllSavedCases()
    labeledTraining = findLabels(cases)
    print 'labeled cases are: ' + str([cas.name for cas in labeledTraining])
    """
    newcas = case.Case('6850872635911328292')
    for i, sentence in enumerate(newcas.sentences):
        print str(i) + ': ' + sentence
    """
    unlabeledCases = filter(lambda x:x not in labeledTraining, cases)
    unlabeledTraining = unlabeledCases[:-1]
    test = [unlabeledCases[-1]]
    #clf = makeSVM(training)
    labelAllTraining(labeledTraining, unlabeledTraining)
    print str(len(unlabeledTraining)) + ' cases machine labeled'
    print len(labeledTraining)
    for cas in test:
        predictSummarySentences(cas, labeledTraining)
        print cas.summary
        for person, linenos in cas.summary.iteritems():
            print str(person)
            for lineno in linenos:
                print cas.sentences[lineno]
    """
    for cas in unlabeledTraining:
        print cas.name
        for i, sentence in enumerate(cas.sentences):
            print str(i) + ': ' + sentence
    """
