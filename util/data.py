import nltk, re

def getGoogleCites(caseName):
    import urllib2, HTMLParser
    def getURL():
        url = 'http://scholar.google.com/scholar?hl=en&q=' + caseName.replace(' ', '+') + '&btnG=&as_sdt=4%2C5'
        headers = { 'User-Agent' : 'Mozilla/5.0' }
        req = urllib2.Request(url, None, headers)
        html = urllib2.urlopen(req).read()
        urlRegex = r'scholar_case\?about=([0-9]+)'
        allLinks = []
        for result in re.finditer(urlRegex, html):
            for link in result.groups():
                allLinks.append(link)
        citeRegex = r'Cited\sby\s(\d+)'
        allNumCites = []
        for result in re.finditer(citeRegex, html):
            for numCites in result.groups():
                allNumCites.append(numCites)
        return allLinks[0], allNumCites[0] #Assuming the first link is the relevant one, also assuming it was cited
    def fixCite(citation):
        """
        Only get one, full sentence out of the cite
        """
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
    urlNum, numCites = getURL()
    url = 'http://scholar.google.com/scholar_case?about=' + urlNum
    headers = { 'User-Agent' : 'Mozilla/5.0' }
    req = urllib2.Request(url, None, headers)
    html = urllib2.urlopen(req).read()
    raw = nltk.clean_html(html)  
    citeBegin = '.*?has\sbeen\scited\s+'
    citations = '(.*?)\s-\sin.*?similar\scitations?\s+'*min(9, numCites) #No more than 9 citations are displayed
    citeRegex = r'' + citeBegin + citations
    cites = []
    for result in re.finditer(citeRegex, raw):
        for cite in result.groups():
            cites.append(fixCite(cite))
    return cites

if __name__ == "__main__":
    #print getGoogleCites('In re Marriage of Shaughnessy')
    print getGoogleCites('179 Cal. App. 3d 1071')
