import case, data
import gensim, logging
from gensim import models
import pickle
import numpy as np

#model = models.Word2Vec.load('models/word2vec/unigramModel')

def wordVecBigrams(cases, save=True):
    """
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    sentences = []
    for cas in cases:
        #sentences.extend([sentence.split() for sentence in cas.tokens])
        for l in cas.tokens:
            bigramSentence = [b for b in zip(l.split(" ")[:-1], l.split(" ")[1:])]
            sentenceList = []
            for w1, w2 in bigramSentence:
                sentenceList.append(w1 + '_' + w2)
            sentences.append(sentenceList)
    model = models.Word2Vec(sentences, min_count=10, size=200, workers=4)
    if save:
        model.save('models/word2vec/bigramModel')
        print 'model saved'
    """
    model = models.Word2Vec.load('models/word2vec/bigramModel')
    print model.most_similar(positive=['trial_court'], negative=[], topn=50)
    print model.most_similar(positive=['we_conclude'], negative=[], topn=50)
    print model.most_similar(positive=['appellant_claims'], negative=[], topn=50)

def wordVecUnigrams(cases, save=True, load=False):
    if load:
        return models.Word2Vec.load('models/word2vec/unigramModel')
    else:
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
        sentences = []
        for cas in cases:
            sentences.extend([sentence.split() for sentence in cas.tokens])
        model = models.Word2Vec(sentences, min_count=10, size=200, workers=4)
        if save:
            model.save('models/word2vec/unigramModel')
            print 'model saved'

def wordVecSrl(cases, save=True, load=False):
    if load:
        return models.Word2Vec.load('models/word2vec/srlModel')
    else:
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
        sentences = []
        for cas in cases:
            for srlSentence in cas.srlSentences:
                newSentence = []
                for clause in srlSentence:
                    for role, text in clause.iteritems():
                        newSentence.append(str((role, text)))
                print newSentence
                sentences.append(newSentence)
        model = models.Word2Vec(sentences, min_count=10, size=200, workers=4)
        #print model.most_similar(positive=["('V', 'conclude')"], negative=[], topn=50)
        if save:
            model.save('models/word2vec/srlModel')
            print 'model saved'

def wordVecSrlBigrams(cases, save=True, load=False):
    if load:
        return models.Word2Vec.load('models/word2vec/srlBigramModel')
    else:
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
        sentences = []
        for cas in cases:
            for srlSentence in cas.srlSentences:
                newSentence = []
                for clause in srlSentence:
                    for role, text in clause.iteritems():
                        newSentence.append(str((role, text)))
                print newSentence
                bigramSentence = [b for b in zip(newSentence[:-1], newSentence[1:])]
                print bigramSentence
                sentenceList = []
                for w1, w2 in bigramSentence:
                    sentenceList.append(w1 + '_' + w2)
                sentences.append(sentenceList)
        model = models.Word2Vec(sentences, min_count=10, size=200, workers=4)
        #print model.most_similar(positive=["('V', 'conclude')"], negative=[], topn=50)
        if save:
            model.save('models/word2vec/srlBigramModel')
            print 'model saved'

def getRepresentation(cas, intensity=False, log=False, bnrz=False, representationSize=200):
    from sklearn.preprocessing import binarize
    ret = [None]*len(cas.tokens)
    for i, sentence in enumerate(cas.tokens):
        altSentence = np.zeros((len(sentence.split()), representationSize))
        for j, word in enumerate(sentence.split()):
            try:
                altWord = np.multiply(np.add(np.divide(model[word], 2.0), 0.5), 255) if intensity else model[word]
                altWord = np.multiply(binarize(altWord, threshold=255.0/2.0), 255) if bnrz and intensity else altWord
                altWord = binarize(altWord) if bnrz and not intensity else altWord
                altSentence[j,:] = altWord
            except:
                altSentence[j,:] = altSentence[j-1,:] if j != 0 else np.zeros(representationSize)
        ret[i] = altSentence
    return ret

def getSrlRepresentation(cas, intensity=False, log=False, bnrz=False, representationSize=200):
    from sklearn.preprocessing import binarize
    model = models.Word2Vec.load('models/word2vec/srlModel')
    ret = [None]*len(cas.sentences)
    for i, sentence in enumerate(cas.srlSentences):
        numRows = sum([len(clause) for clause in sentence])
        altSentence = np.zeros((numRows, representationSize))
        currentRow = 0
        for clause in sentence:
            for j, (role, text) in enumerate(clause.iteritems()):
                word = str((role, text))
                try:
                    altWord = np.multiply(np.add(np.divide(model[word], 2.0), 0.5), 255) if intensity else model[word]
                    altWord = np.multiply(binarize(altWord, threshold=255.0/2.0), 255) if bnrz and intensity else altWord
                    altWord = binarize(altWord) if bnrz and not intensity else altWord
                    altSentence[currentRow,:] = altWord
                except:
                    altSentence[currentRow,:] = altSentence[j-1,:] if j != 0 else np.zeros(representationSize)
                currentRow += 1
        ret[i] = altSentence
    return ret

def topicModelWordVec():
    model = gensim.models.ldamodel.LdaModel.load('models/lda/srlTopicModel')
    topics = model.show_topics(topics=15, topn=1000, formatted=False)
    newModel = {}
    def normalize(v):
        factor = 1.0/sum(v)
        return np.multiply(v, factor)
    for i, topic in enumerate(topics):
        for probability, unit in topic:
            try:
                newModel[unit][i] = probability
            except:
                newModel[unit] = [0]*len(topics)
                newModel[unit][i] = probability
    for unit, wordVec in newModel.iteritems():
        newModel[unit] = normalize(wordVec)
    return newModel

def srlTopicModel(cases, log=True, save=False):
    if log:
        import logging
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    from gensim import corpora, models
    texts = []
    for cas in cases:
        for srlSentence in cas.srlSentences:
            sentence = []
            for clause in srlSentence:
                for role, text in clause.iteritems():
                    sentence.append(str((role, text)))
            texts.append(sentence)
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    lda = models.ldamodel.LdaModel(corpus, id2word=dictionary, num_topics=15, alpha='auto', eval_every=5)
    if save:
        lda.save('models/lda/srlTopicModel')

if __name__ == "__main__":
    #cases = data.getAllSavedCases(senna=True)
    #wordVecSrlBigrams(cases)
    cas = case.Case('6850872635911328292')
    #representation = wordVecSrl(cases)
    """
    for cas in cases:
        print getRepresentation(cas, log=True)
    """
