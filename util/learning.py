import numpy as np
import case, linguistics, data

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
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

def getFeatures(indicators, srlSentence):
    def normalizeFeature(value, mn, mx):
        return (value-mn)/(mx-mn)
    featureDict = {}
    for clause in srlSentence:
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
        #if 'A1' in clause:
        #    featureDict[clause['A1'].lower()] = normalizeFeature(1, 0, 1)
    return featureDict

def getFeaturesBatch(cases):
    caseMap = []
    featureDicts = []
    for cas in cases:
        for i, srlSentence in enumerate(cas.srlSentences):
            add = True
            for person, summarySentences in cas.summary.iteritems():
                for summarySentence in summarySentences:
                    if i == summarySentence:
                        add = False
            if add:
                featureDicts.append(getFeatures(cas.indicators, srlSentence))
                caseMap.append((cas, i))
    return featureDicts, caseMap

def makeNeuron(cases, regParam=10, pnlty='l1', tolerance=0.01):
    def getXAndY():
        XDicts = []
        Y = []
        for cas in cases:
            for label, summarySentences in cas.summary.iteritems():
                for summarySentence in summarySentences:
                    XDicts.append(getFeatures(cas.indicators, cas.srlSentences[summarySentence]))
                    Y.append(label)
        X = v.fit_transform(XDicts)
        return (X, Y)
    (X, Y) = getXAndY()
    clf = LogisticRegression(C=regParam, penalty=pnlty, tol=tolerance)
    clf.fit(X, Y)
    return clf

def labelCases(labeledTraining, unlabeledTraining, testing, numIterations=500, numSummarySentences=10, debug=False):
    print('Using ' + str(len(labeledTraining)) + ' labeled cases and ' + str(len(unlabeledTraining)) + 
        ' unlabeled cases to label ' + str(len(testing)) + ' test cases')
    training = labeledTraining + unlabeledTraining
    for unused in range(numIterations):
        if unused % 100 == 0:
            print 'Iteration ' + str(unused)
        clf = makeNeuron(training)
        neuronTesting, caseMap = getFeaturesBatch(unlabeledTraining)
        votes = clf.decision_function(v.transform(neuronTesting))
        for i, winner in enumerate(np.argmax(votes, axis=0)):
            winningCase, winningLine = caseMap[winner]
            winningCase.summary[i+1].append(winningLine)
    for cas in testing:
        for unused in range(numSummarySentences):
            clf = makeNeuron(training)
            neuronTesting, caseMap = getFeaturesBatch([cas])
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

def documentTopicModel(cases, log=True):
    if log:
        import logging
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    from gensim import corpora, models
    stoplist = set('for a of the and to in'.split())
    texts = [[word for word in cas.string.lower().split() if word not in stoplist]
        for cas in cases]
    all_tokens = sum(texts, [])
    tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
    texts = [[word for word in text if word not in tokens_once]
        for text in texts]
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = tfidf[corpus]
    #lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=15)
    #corpus_lsi = lsi[corpus_tfidf]
    model = models.ldamodel.LdaModel(corpus_tfidf, id2word=dictionary, num_topics=15)
    corpus_lda = model[corpus_tfidf]

def paragraphTopicModel(cas, log=True):
    if log:
        import logging
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    from gensim import corpora, models
    stoplist = set('for a of the and to in'.split())
    texts = [[word for word in paragraph.split() if word not in stoplist]
        for paragraph in cas.string.lower().split('\r\n')]
    all_tokens = sum(texts, [])
    tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
    texts = [[word for word in text if word not in tokens_once]
        for text in texts]
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = tfidf[corpus]
    #lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=15)
    #corpus_lsi = lsi[corpus_tfidf]
    model = models.ldamodel.LdaModel(corpus_tfidf, id2word=dictionary, num_topics=15)
    corpus_lda = model[corpus_tfidf]

if __name__ == "__main__":
    cases = data.getAllSavedCases(senna=False)
    wordVecTest(cases)
    #documentTopicModel(cases)
    #for cas in cases:
    #    paragraphTopicModel(cas)
    """
    labeledTraining = findLabels(cases)
    readLabels(labeledTraining)
    unlabeledCases = filter(lambda x:x not in labeledTraining, cases)
    unlabeledTraining = unlabeledCases[:-2]
    testing = [unlabeledCases[-2], unlabeledCases[-1]]
    labelCases(labeledTraining, unlabeledTraining, testing, debug=True)
    """
