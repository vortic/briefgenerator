import numpy as np
import case, linguistics, data, wordVector
import itertools

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import binarize

#v = DictVectorizer(sparse=False) #Decision_function not supported for sparse SVM
v = DictVectorizer(sparse=True)
import gensim
#model = gensim.models.Word2Vec.load('models/word2vec/unigramModel')
#model = gensim.models.Word2Vec.load('models/word2vec/srlModel')
#model = wordVector.topicModelWordVec()
#model = gensim.models.Word2Vec.load('models/word2vec/srlBigramModel')
num2Person = {1:'Appellant', 2:'Respondent', 3:'Trial Court', 4:'We'}

def readLabels(trainingData, typ):
    def convertWordToLabel(word):
        conversion = {'Appellant':1, 'Respondent':2, 'Trial':3, 'We':4} #Save 0 for unimportant
        return conversion[word]
    def processLabels(summary, caseSentences):
        ret = []
        importantIndices = []
        for lineAndLabel in summary.split('\n'):
            line, englishLabel = lineAndLabel.split()
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
    for cas in trainingData:
        folderName = cas.googleURL
        if typ == 'tokens':
            try:
                with open('cases/' + cas.googleURL + '/tokenSummary.txt', 'r') as f:
                    summary = f.read() #Labeled
                    lbls = processLabels(summary, cas.tokens)
                    for line, label in lbls:
                        cas.tokenSummary[label].append(line)
            except IOError: #Not labeled
                pass
        elif typ == 'srl':
            try:
                with open('cases/' + cas.googleURL + '/srlSummary.txt', 'r') as f:
                    summary = f.read() #Labeled
                    lbls = processLabels(summary, cas.tokens)
                    for line, label in lbls:
                        cas.srlSummary[label].append(line)
            except IOError: #Not labeled
                pass
        else:
            pass
    return None

def findLabels(trainingData):
    labeledData = []
    for cas in trainingData:
        folderName = cas.googleURL
        try:
            with open('cases/' + cas.googleURL + '/srlSummary.txt', 'r') as f:
                labeledData.append(cas)
        except IOError:
            pass
    return labeledData

def getFeaturesUnigrams(sentence):
    def normalizeFeatures(values, mn, mx):
        return np.divide(np.subtract(values, mn), float(mx-mn))
    featureDict = {}
    for i, word in enumerate(sentence.split()):
        try:
            representation = model[word]
            representation = binarize(representation)
            representation = normalizeFeatures(representation, 0, 1)
            for j, vectorEntry in enumerate(representation):
                featureDict[str(i*len(representation)+j)] = vectorEntry
        except KeyError:
            continue
    return featureDict

def getFeaturesBigrams(sentence):
    def normalizeFeatures(values, mn, mx):
        return np.divide(np.subtract(values, mn), float(mx-mn))
    featureDict = {}
    sentence = sentence.split()
    bigramSentence = [b for b in zip(sentence[:-1], sentence[1:])]
    for i, (w1, w2) in enumerate(bigramSentence):
        try:
            representation = model[w1 + '_' + w2]
            representation = binarize(representation)
            representation = normalizeFeatures(representation, 0, 1)
            for j, vectorEntry in enumerate(representation):
                featureDict[str(i*len(representation)+j)] = vectorEntry
        except KeyError:
            continue
    return featureDict

def getFeaturesSrl(srlSentence):
    def normalizeFeatures(values, mn, mx):
        return np.divide(np.subtract(values, mn), float(mx-mn))
    featureDict = {}
    for level, clause in enumerate(srlSentence):
        for (role, text) in clause.iteritems():
            try:
                representation = model[str((role, text))]
                #representation = binarize(representation)
                representation = normalizeFeatures(representation, 0, 1)
                for j, vectorEntry in enumerate(representation):
                    featureDict[(level, role, j)] = vectorEntry
            except KeyError:
                continue
    return featureDict

def getFeaturesSrlBigrams(srlSentence):
    def normalizeFeatures(values, mn, mx):
        return np.divide(np.subtract(values, mn), float(mx-mn))
    featureDict = {}
    newSentence = []
    for level, clause in enumerate(srlSentence):
        for (role, text) in clause.iteritems():
            newSentence.append((str((role, text)), level))
    bigramSentence = [b for b in zip(newSentence[:-1], newSentence[1:])]
    for (w1, l1), (w2, l2) in bigramSentence:
        r1, word1 = eval(w1)
        r2, word2 = eval(w2)
        if l1 == l2:
            try:
                representation = model[w1 + '_' + w2]
                representation = binarize(representation)
                representation = normalizeFeatures(representation, 0, 1)
                for j, vectorEntry in enumerate(representation):
                    featureDict[(l1, r1, r2, j)] = vectorEntry
            except KeyError:
                continue
    return featureDict

def getFeaturesGeneric(sentence, srlSentence, feature):
    featureDict = {}
    if feature == 'srl' or feature == 'srlTopicModel' or feature == 'srlLSI':
        return getFeaturesSrl(srlSentence)
    elif feature == 'unigrams':
        return getFeaturesUnigrams(sentence)
    elif feature == 'bigrams':
        return getFeaturesBigrams(sentence)
    elif feature == 'srlBigrams':
        return getFeaturesSrlBigrams(srlSentence)
    else:
        print 'Error: feature ' + feature + ' not implemented'

def getFeaturesBatch(cas, feature):
    featureDicts = []
    for i, (sentence, srlSentence) in enumerate(zip(cas.sentences, cas.srlSentences)):
        if i%100 == 0:
            print 'sentence ' + str(i)
        featureDicts.append(getFeaturesGeneric(sentence, srlSentence, feature))
    return featureDicts

def makeNeuron(cases, feature, regParam=10, pnlty='l1', tolerance=0.01):
    def getXAndY():
        XDicts = []
        Y = []
        for cas in cases:
            for label, summarySentences in cas.srlSummary.iteritems():
                for summarySentence in summarySentences:
                    XDicts.append(getFeaturesGeneric(cas.sentences[summarySentence], cas.srlSentences[summarySentence], feature))
                    Y.append(label)
        X = v.fit_transform(XDicts)
        return (X, Y)
    (X, Y) = getXAndY()
    clf = LogisticRegression(C=regParam, penalty=pnlty, tol=tolerance)
    clf.fit(X, Y)
    return clf

def f1Score(predictedIndices, desiredIndices):
    relevantCount = 0.0
    for index in predictedIndices:
        if index in desiredIndices:
            relevantCount += 1
    precision = relevantCount/len(predictedIndices)
    recall = relevantCount/len(desiredIndices)
    print 'precision: ' + str(precision)
    print 'recall: ' + str(recall)
    f1Score = 2.0*(precision * recall)/(precision + recall)
    print 'f1 score ' + str(f1Score)
    return f1Score

def labelCases(training, testing, features, numSummarySentences=10, debug=False):
    print('Using ' + str(len(training)) + ' labeled cases to label ' + str(len(testing)) + ' test cases')
    for feature in features:
        global model
        if feature == 'unigrams':
            model = gensim.models.Word2Vec.load('models/word2vec/unigramModel')
        if feature == 'bigrams':
            model = gensim.models.Word2Vec.load('models/word2vec/bigramModel')
        if feature == 'srl':
            model = gensim.models.Word2Vec.load('models/word2vec/srlModel')
        if feature == 'srlBigrams':
            model = gensim.models.Word2Vec.load('models/word2vec/srlBigramModel')
        if feature == 'srlTopicModel':
            model = wordVector.topicModelWordVec()
        if feature == 'srlLSI':
            model = wordVector.LSIWordVec()
        print 'Using features: ' + feature
        clf = makeNeuron(training, feature)
        for cas in testing:
            print cas.name
            neuronTesting = getFeaturesBatch(cas, feature)
            votes = clf.decision_function(v.transform(neuronTesting))
            scores = [[], [], [], []]
            for sentence in votes:
                for person, score in enumerate(sentence):
                    scores[person].append(score)
            for person, lst in enumerate(scores):
                if debug:
                    print num2Person[person+1]
                winners = np.argsort(lst)[-10:][::-1]
                winners.sort()
                for winner in winners:
                    #cas.srlSummary[person+1].append(winner)
                    if debug:
                        print cas.sentences[winner]
                print
            """
            for unused in range(numSummarySentences):
                for i, winner in enumerate(np.argmax(votes, axis=0)):
                    cas.srlSummary[i+1].append(winner)
            if debug:
                print str(cas.name)
                for person, summarySentences in cas.srlSummary.iteritems():
                    print person
                    for summarySentence in summarySentences:
                        print cas.sentences[summarySentence]
            """

if __name__ == "__main__":
    cases = data.getAllSavedCases(senna=True)
    print 'dataset in memory'
    #srlTopicModel(cases, save=True)
    #documentTopicModel(cases)
    #for cas in cases:
    #    paragraphTopicModel(cas)
    labeledTraining = findLabels(cases)
    #readLabels(labeledTraining)
    unlabeledCases = filter(lambda x:x not in labeledTraining, cases)
    #features = ['srl', 'srlTopicModel', 'srlLSI']
    #features = ['srlLSI']
    features = ['unigrams']
    #features = ['bigrams']
    labelCases(labeledTraining, unlabeledCases, features, debug=True)
