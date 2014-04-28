import case, data

def wordVecBigrams(cases):
    import gensim, logging
    from gensim import models
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
    #print model.most_similar(positive=['trial_court'], negative=[], topn=50)
    #print model.most_similar(positive=['we_conclude'], negative=[], topn=50)
    #print model.most_similar(positive=['he_claims'], negative=[], topn=50)
    #print model.most_similar(positive=['she_claims'], negative=[], topn=50)
    #print model.most_similar(positive=['we'], negative=[], topn=50)

def wordVecTest(cases):
    import gensim, logging
    from gensim import models
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    sentences = []
    for cas in cases:
        sentences.extend([sentence.split() for sentence in cas.tokens])
    model = models.Word2Vec(sentences, min_count=10, size=200, workers=4)
    print model.most_similar(positive=['therefore', 'Therefore', 'thus', 'Thus'], negative=[], topn=50)
    #print model.most_similar(positive=['moreover', 'Moreover', 'furthermore', 'Furthermore'], negative=[], topn=50)

if __name__ == "__main__":
    cases = data.getAllSavedCases(senna=False)
    wordVecTest(cases)
