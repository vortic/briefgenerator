import nltk, re, urllib2, os
import case

import time
import random

def getHeader():
    header = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language':'en-US;q=0.8,en;q=0.6',
        'Cookie': 'GSP=ID=e87e4317dc6fd955:LM=1402387863:S=GHB8IuRHFO-L3wEs; PREF=ID=e87e4317dc6fd955:LD=en:CR=2:TM=1402387863:LM=1402387879:S=r57DE5ULElEt91Zy',
        'Host':'scholar.google.com',
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36',
        'X-Chrome-Variations':'CNO1yQEIl7bJAQiptskBCMS2yQEIqYXKAQi3hcoB'
    }
    return header

def getGoogleURL(cas):
    if re.match('^[0-9]+$', cas.name):
        return cas.name
    nameAndYear = cas.name.split(', ')
    url = 'http://scholar.google.com/scholar?hl=en&q=' + nameAndYear[0].replace(' ', '+') + '&btnG=&as_sdt=4%2C5'
    if len(nameAndYear) > 1:
        url = url + '&as_ylo=' + nameAndYear[1]  + '&as_yhi=' + nameAndYear[1]
    #print 'Getting URL for ' +caseName
    header = getHeader()
    req = urllib2.Request(url, None, header)
    time.sleep(random.randint(2, 10))
    html = urllib2.urlopen(req).read()
    #print req.get_header('Cookie')
    urlRegex = r'scholar_case\?case=([0-9]+)'
    allLinks = []
    for result in re.finditer(urlRegex, html):
        for link in result.groups():
            allLinks.append(link)
    return allLinks[0] #Assuming the first link is the relevant one, also assuming it was cited

def getGoogleCites(cas):
    import HTMLParser
    def fixCite(citation):
        """
        Only get one, full sentence out of the cite
        """
        citation = unicode(citation, "utf-8")
        citation = HTMLParser.HTMLParser().unescape(citation)
        sentenceRegex = r'([A-Z].*?\.)'
        finalCitation = ''
        for result in re.finditer(sentenceRegex, citation):
            for sentence in result.groups():
                if len(sentence) > len(finalCitation): #There should only be one "real" sentence
                    finalCitation = sentence
        if finalCitation == '' and citation[-1] != '.':
            return citation + '.'
        elif finalCitation == '':
            return citation
        else:
            return finalCitation
    def fixTitle(title):
        ret = title
        if 'and' in title:
            split = re.split('and', title)
            ret = split[0]
        return ret.strip()
    url = 'http://scholar.google.com/scholar_case?about=' + cas.googleURL
    header = getHeader()
    req = urllib2.Request(url, None, header)
    time.sleep(random.randint(2, 10))
    html = urllib2.urlopen(req).read()
    raw = nltk.clean_html(html)
    #print raw
    citeBegin = '.*?has\sbeen\scited\s+'
    #citations = '(.*?)\s-\sin.*?similar\scitations?\s+'*min(6, numCites) #No more than 9 citations are displayed
    citations = '(.*?)\s-\sin\s(.*?)\s\s'*8 #No more than 9 citations are displayed (sometimes 8)
    citeRegex = r'' + citeBegin + citations
    cites = []
    titles = []
    title = False
    for result in re.finditer(citeRegex, raw):
        for cite in result.groups():
            if title:
                titles.append(fixTitle(cite))
                title = False
            else:
                cites.append(fixCite(cite))
                title = True
    #return cites, titles
    return titles

def getGoogleCase(cas):
    def removeHeading(raw):
        """
        headingRemover = re.compile('.*?OPINION(.*)Save\strees\s-\sread', re.DOTALL)
        if re.match(headingRemover, raw):
            for result in re.finditer(headingRemover, raw):
                for caseText in result.groups():
                    return caseText
        #Failure: just keep Google's stuff in there
        """
        return raw
    try:
        with open('cases/' + cas.googleURL + '/string.txt', 'r') as f:
            return f.read()
    except IOError:
        url = 'http://scholar.google.com/scholar_case?case=' + cas.googleURL
        header = getHeader()
        req = urllib2.Request(url, None, header)
        time.sleep(random.randint(2, 10))
        html = urllib2.urlopen(req).read()
        raw = nltk.clean_html(html)
        ret = removeHeading(raw)
        try:
            try:
                os.makedirs('cases/' + cas.googleURL + '/')
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise
            with open('cases/' + cas.googleURL + '/string.txt', 'w') as f:
                f.write(ret)
                print 'Wrote to cases/' + cas.googleURL + '/string.txt'
        except IOError:
            print 'Could not cache case'
        return ret

def tokenize(string):
    return trainer.tokenize(string)

def getNGoogleCites(cas, n): #Approximately n
    def getTenLinks(start=0):
        url = 'http://scholar.google.com/scholar?cites=' + cas.googleURL + \
              '&as_sdt=2005&sciodt=4,5&hl=en&start=' + str(start)
        header = getHeader()
        req = urllib2.Request(url, None, header)
        time.sleep(random.randint(2, 10))
        html = urllib2.urlopen(req).read()
        urlRegex = r'scholar_case\?case=([0-9]+)'
        allLinks = []
        for result in re.finditer(urlRegex, html):
            for link in result.groups():
                allLinks.append(case.Case(link))
        return allLinks[1:]
    allCites = []
    start = 0
    getMore = True
    while getMore and len(allCites) < n:
        newLinks = getTenLinks(start)
        if newLinks == []:
            getMore = False
        allCites = allCites + newLinks
        start += 10
    return allCites

def getAboutCases(cas):
    url = 'http://scholar.google.com/scholar_case?about=' + cas.googleURL
    header = getHeader()
    req = urllib2.Request(url, None, header)
    time.sleep(random.randint(2, 10))
    html = urllib2.urlopen(req).read()
    urlRegex = r'scholar_case\?case=([0-9]+)'
    allLinks = []
    for result in re.finditer(urlRegex, html):
        for link in result.groups():
            allLinks.append(link)
    return allLinks

def getAllSavedCases(makeString=True, senna=True):
    ret = []
    for caseName in os.listdir('cases'):
        if caseName.isdigit():
            ret.append(case.Case(caseName, makeString=makeString, senna=senna))
    return ret

if __name__ == "__main__":
    #cites, titles = getGoogleCites('224 Cal. App. 3d 885')
    cases = getAllSavedCases()
    for cas in cases:
        getNGoogleCites(cas, 50)
    """for cite, title in zip(cites, titles):
        print
        if re.match('.*\d.*', title):
            getGoogleCase(title)
        else:
            print 'failed on ' + title"""
    #print getGoogleCites('179 Cal. App. 3d 1071')
    #getGoogleCase('224 Cal. App. 3d 885')
