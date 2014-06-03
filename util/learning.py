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
model = gensim.models.Word2Vec.load('models/word2vec/srlModel')

def readLabels(trainingData, typ):
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

"""
def getFeatures(splitSentence):
    def normalizeFeatures(values, mn, mx):
        return np.divide(np.subtract(values, mn), float(mx-mn))
    featureDict = {}
    for i, word in enumerate(splitSentence):
        try:
            representation = model[word]
            representation = binarize(representation)
            representation = normalizeFeatures(representation, 0, 1)
            for j, vectorEntry in enumerate(representation):
                featureDict[str(i*len(representation)+j)] = vectorEntry
        except KeyError:
            continue
    return featureDict
"""

def getFeatures(srlSentence):
    def normalizeFeatures(values, mn, mx):
        return np.divide(np.subtract(values, mn), float(mx-mn))
    featureDict = {}
    i = 0
    for clause in srlSentence:
        for (role, text) in clause.iteritems():
            try:
                representation = model[str((role, text))]
                representation = binarize(representation)
                representation = normalizeFeatures(representation, 0, 1)
                for j, vectorEntry in enumerate(representation):
                    featureDict[str(i*len(representation)+j)] = vectorEntry
                i += 1
            except KeyError:
                i += 1
                continue
    return featureDict

def getFeaturesBatch(cases):
    caseMap = []
    featureDicts = []
    for cas in cases:
        for i, sentence in enumerate(cas.srlSentences):
            add = True
            if i%100 == 0:
                print 'features ' + str(i)
            for person, summarySentences in cas.srlSummary.iteritems():
                for summarySentence in summarySentences:
                    if i == summarySentence:
                        add = False
            if add:
                featureDicts.append(getFeatures(sentence))
                caseMap.append((cas, i))
    return featureDicts, caseMap

def makeNeuron(cases, regParam=10, pnlty='l1', tolerance=0.01):
    def getXAndY():
        XDicts = []
        Y = []
        for cas in cases:
            for label, summarySentences in cas.srlSummary.iteritems():
                for summarySentence in summarySentences:
                    XDicts.append(getFeatures(cas.srlSentences[summarySentence]))
                    Y.append(label)
        X = v.fit_transform(XDicts)
        return (X, Y)
    (X, Y) = getXAndY()
    clf = LogisticRegression(C=regParam, penalty=pnlty, tol=tolerance)
    clf.fit(X, Y)
    return clf

def labelCases(labeledTraining, unlabeledTraining, testing, numIterations=1, minibatchSize = 20, numSummarySentences=10, debug=False):
    print('Using ' + str(len(labeledTraining)) + ' labeled cases and ' + str(len(unlabeledTraining)) + 
        ' unlabeled cases to label ' + str(len(testing)) + ' test cases')
    for index in range(numIterations):
        if index % 100 == 0:
            print 'Iteration ' + str(index)
        a, b = index%len(cases), (index+minibatchSize)%len(unlabeledTraining)
        training = labeledTraining
        if b > a:
            training += unlabeledTraining[a:b]
        else:
            training += unlabeledTraining[0:minibatchSize]
        print 'training set of size ' + str(len(training))
        clf = makeNeuron(training)
        print 'made classifier'
        neuronTesting, caseMap = getFeaturesBatch(training)
        print 'got features'
        votes = clf.decision_function(v.transform(neuronTesting))
        print 'got decision function'
        for _ in range(minibatchSize):
            for person in range(len(votes[0])):
                scores = [votes[index][person] for index in range(len(votes))]
                scores.sort()
                bestScores = scores[-minibatchSize:]
                winners = [np.where(votes==score)[0][0] for score in bestScores]
                for winner in winners:
                    winningCase, winningLine = caseMap[winner]
                    winningCase.srlSummary[person+1].append(winningLine)
                    if debug:
                        print 'person:' + str(person+1) + ' winner: ' + str(winner)
                        print winningCase.sentences[winningLine]
    training = labeledTraining + unlabeledTraining
    for cas in testing:
        for unused in range(numSummarySentences):
            clf = makeNeuron(training)
            neuronTesting, caseMap = getFeaturesBatch([cas])
            votes = clf.decision_function(v.transform(neuronTesting))
            for i, winner in enumerate(np.argmax(votes, axis=0)):
                winningCase, winningLine = caseMap[winner]
                winningCase.srlSummary[i+1].append(winningLine)
        if debug:
            print str(cas.name)
            for person, summarySentences in cas.srlSummary.iteritems():
                print person
                for summarySentence in summarySentences:
                    print cas.sentences[summarySentence]

def documentTopicModel(cases, log=True):
    if log:
        import logging
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    from gensim import corpora, models
    stoplist = set('for a of the and to in cal. n.e.2d ( .) n.w.2d cal.rptr.2d n.j.'.split())
    texts = [[word for word in cas.string.lower().split() if word not in stoplist]
        for cas in cases]
    """
    all_tokens = sum(texts, [])
    tokens_n_times = set(word for word in set(all_tokens) if all_tokens.count(word) <= 10)
    texts = [[word for word in text if word not in tokens_n_times]
        for text in texts]
    """
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = tfidf[corpus]
    #lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=15)
    #corpus_lsi = lsi[corpus_tfidf]
    lda = models.ldamodel.LdaModel(corpus_tfidf, id2word=dictionary, num_topics=1, alpha='auto', eval_every=5)
    corpus_lda = lda[corpus_tfidf]

def paragraphTopicModel(cas, log=True):
    if log:
        import logging
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    from gensim import corpora, models
    stoplist = set('for a of the and to in cal. n.e.2d ( .) n.w.2d cal.rptr.2d n.j.'.split())
    texts = [[word for word in paragraph.split() if word not in stoplist]
        for paragraph in cas.string.lower().split('\r\n')]
    all_tokens = sum(texts, [])
    tokens_n_times = set(word for word in set(all_tokens) if all_tokens.count(word) == 10)
    texts = [[word for word in text if word not in tokens_n_times]
        for text in texts]
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = tfidf[corpus]
    #lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=15)
    #corpus_lsi = lsi[corpus_tfidf]
    lda = models.ldamodel.LdaModel(corpus_tfidf, id2word=dictionary, num_topics=15, alpha='auto', eval_every=5)
    corpus_lda = lda[corpus_tfidf]

if __name__ == "__main__":
    cases = data.getAllSavedCases(senna=True)
    print 'dataset in memory'
    #documentTopicModel(cases)
    #for cas in cases:
    #    paragraphTopicModel(cas)
    labeledTraining = findLabels(cases)
    #readLabels(labeledTraining)
    unlabeledCases = filter(lambda x:x not in labeledTraining, cases)
    unlabeledTraining = unlabeledCases[:-2]
    testing = [unlabeledCases[-2], unlabeledCases[-1]]
    labelCases(labeledTraining, unlabeledTraining, testing, debug=True)
