import case, data
import gensim, logging
import pickle
import numpy as np

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
    model = gensim.models.Word2Vec.load('models/word2vec/bigramModel')
    print model.most_similar(positive=['trial_court'], negative=[], topn=50)
    print model.most_similar(positive=['we_conclude'], negative=[], topn=50)
    print model.most_similar(positive=['appellant_claims'], negative=[], topn=50)

def wordVecUnigrams(cases, save=True, load=False):
    if load:
        return gensim.models.Word2Vec.load('models/word2vec/unigramModel')
    else:
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
        sentences = []
        for cas in cases:
            sentences.extend([sentence.split() for sentence in cas.tokens])
        model = models.Word2Vec(sentences, min_count=10, size=200, workers=4)
        if save:
            model.save('models/word2vec/unigramModel')
            print 'model saved'

def getRepresentation(cas, save=False, intensity=False, log=False, binarize=False, representationSize=200):
    """Caution: running with save on makes a file of size ~7MB for each case. Don't use it on the whole corpus."""
    if save:
        try:
            return pickle.load(open("cases/" + cas.googleURL + "/representation.p", "rb"))
        except:
            model = gensim.models.Word2Vec.load('models/word2vec/unigramModel')
            toWrite = np.array([])
            for sentence in cas.tokens:
                altSentence = np.zeros(len(sentence.split()))
                for i, word in enumerate(sentence.split()):
                    try:
                        altWord = np.multiply(np.add(np.divide(word, 2.0), 0.5), 255) if intensity else word
                        altSentence[i] = altWord
                    except:
                        altSentence[i] = np.zeros(representationSize)
                toWrite.append(altSentence)
            pickle.dump(toWrite, open("cases/" + cas.googleURL + "/representation.p", "wb"))
            print 'wrote to cases/' + cas.googleURL + '/representation.p'
            return toWrite
    else:
        from sklearn.preprocessing import binarize
        model = gensim.models.Word2Vec.load('models/word2vec/unigramModel')
        ret = [None]*len(cas.tokens)
        for i, sentence in enumerate(cas.tokens):
            altSentence = np.zeros((len(sentence.split()), representationSize))
            for j, word in enumerate(sentence.split()):
                try:
                    altWord = np.multiply(np.add(np.divide(model[word], 2.0), 0.5), 255) if intensity else model[word]
                    altWord = np.multiply(binarize(altWord, threshold=255.0/2.0), 255) if binarize else altWord
                    altSentence[j,:] = altWord
                except:
                    altSentence[j,:] = altSentence[j-1,:]
            ret[i] = altSentence
        return ret

if __name__ == "__main__":
    cases = data.getAllSavedCases(senna=False)
    model = wordVecUnigrams(cases)
    #print model.most_similar(positive=['therefore', 'Therefore', 'thus', 'Thus'], negative=[], topn=50)
    #model = wordVecBigrams(cases)
