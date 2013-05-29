"""
grab specific cases via the search option
"""

from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.http import Request, FormRequest

class FindlawsearchSpider(CrawlSpider):
    name="findlaw_search"
    start_urls = ["http://caselaw.lp.findlaw.com/scripts/callawcs.pl"]
    login_page = 'http://login.findlaw.com/scripts/login'
    rules = [Rule(SgmlLinkExtractor(allow=start_urls[0]),
                  'search', follow=True)
             ]
    
    def start_requests(self):
        return [Request(self.login_page, callback=self.login)]
    
    def login(self, response):
        print "===TRYING TO LOGIN===="
        return FormRequest.from_response(response,
                                         formdata={'user': 'srudamaster@yahoo.com', 
                                                   'password': 'p0pp0p'},
                                         callback=self.check_login_response)

    def check_login_response(self, response):
        if 'Welcome Victor Huang!' in response.body:
            print "=====LOGIN SUCCESSFUL======"
            return self.make_requests_from_url(self.start_urls[0])
        else:
            print "====LOGIN FAILED===="
            
    def search(self, response):
        print "====ENTERING SEARCH===="
        return FormRequest.from_response(response,
                                         formnumber=1, 
                                         formdata={'vol': '81',
                                                   'reporter': 'Cal.App.2d',
                                                   'page': '1'},
                                         callback=self.grab_case)
    
    def grab_case(self, response):
        if 'Bank of America' in response.body:
            print "=====HOORAY!!!!!!====="
        else:
            print "====NOOOOOOOOOOO===="
