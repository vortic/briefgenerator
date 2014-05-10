import case, data, learning
import random
import collections
import numpy as np
import gensim

def coherentSummary(argumentSentences, allSentences, allSrlSentences):
    G = generateCoherenceGraph(argumentSentences, allSentences, allSrlSentences)

def generateCoherenceGraph(argumentSentences, allSentences, allSrlSentences):
    #Find all chains such that m-coherence is at least tau
    def findShortChains(m=4, k=1):
        def importantWords(chain, numWords=5, srl=False):
            if srl:
                wordCounter = collections.Counter()
                verbsToConsider = set()
                A0sToConsider = set()
                ret = []
                for srlSentence in chain:
                    for clause in srlSentence:
                        if 'A0' in clause:
                            A0sToConsider.add(clause['A0'])
                        if 'V' in clause:
                            verbsToConsider.add(clause['V'])
                for srlSentence in allSrlSentences:
                    for clause in srlSentence:
                        if 'A0' in clause and clause['A0'] in A0sToConsider:
                            wordCounter[clause['A0']] += 1
                        if 'V' in clause and clause['V'] in verbsToConsider:
                            wordCounter[clause['V']] += 1
                for word, count in wordCounter.most_common(numWords):
                    ret.append(word)
                return ret
            else:
                from gensim import models
                model = gensim.models.Word2Vec.load('models/word2vec/unigramModel')
                for sentence in chain:
                    for word in sentence.split():
                        print word
                        try:
                            print model[word]
                        except:
                            pass
        for i in range(k):
            possibleEndpoints = argumentSentences[:]
            d1 = random.choice(possibleEndpoints)
            possibleEndpoints.remove(d1)
            dm = random.choice(possibleEndpoints)
            print [d1, dm]
            impWords = importantWords([d1, dm])
            model = [0]*len(impWords)
            print d1
            print dm
            print impWords
            for i, word in enumerate(impWords):
                polyfitInput = [0]*2
                for clause in d1:
                    if 'A0' in clause and clause['A0'] == word:
                        polyfitInput[0] += 1
                    if 'V' in clause and clause['V'] == word:
                        polyfitInput[0] += 1
                for clause in dm:
                    if 'A0' in clause and clause['A0'] == word:
                        polyfitInput[1] += 1
                    if 'V' in clause and clause['V'] == word:
                        polyfitInput[1] += 1
                print polyfitInput
                model[i] = np.polyfit([1, m], polyfitInput, 1)
            print model
    return findShortChains()

if __name__ == "__main__":
    cases = data.getAllSavedCases()
    labeledTraining = learning.findLabels(cases)
    learning.readLabels(labeledTraining)
    unlabeledCases = filter(lambda x:x not in labeledTraining, cases)
    unlabeledTraining = unlabeledCases[:-1]
    testing = [unlabeledCases[-1]]
    learning.labelCases(labeledTraining, unlabeledTraining, testing, numIterations=20)
    for cas in testing:
        print 'case ' + str(cas.name)
        d = {}
        for person, summarySentences in cas.summary.iteritems():
            personSentences = []
            for sentence in summarySentences:
                personSentences.append(cas.sentences[sentence])
            d[person] = personSentences
        for person, summarySentences in d.iteritems():
            print coherentSummary(summarySentences, cas.sentences, cas.srlSentences)
