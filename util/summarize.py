import gensim

import numpy as np

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import binarize

v = DictVectorizer(sparse=True)

class Sentence:
    def __init__(self, docset, article, num, wdcount, text):
        self.docset = docset
        self.article = article
        self.num = num
        self.wdcount = wdcount
        self.text = text

def loadDucDocs():
    import os
    from lxml import etree
    docsets = []
    for (_, dirnames, _) in os.walk('DUC/docs/'):
        for docsetName in dirnames:
            docset = []
            for (_, _, articles) in os.walk('DUC/docs/' + docsetName + '/'):
                for articleName in articles:
                    article = []
                    with open('DUC/docs/' + docsetName + '/' + articleName, 'r') as xml:
                        xmlstring = ''.join(xml.readlines())
                        parser = etree.XMLParser(recover=True)
                        root = etree.fromstring(xmlstring, parser=parser)
                        for text in root:
                            if text.tag == 'TEXT':
                                for child in text:
                                    if child.tag == 's':
                                        num = child.attrib['num']
                                        wdcount = child.attrib['wdcount']
                                        txt = child.text
                                        sentence = Sentence(docsetName, articleName, num, wdcount, txt)
                                        article.append(sentence)
                    docset.append((articleName, article))
            docsets.append((docsetName[:-1], docset))
    return docsets

def loadModelSummaries():
    import os
    def loadSummary(ducFile, docsetName):
        from lxml import etree
        summary = []
        with open(ducFile, 'r') as xml:
            xmlstring = ''.join(xml.readlines())
            parser = etree.XMLParser(recover=True)
            root = root = etree.fromstring(xmlstring, parser=parser)
            assert(docsetName == root.attrib['DOCSET'])
            for child in root:
                articleName = child.attrib['docid']
                num = child.attrib['num'] 
                wdcount = child.attrib['wdcount']
                txt = child.text
                sentence = Sentence(docsetName, articleName, num, wdcount, txt)
                summary.append(sentence)
            return summary
    summaries = {}
    for (dirpath, dirnames, filenames) in os.walk('DUC/summaries/'):
        for dirname in dirnames:
            docsetName = dirname[:-2]
            try:
                summary = loadSummary('DUC/summaries/' + dirname + '/400e', docsetName)
            except IOError:
                #print 'No 400e summary for ' + dirname
                continue
            try:
                summaries[docsetName].append(summary)
            except KeyError:
                summaries[docsetName] = [summary]
    return summaries

def getFeaturesUnigrams(sentence):
    def normalizeFeatures(values, mn, mx):
        return np.divide(np.subtract(values, mn), float(mx-mn))
    featureDict = {}
    for i, word in enumerate(sentence.text.split()):
        try:
            representation = model[word]
            representation = binarize(representation)
            representation = normalizeFeatures(representation, 0, 1)
            for j, vectorEntry in enumerate(representation):
                featureDict[str(i*len(representation)+j)] = vectorEntry
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

def getFeaturesBatch(sentences, feature):
    featureDicts = []
    for sentence in sentences:
        featureDicts.append(getFeaturesGeneric(sentence, None, feature))
    return featureDicts

def makeNeuron(docsets, feature, regParam=10, pnlty='l1', tolerance=0.01):
    def getXAndY():
        XDicts = []
        Y = []
        for docsetName, docset in docsets:
            used = set()
            for summary in summaries[docsetName]:
                for summarySentence in summary:
                    used.add(summarySentence.num)
            for articleName, article in docset:
                for sentence in article:
                    XDicts.append(getFeaturesGeneric(sentence, None, feature))
                    if sentence.num in used:
                        Y.append(1)
                    else:
                        Y.append(0)
        X = v.fit_transform(XDicts)
        return (X, Y)
    (X, Y) = getXAndY()
    clf = LogisticRegression(C=regParam, penalty=pnlty, tol=tolerance)
    clf.fit(X, Y)
    return clf

def summarizeDocsets(training, testing, features, debug=False):
    systemSummaries = {}
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
        print clf
        for docsetName, docset in testing:
            print 'Testing on ' + docsetName
            flatSentences = [sentence for (articleName, article) in docset for sentence in article]
            neuronTesting = getFeaturesBatch(flatSentences, feature)
            votes = clf.decision_function(v.transform(neuronTesting))
            winners = np.argsort(votes)[-len(votes):][::-1]
            i = 0
            usedCount = 0
            summary = []
            while usedCount < 400:
                summary.append(flatSentences[winners[i]].text)
                i += 1
                usedCount += int(flatSentences[winners[i]].wdcount)
            systemSummaries[(docsetName, feature)] = summary
            return systemSummaries

def summarizeN(features, n=1):
    docsets = loadDucDocs()
    global summaries
    summaries = loadModelSummaries()
    training = docsets[:-n]
    testing = filter(lambda x:x not in training, docsets)
    print 'Using ' + str(len(training)) + ' docsets for training and ' + str(len(testing)) + ' for testing'
    systemSummaries = summarizeDocsets(training, testing, features)
    return systemSummaries

if __name__ == "__main__":
    docsets = loadDucDocs()
    #docsets = docsets[:5]
    global summaries
    summaries = loadModelSummaries()
    training = docsets[:-1]
    testing = filter(lambda x:x not in training, docsets)
    print 'Using ' + str(len(training)) + ' docsets for training and ' + str(len(testing)) + ' for testing'
    features = ['unigrams']
    systemSummaries = summarizeDocsets(training, testing, features)
    for (docsetName, feature), summary in systemSummaries.iteritems():
        print docsetName
        print feature
        print summary
