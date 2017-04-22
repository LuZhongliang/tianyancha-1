# -*- coding:utf-8 -*-

import scrapy
import codecs
import time
import re
import json
from tianyancha.items import TianyanchaItem
from scrapy.spiders import CrawlSpider
from tianyancha.middlewares import safe_append, safe_append_date, safe_appends
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

names = globals()

class TianYanCha_Spider(CrawlSpider):
    name = 'tyc_spider'
    start_urls = ['http://www.tianyancha.com                 ']

    def parse(self, response):
        with codecs.open('../company_test.txt', 'r', encoding='utf-8') as f:
            for line in f.readlines():
                url = str(line.replace('\r', '').replace('\n', '').replace('=', ''))
                requests = scrapy.Request(url, callback=self.parse_basic_info)
                yield requests

    def parse_basic_info(self, response):
        item = TianyanchaItem()
        company_id = response.url[34:]
        company_name = response.selector.xpath('//div[@class="company_header_width"]/div[1]/span/text()').extract_first(default=u'未公开')
        legal_representative = response.selector.xpath('//a[@ng-if="company.legalPersonName"]/text()').extract_first(default=u'未公开')
        registered_capital = response.selector.xpath('//div[@class="baseInfo_model2017"]/table/tbody/tr/td[2]/div/text()').extract_first(default=u'未公开')
        registered_time = response.selector.xpath('//div[@class="baseInfo_model2017"]/table/tbody/tr/td[3]/div/text()').extract_first(default=u'未公开')
        condition = response.selector.xpath('//div[@class="baseInfo_model2017"]/table/tbody/tr/td[4]/div/text()').extract_first(default=u'未公开')
        temp_items = response.selector.xpath('//div[@class="row b-c-white company-content base2017"]/table/tbody/tr/td/div/span/text() | //div[@class="row b-c-white company-content base2017"]/table/tbody/tr/td/div/span/span/text()').extract()
        registered_number = temp_items[0]
        organization_number = temp_items[1]
        credit_number = temp_items[2]
        enterprise_type = temp_items[3]
        industry = temp_items[4]
        operating_start = temp_items[5][:10]
        operating_end = temp_items[5][-10:]
        approved_date = temp_items[6]
        registration_authority = temp_items[7]
        registered_address = temp_items[8]
        business_scope = temp_items[9]
        telephone = response.selector.xpath(u'//span[text()="电话："]/following-sibling::span[1]/text()').extract_first(default=u'暂')
        email = response.selector.xpath(u'//span[text()="邮箱："]/following-sibling::span[1]/text()').extract_first(default=u'暂')
        address = response.selector.xpath(u'//span[text()="地址："]/following-sibling::span[1]/text()').extract_first(default=u'暂')
        website = response.selector.xpath(u'//span[text()="网址："]/following-sibling::a[1]/text()').extract_first(default=u'暂')
        score = response.selector.xpath('//td[@class="td-score position-rel"]/img/@ng-alt | //img[@class="td-score-img"]/@ng-alt').extract()[0][-2:]
        logo_location = response.selector.xpath(u'//img[@alt="公司图标"]/@src').extract_first(default=u'暂')
        former_name = response.selector.xpath('//div[@ng-if="company.historyNames"]/div/text()').extract_first(default=u'')

        flag = response.selector.xpath('//div[@class="navigation new-border new-c3"]/div/div/div/div/@class').extract()
        for i in range(0, len(flag)):
            if flag[i][-7:] == u'disable':
                flag[i] = 0
            else:
                flag[i] = 1

        item["flag"] = flag
        item["company_name"] = company_name
        item["legal_representative"] = legal_representative
        item["registered_capital"] = registered_capital
        item["registered_time"] = registered_time
        item["condition"] = condition
        item["registered_number"] = registered_number
        item["organization_number"] = organization_number
        item["credit_number"] = credit_number
        item["enterprise_type"] = enterprise_type
        item["industry"] = industry
        item["operating_start"] = operating_start
        item["operating_end"] = operating_end
        item["approved_date"] = approved_date
        item["registration_authority"] = registration_authority
        item["registered_address"] = registered_address
        item["business_scope"] = business_scope
        item["telephone"] = telephone
        item["email"] = email
        item["website"] = website
        item["logo_location"] = logo_location
        item["address"] = address
        item["score"] = score
        item["company_id"] = company_id
        item["former_name"] = former_name

        next_url = 'http://www.tianyancha.com/expanse/staff.json?id=' + str(item["company_id"]) + '&ps=20&pn=1'
        request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_main_person)
        yield request

    def parse_main_person(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        person_id = []
        person_name = []
        position = []

        if flag[2] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["result"]:
                person_id.append(dic["id"])
                person_name.append(dic["name"])
                position.append(dic["typeJoin"][0])

        item["person_id"] = person_id
        item["person_name"] = person_name
        item["position"] = position

        item["shareholder_id"] = []
        item["shareholder_name"] = []
        item["investment_proportion"] = []
        item["subscribed_contribution"] = []
        item["subscribed_contribution_time"] = []
        item["really_contribution"] = []
        item["page"] = 1

        next_url = 'http://www.tianyancha.com/expanse/holder.json?id=' + str(item["company_id"]) + '&ps=20&pn=1'
        request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_shareholder_info)
        yield request

    def parse_shareholder_info(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        shareholder_id = item["shareholder_id"]
        shareholder_name = item["shareholder_name"]
        investment_proportion = item["investment_proportion"]
        subscribed_contribution = item["subscribed_contribution"]
        subscribed_contribution_time = item["subscribed_contribution_time"]
        really_contribution = item["really_contribution"]

        data = json.loads(response.body)
        try:
            temp = data["data"]["result"]
        except:
            flag[3] = 0

        if flag[3] is 1:
            for dic in data["data"]["result"]:
                try:
                    shareholder_id.append(dic["id"] or u'')
                except:
                    shareholder_id.append(u'')

                try:
                    shareholder_name.append(dic["name"] or u'')
                except:
                    shareholder_name.append(u'')

                try:
                    investment_proportion.append(dic["capital"][0]["percent"][:-1] or u'')
                except:
                    investment_proportion.append(u'')

                try:
                    subscribed_contribution.append(dic["capital"][0]["amomon"] or u'')
                except:
                    subscribed_contribution.append(u'')

                try:
                    subscribed_contribution_time.append(dic["capital"][0]["time"] or u'')
                except:
                    subscribed_contribution_time.append(u'')

                try:
                    really_contribution.append(dic["capitalActl"][0]["amomon"] or u'')
                except:
                    really_contribution.append(u'')

        item["shareholder_id"] = shareholder_id
        item["shareholder_name"] = shareholder_name
        item["investment_proportion"] = investment_proportion
        item["subscribed_contribution"] = subscribed_contribution
        item["subscribed_contribution_time"] = subscribed_contribution_time
        item["really_contribution"] = really_contribution

        if len(response.body) > 1000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/holder.json?id=' + str(item["company_id"]) + '&ps=20&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_shareholder_info)
            yield request
        else:
            item["invested_company_id"] = []
            item["invested_company_name"] = []
            item["invested_representative"] = []
            item["registered_cap"] = []
            item["investment_amount"] = []
            item["investment_prop"] = []
            item["registered_date"] = []
            item["condit"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/inverst.json?id=' + str(item["company_id"]) + '&ps=20&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_investment)
            yield request

    def parse_investment(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        invested_company_id = item["invested_company_id"]
        invested_company_name = item["invested_company_name"]
        invested_representative = item["invested_representative"]
        registered_cap = item["registered_cap"]
        investment_amount = item["investment_amount"]
        investment_prop = item["investment_prop"]
        registered_date = item["registered_date"]
        condit = item["condit"]

        data = json.loads(response.body)
        try:
            temp = data["data"]["result"]
        except:
            flag[4] = 0

        if flag[4] is 1:
            for dic in data["data"]["result"]:
                safe_append(invested_company_id, dic, 'id')
                safe_append(invested_company_name, dic, 'name')
                safe_append(invested_representative, dic, 'legalPersonName')
                safe_append(registered_cap, dic, 'regCapital')
                safe_append(investment_amount, dic, 'amount')
                safe_append(investment_prop, dic, 'percent')

                safe_append_date(registered_date, dic, 'estiblishTime')
                safe_append(condit, dic, 'regStatus')

        item["invested_company_id"] = invested_company_id
        item["invested_company_name"] = invested_company_name
        item["invested_representative"] = invested_representative
        item["registered_cap"] = registered_cap
        item["investment_amount"] = investment_amount
        item["investment_prop"] = investment_prop
        item["registered_date"] = registered_date
        item["condit"] = condit

        if len(response.body) > 3000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/inverst.json?id=' + str(item["company_id"]) + '&ps=20&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_investment)
            yield request
        else:
            item["change_time"] = []
            item["change_item"] = []
            item["before_change"] = []
            item["after_change"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/changeinfo.json?id=' + str(item["company_id"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_change_record)
            yield request

    def parse_change_record(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        change_time = item["change_time"]
        change_item = item["change_item"]
        before_change = item["before_change"]
        after_change = item["after_change"]

        data = json.loads(response.body)
        try:
            temp = data["data"]["result"]
        except:
            flag[5] = 0

        if flag[5] is 1:
            for dic in data["data"]["result"]:
                try:
                    change_time.append(dic["changeTime"] or u'')
                except:
                    change_time.append(u'')
                try:
                    change_item.append(dic["changeItem"] or u'')
                except:
                    change_item.append(u'')
                try:
                    before_change.append(dic["contentBefore"] or u'')
                except:
                    before_change.append(u'')

                try:
                    after_change.append(dic["contentAfter"] or u'')
                except:
                    after_change.append(u'')

        item["change_time"] = change_time
        item["change_item"] = change_item
        item["before_change"] = before_change
        item["after_change"] = after_change

        if len(response.body) > 800:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/changeinfo.json?id=' + str(item["company_id"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_change_record)
            yield request
        else:
            next_url = 'http://www.tianyancha.com/expanse/annu.json?id=' + str(item["company_id"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_annual_reports)
            yield request

    def parse_annual_reports(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        annual_year = []
        annual_url = []

        data = json.loads(response.body)
        try:
            temp = data["data"]
        except:
            flag[6] = 0

        if flag[6] is 1:
            for dic in data["data"]:
                url = 'http://www.tianyancha.com/annualreport/newReport.json?id=' + str(item["company_id"]) + '&year=' + str(dic["reportYear"])
                annual_url.append(url)
                try:
                    annual_year.append(dic["reportYear"] or u'')
                except:
                    annual_year.append(u'')

        item["annual_year"] = annual_year
        item["annual_url"] = annual_url

        item["branch_id"] = []
        item["branch_name"] = []
        item["branch_legalrep"] = []
        item["branch_cond"] = []
        item["branch_regtime"] = []
        item["page"] = 1

        if flag[6] is 1:

            item["total_assets"] = []
            item["total_sales"] = []
            item["mainbusiness_income"] = []
            item["total_tax"] = []
            item["total_ownersequity"] = []
            item["total_profit"] = []
            item["retained_profits"] = []
            item["total_liabilities"] = []

            item["amend_date"] = []
            item["amend_event"] = []
            item["before_amend"] = []
            item["after_amend"] = []

            item["page"] = 1
            next_url = item["annual_url"][0]
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_annual_detail)
            yield request
        else:
            item["page"] = 1
            next_url = 'http://www.tianyancha.com/expanse/branch.json?id=' + str(item["company_id"]) + '&ps=10&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_branch)
            yield request

    def parse_annual_detail(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        asset_status_name_list = ['totalAssets', 'totalEquity', 'totalSales', 'totalProfit', 'primeBusProfit',
                                  'retainedProfit', 'totalTax', 'totalLiability']
        asset_status_item_list = ['total_assets', 'total_sales', 'mainbusiness_income', 'total_tax', 'total_ownersequity',
                                  'total_profit', 'retained_profits', 'total_liabilities']

        alter_event_name_list = ['changeItem', 'contentBefore', 'contentAfter', 'changeTime']
        alter_event_item_list = ['amend_date', 'amend_event', 'before_amend', 'after_amend']

        for i in range(len(asset_status_name_list)):
            names[asset_status_name_list[i]] = item[asset_status_item_list[i]]
        for i in range(len(alter_event_name_list)):
            names[alter_event_name_list[i]] = item[alter_event_item_list[i]]

        data = json.loads(response.body)

        for item_name in asset_status_name_list:
            safe_appends(names[item_name], data["data"], "baseInfo", item_name)

        for item_name in alter_event_name_list:
            safe_appends(names[item_name], data["data"], "changeRecordList", item_name)

        for i in range(len(asset_status_name_list)):
            item[asset_status_item_list[i]] = names[asset_status_name_list[i]]
        for i in range(len(alter_event_name_list)):
            item[alter_event_item_list[i]] = names[alter_event_name_list[i]]

        if response.url == item["annual_url"][-1]:

            next_url = 'http://www.tianyancha.com/expanse/branch.json?id=' + str(item["company_id"]) + '&ps=10&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_branch)
            yield request
        else:
            next_url = item["annual_url"][item["page"]]
            item["page"] += 1
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_annual_detail)
            yield request

    def parse_branch(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        branch_id = item["branch_id"]
        branch_name = item["branch_name"]
        branch_legalrep = item["branch_legalrep"]
        branch_cond = item["branch_cond"]
        branch_regtime = item["branch_regtime"]

        data = json.loads(response.body)
        try:
            temp = data["data"]["result"]
        except:
            flag[7] = 0

        if flag[7] is 1:
            for dic in data["data"]["result"]:
                try:
                    branch_id.append(dic["id"] or u'')
                except:
                    branch_id.append(u'')

                try:
                    branch_name.append(dic["name"] or u'')
                except:
                    branch_name.append(u'')
                branch_legalrep.append(u'暂')
                branch_cond.append(u'暂')
                branch_regtime.append(u'暂')

        item["branch_id"] = branch_id
        item["branch_name"] = branch_name
        item["branch_legalrep"] = branch_legalrep
        item["branch_cond"] = branch_cond
        item["branch_regtime"] = branch_regtime

        if len(response.body) > 500:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/branch.json?id=' + str(item["company_id"]) + '&ps=10&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_branch)
            yield request
        else:
            item["finance_date"] = []
            item["finance_round"] = []
            item["valuation"] = []
            item["finance_amount"] = []
            item["finance_proportion"] = []
            item["investor"] = []
            item["news_title"] = []
            item["news_url"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/findHistoryRongzi.json?name=' + str(item["company_name"]) + '&ps=10&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_finance_history)
            yield request

    def parse_finance_history(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        finance_date = item["finance_date"]
        finance_round = item["finance_round"]
        valuation = item["valuation"]
        finance_amount = item["finance_amount"]
        finance_proportion = item["finance_proportion"]
        investor = item["investor"]
        news_title = item["news_title"]
        news_url = item["news_url"]

        data = json.loads(response.body)
        try:
            temp = data["data"]["page"]["rows"]
        except:
            flag[8] = 0

        if flag[8] is 1:
            for dic in data["data"]["page"]["rows"]:
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["date"])[:10])))
                    finance_date.append(str(date))
                except:
                    finance_date.append(u'')
                try:
                    finance_round.append(dic["round"] or u'')
                except:
                    finance_round.append(u'')

                try:
                    valuation.append(dic["value"] or u'')
                except:
                    valuation.append(u'')

                try:
                    finance_amount.append(dic["money"] or u'')
                except:
                    finance_amount.append(u'')

                try:
                    finance_proportion.append(dic["share"] or u'')
                except:
                    finance_proportion.append(u'')

                try:
                    investor.append(("，".join(re.findall(r'[\{|\,](.*?)\:', dic["rongziMap"]))) or u'')
                except:
                    investor.append(u'')

                try:
                    news_title.append(dic["newsTitle"] or u'')
                except:
                    news_title.append(u'')

                try:
                    news_url.append(dic["newsUrl"] or u'')
                except:
                    news_url.append(u'')

        if len(response.body) > 6000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/findHistoryRongzi.json?name=' + str(item["company_name"]) + '&ps=10&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_finance_history)
            yield request

        else:
            item["member_name"] = []
            item["member_pos"] = []
            item["member_intro"] = []
            item["member_icon"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/findTeamMember.json?name=' + str(item["company_name"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_core_team)
            yield request

    def parse_core_team(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        member_name = item["member_name"]
        member_pos = item["member_pos"]
        member_intro = item["member_intro"]
        member_icon = item["member_icon"]

        data = json.loads(response.body)
        try:
            temp = data["data"]["page"]["rows"]
        except:
            flag[9] = 0

        if flag[9] is 1:
            for dic in data["data"]["page"]["rows"]:
                try:
                    member_name.append(dic["name"] or u'')
                except:
                    member_name.append(u'')

                try:
                    member_pos.append(dic["title"] or u'')
                except:
                    member_pos.append(u'')

                try:
                    member_intro.append(dic["desc"] or u'')
                except:
                    member_intro.append(u'')

                try:
                    member_icon.append(dic["icon"] or u'')
                except:
                    member_icon.append(u'')

        item["member_name"] = member_name
        item["member_pos"] = member_pos
        item["member_intro"] = member_intro
        item["member_icon"] = member_icon

        if len(response.body) > 3000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/findTeamMember.json?name=' + str(item["company_name"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_core_team)
            yield request
        else:
            item["business_name"] = []
            item["business_type"] = []
            item["business_intro"] = []
            item["business_logo"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/findProduct.json?name=' + str(item["company_name"]) + '&ps=15&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_enterprise_business)
            yield request

    def parse_enterprise_business(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        product_name = item["business_name"]
        product_type = item["business_type"]
        product_short = item["business_intro"]
        product_logo = item["business_logo"]

        data = json.loads(response.body)
        try:
            temp = data["data"]["page"]["rows"]
        except:
            flag[10] = 0

        if flag[10] is 1:
            for dic in data["data"]["page"]["rows"]:
                try:
                    product_name.append(dic["product"] or u'')
                except:
                    product_name.append(u'')

                try:
                    product_type.append(dic["hangye"] or u'')
                except:
                    product_type.append(u'')

                try:
                    product_short.append(dic["yewu"] or u'')
                except:
                    product_short.append(u'')

                try:
                    product_logo.append(dic["logo"] or u'')
                except:
                    product_logo.append(u'')

        item["business_name"] = product_name
        item["business_type"] = product_type
        item["business_intro"] = product_short
        item["business_logo"] = product_logo

        if len(response.body) > 7000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/findProduct.json?name=' + str(item["company_name"]) + '&ps=15&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_enterprise_business)
            yield request
        else:
            item["invest_time"] = []
            item["invest_round"] = []
            item["invest_amount"] = []
            item["invest_company"] = []
            item["invest_product"] = []
            item["invest_pro_icon"] = []
            item["invest_area"] = []
            item["invest_industry"] = []
            item["invest_business"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/findTzanli.json?name=' + str(item["company_name"]) + '&ps=10&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_investment_event)
            yield request

    def parse_investment_event(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        invest_time = item["invest_time"]
        invest_round = item["invest_round"]
        invest_amount = item["invest_amount"]
        invest_company = item["invest_company"]
        invest_product = item["invest_product"]
        invest_pro_icon = item["invest_pro_icon"]
        invest_area = item["invest_area"]
        invest_industry = item["invest_industry"]
        invest_business = item["invest_business"]

        if flag[11] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["page"]["rows"]:
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["tzdate"])[:10])))
                    invest_time.append(str(date))
                except:
                    invest_time.append(u'')
                try:
                    invest_round.append(dic["lunci"] or u'')
                except:
                    invest_round.append(u'')
                try:
                    invest_amount.append(dic["money"] or u'')
                except:
                    invest_amount.append(u'')
                try:
                    invest_company.append(("，".join(re.findall(r'[\{|\,](.*?)\:', dic["rongzi_map"])) or u''))
                except:
                    invest_company.append(u'')

                try:
                    invest_pro_icon.append(dic["icon"] or u'')
                except:
                    invest_pro_icon.append(u'')
                try:
                    invest_area.append(dic["location"] or u'')
                except:
                    invest_area.append(u'')
                try:
                    invest_product.append(dic["product"] or u'')
                except:
                    invest_product.append(u'')

                try:
                    invest_industry.append(dic["hangye1"] or u'')
                except:
                    invest_industry.append(u'')

                try:
                    invest_business.append(dic["yewu"] or u'')
                except:
                    invest_business.append(u'')

        item["invest_time"] = invest_time
        item["invest_round"] = invest_round
        item["invest_amount"] = invest_amount
        item["invest_company"] = invest_company
        item["invest_product"] = invest_product
        item["invest_pro_icon"] = invest_pro_icon
        item["invest_area"] = invest_area
        item["invest_industry"] = invest_industry
        item["invest_business"] = invest_business

        if len(response.body) > 3000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/findTzanli.json?name=' + str(item["company_name"]) + '&ps=10&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_investment_event)
            yield request
        else:
            item["product_name"] = []
            item["product_logo"] = []
            item["product_area"] = []
            item["product_round"] = []
            item["product_industry"] = []
            item["product_business"] = []
            item["setup_date"] = []
            item["product_valuation"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/findJingpin.json?name=' + str(item["company_name"]) + '&ps=10&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_competing_product)
            yield request

    def parse_competing_product(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        product_name = item["product_name"]
        product_logo = item["product_logo"]
        product_area = item["product_area"]
        product_round = item["product_round"]
        product_industry = item["product_industry"]
        product_business = item["product_business"]
        setup_date = item["setup_date"]
        product_valuation = item["product_valuation"]

        if flag[12] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["page"]["rows"]:
                try:
                    product_name.append(dic["jingpinProduct"] or u'')
                except:
                    product_name.append(u'')
                try:
                    product_logo.append(dic["icon"] or u'')
                except:
                    product_logo.append(u'')
                try:
                    product_area.append(dic["location"] or u'')
                except:
                    product_area.append(u'')
                try:
                    product_round.append(dic["round"] or u'')
                except:
                    product_round.append(u'')
                try:
                    product_industry.append(dic["hangye"] or u'')
                except:
                    product_industry.append(u'')
                try:
                    product_business.append(dic["yewu"] or u'')
                except:
                    product_business.append(u'')
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["setupDate"])[:10])))
                    setup_date.append(date or u'')
                except:
                    setup_date.append(u'')
                try:
                    product_valuation.append(dic["value"] or u'')
                except:
                    product_valuation.append(u'')

        item["product_name"] = product_name
        item["product_logo"] = product_logo
        item["product_area"] = product_area
        item["product_round"] = product_round
        item["product_industry"] = product_industry
        item["product_business"] = product_business
        item["setup_date"] = setup_date
        item["product_valuation"] = product_valuation

        if len(response.body) > 3000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/findJingpin.json?name=' + str(item["company_name"]) + '&ps=10&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_competing_product)
            yield request
        else:
            item["page"] = 1

            item["judgement_name"] = []
            item["lawsuit_date"] = []
            item["judgement_id"] = []
            item["case_type"] = []

            next_url = 'http://www.tianyancha.com/v2/getlawsuit/' + str(item["company_name"]) + '.json?ps=10&page=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_law_suit)
            yield request

    def parse_law_suit(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        judgement_name = item["judgement_name"]
        lawsuit_date = item["lawsuit_date"]
        judgement_id = item["judgement_id"]
        case_type = item["case_type"]

        if flag[13] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["items"]:
                safe_append(judgement_name, dic, 'title')
                safe_append_date(lawsuit_date, dic, 'submittime')
                safe_append(judgement_id, dic, 'uuid')
                safe_append(case_type, dic, 'casetype')

        item["judgement_name"] = judgement_name
        item["lawsuit_date"] = lawsuit_date
        item["judgement_id"] = judgement_id
        item["case_type"] = case_type

        if len(response.body) > 3000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/v2/getlawsuit/' + str(item["company_name"]) + '.json?ps=10&page=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_law_suit)
            yield request
        else:
            if len(item["judgement_id"]) > 0:
                item["relative_comp"] = []
                item["judgement_title"] = []
                item["case_num"] = []
                item["judgement_content"] = []

                item["page"] = 1
                next_url = 'http://www.tianyancha.com/lawsuit/detail/' + item["judgement_id"][0] + '.json'
                request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag},
                                         callback=self.parse_lawsuit_detail)
                yield request
            else:
                next_url = 'http://www.tianyancha.com/v2/court/' + str(item["company_name"]) + '.json?'
                request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag},
                                         callback=self.parse_court_announcement)
                yield request

    def parse_lawsuit_detail(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        relative_comp = item["relative_comp"]
        judgement_title = item["judgement_title"]
        case_num = item["case_num"]
        judgement_content = item["judgement_content"]

        data = json.loads(response.body)

        dic = data["data"]
        relative_comp.append(list(set(re.findall(r'http://www.tianyancha.com/company/(\d*)', response.body))))
        safe_append(judgement_title, dic, 'title')
        safe_append(case_num, dic, 'caseno')
        safe_append(judgement_content, dic, 'plaintext')

        item["relative_comp"] = relative_comp
        item["judgement_title"] = judgement_title
        item["case_num"] = case_num
        item["judgement_content"] = judgement_content

        item["page"] += 1

        if item["page"] > len(item["judgement_id"]):
            next_url = 'http://www.tianyancha.com/v2/court/' + str(item["company_name"]) + '.json?'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag},
                                     callback=self.parse_court_announcement)
            yield request
        else:
            next_url = 'http://www.tianyancha.com/lawsuit/detail/' + item["judgement_id"][(item["page"] - 1)] + '.json'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag},
                                     callback=self.parse_lawsuit_detail)
            yield request

    def parse_court_announcement(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        announce_time = []
        appeal = []
        respondent = []
        announce_type = []
        court = []
        announce_content = []

        if flag[14] is 1:
            data = json.loads(response.body)
            for dic in data["courtAnnouncements"]:
                try:
                    announce_time.append(dic["publishdate"] or u'')
                except:
                    announce_time.append(u'')
                try:
                    appeal.append(dic["party1"] or u'')
                except:
                    appeal.append(u'')
                try:
                    respondent.append(dic["party2"] or u'')
                except:
                    respondent.append(u'')
                try:
                    announce_type.append(dic["bltntypename"] or u'')
                except:
                    announce_type.append(u'')

                try:
                    court.append(dic["courtcode"] or u'')
                except:
                    court.append(u'')

                try:
                    announce_content.append(dic["content"] or u'')
                except:
                    announce_content.append(u'')

        item["announce_time"] = announce_time
        item["appeal"] = appeal
        item["respondent"] = respondent
        item["announce_type"] = announce_type
        item["court"] = court
        item["announce_content"] = announce_content

        next_url = 'http://www.tianyancha.com/v2/dishonest/' + str(item["company_name"]) + '.json'
        request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_the_dishonest)
        yield request

    def parse_the_dishonest(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        dis_company = []
        dic_legalrepre = []
        dis_code = []
        execute_number = []
        case_number = []
        execute_unite = []
        legal_obligation = []
        performance = []
        execute_court = []
        province = []
        filing_time = []
        pub_time = []

        if flag[15] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["items"]:
                try:
                    dis_company.append(dic["iname"] or u'')
                except:
                    dis_company.append(u'')

                try:
                    dic_legalrepre.append(dic["businessentity"] or u'')
                except:
                    dic_legalrepre.append(u'')

                try:
                    dis_code.append(dic["cardnum"] or u'')
                except:
                    dis_code.append(u'')
                try:
                    execute_number.append(dic["casecode"] or u'')
                except:
                    execute_number.append(u'')

                try:
                    case_number.append(dic["gistid"] or u'')
                except:
                    case_number.append(u'')

                try:
                    execute_unite.append(dic["gistunit"] or u'')
                except:
                    execute_unite.append(u'')
                try:
                    legal_obligation.append(dic["duty"] or u'')
                except:
                    legal_obligation.append(u'')

                try:
                    performance.append(dic["performance"] or u'')
                except:
                    performance.append(u'')

                try:
                    execute_court.append(dic["courtname"] or u'')
                except:
                    execute_court.append(u'')
                try:
                    province.append(dic["areaname"] or u'')
                except:
                    province.append(u'')
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["regdate"])[:10])))
                    filing_time.append(date)
                except:
                    filing_time.append(u'')
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["publishdate"])[:10])))
                    pub_time.append(date)
                except:
                    pub_time.append(u'')

        item["dis_company"] = dis_company
        item["dic_legalrepre"] = dic_legalrepre
        item["dis_code"] = dis_code
        item["execute_number"] = execute_number
        item["case_number"] = case_number
        item["execute_unite"] = execute_unite
        item["legal_obligation"] = legal_obligation
        item["performance"] = performance
        item["execute_court"] = execute_court
        item["province"] = province
        item["filing_time"] = filing_time
        item["pub_time"] = pub_time

        item["filing_date"] = []
        item["executed_target"] = []
        item["case_code"] = []
        item["executed_court"] = []

        next_url = 'http://www.tianyancha.com/expanse/zhixing.json?id=' + str(item["company_id"]) + '&ps=5&pn=1'
        request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_the_executed)
        yield request

    def parse_the_executed(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        filing_date = item["filing_date"]
        executed_target = item["executed_target"]
        case_code = item["case_code"]
        executed_court = item["executed_court"]

        if flag[16] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["items"]:
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["caseCreateTime"])[:10])))
                    filing_date.append(date)
                except:
                    filing_date.append(u'')
                try:
                    executed_target.append(dic["execMoney"] or u'')
                except:
                    executed_target.append(u'')

                try:
                    case_code.append(dic["caseCode"] or u'')
                except:
                    case_code.append(u'')

                try:
                    executed_court.append(dic["execCourtName"] or u'')
                except:
                    executed_court.append(u'')

        item["filing_date"] = filing_date
        item["executed_target"] = executed_target
        item["case_code"] = case_code
        item["executed_court"] = executed_court

        if len(response.body) > 700:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/zhixing.json?id=' + str(item["company_id"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_the_executed)
            yield request
        else:
            item["page"] = 1

            item["include_date"] = []
            item["include_reason"] = []
            item["include_authority"] = []
            item["remove_date"] = []
            item["remove_reason"] = []
            item["remove_authority"] = []

            next_url = 'http://www.tianyancha.com/expanse/abnormal.json?id=' + str(item["company_id"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_abnormal_management)
            yield request

    def parse_abnormal_management(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]


        include_date = item["include_date"]
        include_reason = item["include_reason"]
        include_authority = item["include_authority"]
        remove_date = item["remove_date"]
        remove_reason = item["remove_reason"]
        remove_authority = item["remove_authority"]

        if flag[17] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["result"]:
                safe_append(remove_date, dic, 'removeDate')
                safe_append(remove_reason, dic, 'removeReason')
                safe_append(remove_authority, dic, 'removeDepartment')
                try:
                    include_date.append(dic["putDate"] or u'')
                except:
                    include_date.append(u'')

                try:
                    include_reason.append(dic["putReason"] or u'')
                except:
                    include_reason.append(u'')

                try:
                    include_authority.append(dic["putDepartment"] or u'')
                except:
                    include_authority.append(u'')

        item["include_date"] = include_date
        item["include_reason"] = include_reason
        item["include_authority"] = include_authority

        if len(response.body) > 900:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/abnormal.json?id=' + str(item["company_id"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_abnormal_management)
            yield request
        else:
            item["pub_code"] = []
            item["pub_type"] = []
            item["pub_content"] = []
            item["pub_date"] = []
            item["pub_authority"] = []
            item["pub_people"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/punishment.json?name=' + str(item["company_name"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_adminis_pubnish)
            yield request

    def parse_adminis_pubnish(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        pub_code = item["pub_code"]
        pub_type = item["pub_type"]
        pub_content = item["pub_content"]
        pub_date = item["pub_date"]
        pub_authority = item["pub_authority"]
        pub_people = item["pub_people"]

        if flag[18] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["items"]:
                try:
                    pub_code.append(dic["punishNumber"] or u'')
                except:
                    pub_code.append(u'')

                try:
                    pub_type.append(dic["type"] or u'')
                except:
                    pub_type.append(u'')
                try:
                    pub_content.append(dic["content"] or u'未公示')
                except:
                    pub_content.append(u'未公示')
                try:
                    pub_date.append(dic["decisionDate"] or u'')
                except:
                    pub_date.append(u'')

                try:
                    pub_authority.append(dic["departmentName"] or u'')
                except:
                    pub_authority.append(u'')

                try:
                    pub_people.append(dic["legalPersonName"] or u'')
                except:
                    pub_people.append(u'')

        item["pub_code"] = pub_code
        item["pub_type"] = pub_type
        item["pub_content"] = pub_content
        item["pub_date"] = pub_date
        item["pub_authority"] = pub_authority
        item["pub_people"] = pub_people

        if len(response.body) > 1500:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/punishment.json?name=' + str(item["company_name"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_adminis_pubnish)
            yield request
        else:
            item["set_time"] = []
            item["set_reason"] = []
            item["set_department"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/illegal.json?name=' + str(item["company_name"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_seriously_illegal)
            yield request

    def parse_seriously_illegal(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        set_time = item["set_time"]
        set_reason = item["set_reason"]
        set_department = item["set_department"]

        if flag[19] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["items"]:
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["putDate"])[:10])))
                    set_time.append(date)
                except:
                    set_time.append(u'')
                try:
                    set_reason.append(dic["putReason"])
                except:
                    set_reason.append(u'')
                try:
                    set_department.append(dic["putDepartment"])
                except:
                    set_department.append(u'')

        item["set_time"] = set_time
        item["set_reason"] = set_reason
        item["set_department"] = set_department

        if len(response.body) > 700:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/illegal.json?name=' + str(item["company_name"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_seriously_illegal)
            yield request
        else:
            item["regist_date"] = []
            item["regist_num"] = []
            item["regist_cond"] = []
            item["pledged_amount"] = []
            item["pledgor"] = []
            item["pledged_code"] = []
            item["pledgee"] = []
            item["pledgee_code"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/companyEquity.json?name=' + str(item["company_name"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_equity_pledge)
            yield request

    def parse_equity_pledge(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        regist_date = item["regist_date"]
        regist_num = item["regist_num"]
        regist_cond = item["regist_cond"]
        pledged_amount = item["pledged_amount"]
        pledgor = item["pledgor"]
        pledged_code = item["pledged_code"]
        pledgee = item["pledgee"]
        pledgee_code = item["pledgee_code"]

        if flag[20] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["items"]:
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["regDate"])[:10])))
                    regist_date.append(date)
                except:
                    regist_date.append(u'')
                try:
                    regist_num.append(dic["regNumber"] or u'')
                except:
                    regist_num.append(u'')
                try:
                    regist_cond.append(dic["state"] or u'')
                except:
                    regist_cond.append(u'')
                try:
                    pledged_amount.append(dic["equityAmount"] or u'')
                except:
                    pledged_amount.append(u'')
                try:
                    pledgor.append(dic["pledgor"] or u'')
                except:
                    pledgor.append(u'')

                try:
                    pledged_code.append(dic["certifNumber"] or u'')
                except:
                    pledged_code.append(u'')

                try:
                    pledgee.append(dic["pledgee"] or u'')
                except:
                    pledgee.append(u'')
                try:
                    pledgee_code.append(dic["certifNumberR"] or u'')
                except:
                    pledgee_code.append(u'')

        item["regist_date"] = regist_date
        item["regist_num"] = regist_num
        item["regist_cond"] = regist_cond
        item["pledged_amount"] = pledged_amount
        item["pledgor"] = pledgor
        item["pledged_code"] = pledged_code
        item["pledgee"] = pledgee
        item["pledgee_code"] = pledgee_code
        item["pledge_remark"] = []

        if len(response.body) > 900:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/companyEquity.json?name=' + str(item["company_name"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_equity_pledge)
            yield request
        else:
            item["registed_num"] = []
            item["registed_depart"] = []
            item["registed_date"] = []
            item["registed_cond"] = []
            item["vouched_type"] = []
            item["vouched_amount"] = []
            item["debt_start"] = []
            item["debt_end"] = []
            item["vouched_range"] = []
            item["mortgagee_info"] = []
            item["pawn_info"] = []
            item["cancel_date"] = []
            item["cancel_reason"] = []

            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/mortgageInfo.json?name=' + str(item["company_name"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_chattel_mortgage)
            yield request

    def parse_chattel_mortgage(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        registed_num = item["registed_num"]
        registed_depart = item["registed_depart"]
        registed_date = item["registed_date"]
        registed_cond = item["registed_cond"]
        vouched_type = item["vouched_type"]
        vouched_amount = item["vouched_amount"]
        debt_start = item["debt_start"]
        debt_end = item["debt_end"]
        vouched_range = item["vouched_range"]
        cancel_date = item["cancel_date"]
        cancel_reason = item["cancel_reason"]
        mortgagee_info = item["mortgagee_info"]
        pawn_info = item["pawn_info"]

        if flag[21] is 1:
            data = json.loads(response.body)
            data = json.loads(data["data"])
            for dic in data["items"]:
                try:
                    registed_num.append(dic["baseInfo"]["regNum"] or u'')
                except:
                    registed_num.append(u'')

                try:
                    registed_depart.append(dic["baseInfo"]["regDepartment"] or u'')
                except:
                    registed_depart.append(u'')

                try:
                    registed_date.append(dic["baseInfo"]["regDate"] or u'')
                except:
                    registed_date.append(u'')

                try:
                    registed_cond.append(dic["baseInfo"]["status"] or u'')
                except:
                    registed_cond.append(u'')

                try:
                    vouched_type.append(dic["baseInfo"]["type"] or u'')
                except:
                    vouched_type.append(u'')

                try:
                    vouched_amount.append(dic["baseInfo"]["amount"] or u'')
                except:
                    vouched_amount.append(u'')

                try:
                    debt_start.append(dic["baseInfo"]["term"][2:12].replace(u'年', '-').replace(u'月', '-').replace(u'日', '') or u'')
                except:
                    debt_start.append(u'')

                try:
                    debt_end.append(dic["baseInfo"]["term"][-10:].replace(u'年', '-').replace(u'月', '-').replace(u'日', '') or u'')
                except:
                    debt_end.append(u'')

                try:
                    vouched_range.append(dic["baseInfo"]["scope"] or u'')
                except:
                    vouched_range.append(u'')
                try:
                    cancel_date.append(dic["baseInfo"]["cancelDate"])
                    cancel_reason.append(dic["baseInfo"]["cancelReason"])
                except:
                    cancel_date.append(u'')
                    cancel_reason.append(u'')

                safe_append(mortgagee_info, dic, 'peopleInfo')

                try:
                    pawn_info.append(str(dic["pawnInfoList"]).decode("unicode-escape"))
                except:
                    pawn_info.append(u'')

        item["registed_num"] = registed_num
        item["registed_depart"] = registed_depart
        item["registed_date"] = registed_date
        item["registed_cond"] = registed_cond
        item["vouched_type"] = vouched_type
        item["vouched_amount"] = vouched_amount
        item["debt_start"] = debt_start
        item["debt_end"] = debt_end
        item["vouched_range"] = vouched_range
        item["pawn_remark"] = []
        item["cancel_date"] = cancel_date
        item["cancel_reason"] = cancel_reason
        item["mortgagee_info"] = mortgagee_info
        item["pawn_info"] = pawn_info

        if len(response.body) > 3000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/mortgageInfo.json?name=' + str(item["company_name"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_chattel_mortgage)
            yield request
        else:
            item["tax_date"] = []
            item["tax_num"] = []
            item["tax_type"] = []
            item["tax_current"] = []
            item["tax_balance"] = []
            item["tax_depart"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/owntax.json?id=' + str(item["company_id"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_owe_tax)
            yield request

    def parse_owe_tax(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        tax_date = item["tax_date"]
        tax_num = item["tax_num"]
        tax_type = item["tax_type"]
        tax_current = item["tax_current"]
        tax_balance = item["tax_balance"]
        tax_depart = item["tax_depart"]

        if flag[22] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["items"]:
                try:
                    tax_date.append(dic["publishDate"] or u'')
                except:
                    tax_date.append(u'')
                try:
                    tax_num.append(dic["taxIdNumber"] or u'')
                except:
                    tax_num.append(u'')
                try:
                    tax_type.append(dic["taxCategory"] or u'')
                except:
                    tax_type.append(u'')
                try:
                    tax_current.append(dic[""] or u'')
                except:
                    tax_current.append(u'')
                try:
                    tax_balance.append(dic["ownTaxAmount"] or u'')
                except:
                    tax_balance.append(u'')
                try:
                    tax_depart.append(dic[""] or u'')
                except:
                    tax_depart.append(u'')

        item["tax_date"] = tax_date
        item["tax_num"] = tax_num
        item["tax_type"] = tax_type
        item["tax_current"] = tax_current
        item["tax_balance"] = tax_balance
        item["tax_depart"] = tax_depart

        if len(response.body) > 800:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/owntax.json?id=' + str(item["company_id"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_owe_tax)
            yield request
        else:
            item["bid_url"] = []
            item["bid_time"] = []
            item["bid_title"] = []
            item["bid_purchaser"] = []
            item["bid_content"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/bid.json?id=' + str(item["company_id"]) + '&ps=10&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_bidding)
            yield request

    def parse_bidding(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        bid_url = item["bid_url"]
        bid_time = item["bid_time"]
        bid_title = item["bid_title"]
        bid_purchaser = item["bid_purchaser"]
        bid_content = item["bid_content"]

        try:
            data = json.loads(response.body)
            test = data["data"]["items"]
        except:
            flag[23] = 0

        if flag[23] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["items"]:
                try:
                    url = 'http://www.tianyancha.com/extend/getCompanyBidByUUID.json?uuid=' + str(dic["uuid"])
                    bid_url.append(url)
                except:
                    bid_url.append(u'')
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["publishTime"])[:10])))
                    bid_time.append(date)
                except:
                    bid_time.append(u'')
                try:
                    bid_title.append(dic["title"] or u'')
                except:
                    bid_title.append(u'')

                try:
                    bid_purchaser.append(dic["purchaser"] or u'')
                except:
                    bid_purchaser.append(u'')

                safe_append(bid_content, dic, "intro")

        item["bid_url"] = bid_url
        item["bid_time"] = bid_time
        item["bid_title"] = bid_title
        item["bid_purchaser"] = bid_purchaser
        item["bid_content"] = bid_content
        item["bid_related"] = []
        item["rfp_id"] = []

        if len(response.body) > 10000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/bid.json?id=' + str(item["company_id"]) + '&ps=10&pn=1' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_bidding)
            yield request
        else:
            item["page"] = 1
            if len(item["bid_url"]) > 0:
                next_url = item["bid_url"][0]
                request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_bidding_detail)
                yield request
            else:
                item["bond_name"] = []
                item["bond_code"] = []
                item["bond_publisher"] = []
                item["bond_type"] = []
                item["bond_start"] = []
                item["bond_end"] = []
                item["bond_duration"] = []
                item["trading_day"] = []
                item["interest_mode"] = []
                item["bond_delisting"] = []
                item["credit_agency"] = []
                item["bond_rating"] = []
                item["face_value"] = []
                item["reference_rate"] = []
                item["coupon_rate"] = []
                item["actual_circulation"] = []
                item["planned_circulation"] = []
                item["issue_price"] = []
                item["spread"] = []
                item["frequency"] = []
                item["bond_date"] = []
                item["exercise_type"] = []
                item["exercise_date"] = []
                item["trustee"] = []
                item["circulation_scope"] = []
                item["page"] = 1

                next_url = 'http://www.tianyancha.com/extend/getBondList.json?companyName=' + str(item["company_name"]) + '&ps=5&pn=1'
                request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_bond_infomation)
                yield request

    def parse_bidding_detail(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        bid_related = item["bid_related"]

        bid_related.append(list(set(re.findall(r'http://www.tianyancha.com/company/(\d*)', response.body))))

        item["bid_related"] = bid_related

        if response.url != item["bid_url"][-1]:
            next_url = item["bid_url"][item["page"]]
            item["page"] += 1
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag},
                                     callback=self.parse_bidding_detail)
            yield request
        else:
            item["page"] = 1

            item["bond_name"] = []
            item["bond_code"] = []
            item["bond_publisher"] = []
            item["bond_type"] = []
            item["bond_start"] = []
            item["bond_end"] = []
            item["bond_duration"] = []
            item["trading_day"] = []
            item["interest_mode"] = []
            item["bond_delisting"] = []
            item["credit_agency"] = []
            item["bond_rating"] = []
            item["face_value"] = []
            item["reference_rate"] = []
            item["coupon_rate"] = []
            item["actual_circulation"] = []
            item["planned_circulation"] = []
            item["issue_price"] = []
            item["spread"] = []
            item["frequency"] = []
            item["bond_date"] = []
            item["exercise_type"] = []
            item["exercise_date"] = []
            item["trustee"] = []
            item["circulation_scope"] = []

            next_url = 'http://www.tianyancha.com/extend/getBondList.json?companyName=' + str(
                item["company_name"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag},
                                     callback=self.parse_bond_infomation)
            yield request


    def parse_bond_infomation(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]
        bond_name = item["bond_name"]
        bond_code = item["bond_code"]
        bond_publisher = item["bond_publisher"]
        bond_type = item["bond_type"]
        bond_start = item["bond_start"]
        bond_end = item["bond_end"]
        bond_duration = item["bond_duration"]
        trading_day = item["trading_day"]
        interest_mode = item["interest_mode"]
        bond_delisting = item["bond_delisting"]
        credit_agency = item["credit_agency"]
        bond_rating = item["bond_rating"]
        face_value = item["face_value"]
        reference_rate = item["reference_rate"]
        coupon_rate = item["coupon_rate"]
        actual_circulation = item["actual_circulation"]
        planned_circulation = item["planned_circulation"]
        issue_price = item["issue_price"]
        spread = item["spread"]
        frequency = item["frequency"]
        bond_date = item["bond_date"]
        exercise_type = item["exercise_type"]
        exercise_date = item["exercise_date"]
        trustee = item["trustee"]
        circulation_scope = item["circulation_scope"]

        if flag[24] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["bondList"]:
                try:
                    bond_name.append(dic["bondName"] or u'')
                except:
                    bond_name.append(u'')

                try:
                    bond_code.append(dic["bondNum"] or u'')
                except:
                    bond_code.append(u'')

                try:
                    bond_publisher.append(dic["publisherName"] or u'')
                except:
                    bond_publisher.append(u'')
                try:
                    bond_type.append(dic["bondType"] or u'')
                except:
                    bond_type.append(u'')
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["publishTime"])[:10])))
                    bond_start.append(date)
                except:
                    bond_start.append(u'')
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["publishExpireTime"])[:10])))
                    bond_end.append(date)
                except:
                    bond_end.append(u'')
                try:
                    bond_duration.append(dic["bondTimeLimit"] or u'')
                except:
                    bond_duration.append(u'')

                try:
                    trading_day.append(dic["bondTradeTime"] or u'')
                except:
                    trading_day.append(u'')

                try:
                    interest_mode.append(dic["calInterestType"] or u'')
                except:
                    interest_mode.append(u'')

                try:
                    bond_delisting.append(dic["bondStopTime"] or u'')
                except:
                    bond_delisting.append(u'')
                try:
                    credit_agency.append(dic["creditRatingGov"] or u'未公示')
                except:
                    credit_agency.append(u'未公示')
                try:
                    bond_rating.append(dic["debtRating"] or u'未公示')
                except:
                    bond_rating.append(u'未公示')
                try:
                    face_value.append(dic["faceValue"] or u'')
                except:
                    face_value.append(u'')

                try:
                    reference_rate.append(dic["refInterestRate"] or u'未公示')
                except:
                    reference_rate.append(u'未公示')
                try:
                    coupon_rate.append(dic["faceInterestRate"] or u'')
                except:
                    coupon_rate.append(u'')

                try:
                    actual_circulation.append(dic["realIssuedQuantity"] or u'')
                except:
                    actual_circulation.append(u'')

                try:
                    planned_circulation.append(dic["planIssuedQuantity"] or u'')
                except:
                    planned_circulation.append(u'')

                try:
                    issue_price.append(dic["issuedPrice"] or u'')
                except:
                    issue_price.append(u'')

                try:
                    spread.append(dic["interestDiff"] or u'未公示')
                except:
                    spread.append(u'未公示')
                try:
                    frequency.append(dic["payInterestHZ"] or u'')
                except:
                    frequency.append(u'')

                try:
                    bond_date.append(dic["startCalInterestTime"] or u'')
                except:
                    bond_date.append(u'')

                try:
                    trustee.append(dic["escrowAgent"] or u'')
                except:
                    trustee.append(u'')

                try:
                    circulation_scope.append(dic["flowRange"] or u'')
                except:
                    circulation_scope.append(u'')
                try:
                    exercise_type.append(dic["exeRightType"] or u'未公示')
                except:
                    exercise_type.append(u'未公示')
                try:
                    exercise_date.append(dic["exeRightTime"] or u'未公示')
                except:
                    exercise_date.append(u'未公示')

        item["bond_name"] = bond_name
        item["bond_code"] = bond_code
        item["bond_publisher"] = bond_publisher
        item["bond_type"] = bond_type
        item["bond_start"] = bond_start
        item["bond_end"] = bond_end
        item["bond_duration"] = bond_duration
        item["trading_day"] = trading_day
        item["interest_mode"] = interest_mode
        item["bond_delisting"] = bond_delisting
        item["credit_agency"] = credit_agency
        item["bond_rating"] = bond_rating
        item["face_value"] = face_value
        item["reference_rate"] = reference_rate
        item["coupon_rate"] = coupon_rate
        item["actual_circulation"] = actual_circulation
        item["planned_circulation"] = planned_circulation
        item["issue_price"] = issue_price
        item["spread"] = spread
        item["frequency"] = frequency
        item["bond_date"] = bond_date
        item["exercise_type"] = exercise_type
        item["exercise_date"] = exercise_date
        item["trustee"] = trustee
        item["circulation_scope"] = circulation_scope

        if len(response.body) > 2000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/extend/getBondList.json?companyName=' + str(item["company_name"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_bond_infomation)
            yield request
        else:
            item["admini_region"] = []
            item["supervision_num"] = []
            item["pruchase_trustee"] = []
            item["trasaction_price"] = []
            item["signed_date"] = []
            item["total_area"] = []
            item["parcel_location"] = []
            item["purchase_assignee"] = []
            item["superior_company"] = []
            item["land_use"] = []
            item["supply_mode"] = []
            item["max_volume"] = []
            item["min_volume"] = []
            item["start_time"] = []
            item["end_time"] = []
            item["link_url"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/purchaseland.json?name=' + str(item["company_name"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_purchase_island)
            yield request

    def parse_purchase_island(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        admini_region = item["admini_region"]
        supervision_num = item["supervision_num"]
        pruchase_trustee = item["pruchase_trustee"]
        trasaction_price = item["trasaction_price"]
        signed_date = item["signed_date"]
        total_area = item["total_area"]
        parcel_location = item["parcel_location"]
        purchase_assignee = item["purchase_assignee"]
        superior_company = item["superior_company"]
        land_use = item["land_use"]
        supply_mode = item["supply_mode"]
        max_volume = item["max_volume"]
        min_volume = item["min_volume"]
        start_time = item["start_time"]
        end_time = item["end_time"]
        link_url = item["link_url"]

        if flag[25] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["companyPurchaseLandList"]:
                try:
                    admini_region.append(dic["adminRegion"] or u'')
                except:
                    admini_region.append(u'')

                try:
                    supervision_num.append(dic["elecSupervisorNo"] or u'')
                except:
                    supervision_num.append(u'')

                try:
                    pruchase_trustee.append(dic["assignee"] or u'')
                except:
                    pruchase_trustee.append(u'')

                try:
                    trasaction_price.append(dic["dealPrice"] or u'')
                except:
                    trasaction_price.append(u'')
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["signedDate"])[:10])))
                    signed_date.append(date)
                except:
                    signed_date.append(u'')
                try:
                    total_area.append(dic["totalArea"] or u'')
                except:
                    total_area.append(u'')

                try:
                    parcel_location.append(dic["location"] or u'')
                except:
                    parcel_location.append(u'')

                try:
                    purchase_assignee.append(dic["assignee"] or u'')
                except:
                    purchase_assignee.append(u'')

                try:
                    superior_company.append(dic["parentCompany"] or u'')
                except:
                    superior_company.append(u'')

                try:
                    land_use.append(dic["purpose"] or u'')
                except:
                    land_use.append(u'')

                try:
                    supply_mode.append(dic["supplyWay"] or u'')
                except:
                    supply_mode.append(u'')

                try:
                    max_volume.append(dic["maxVolume"] or u'')
                except:
                    max_volume.append(u'')

                try:
                    min_volume.append(dic["minVolume"] or u'')
                except:
                    min_volume.append(u'')
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["startTime"])[:10])))
                    start_time.append(date)
                except:
                    start_time.append(u'')
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["endTime"])[:10])))
                    end_time.append(date)
                except:
                    end_time.append(u'')
                try:
                    link_url.append(dic["linkUrl"] or u'')
                except:
                    link_url.append(u'')

        item["admini_region"] = admini_region
        item["supervision_num"] = supervision_num
        item["pruchase_trustee"] = pruchase_trustee
        item["trasaction_price"] = trasaction_price
        item["signed_date"] = signed_date
        item["total_area"] = total_area
        item["parcel_location"] = parcel_location
        item["purchase_assignee"] = purchase_assignee
        item["superior_company"] = superior_company
        item["land_use"] = land_use
        item["supply_mode"] = supply_mode
        item["max_volume"] = max_volume
        item["min_volume"] = min_volume
        item["start_time"] = start_time
        item["end_time"] = end_time
        item["link_url"] = link_url

        if len(response.body) > 2000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/purchaseland.json?name=' + str(item["company_name"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_purchase_island)
            yield request
        else:
            item["employ_position"] = []
            item["employ_city"] = []
            item["employ_area"] = []
            item["employ_company"] = []
            item["wage"] = []
            item["experience"] = []
            item["source"] = []
            item["source_url"] = []
            item["start_date"] = []
            item["end_date"] = []
            item["education"] = []
            item["employ_num"] = []
            item["position_desc"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/extend/getEmploymentList.json?companyName=' + str(item["company_name"]) + '&ps=10&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_the_employ)
            yield request

    def parse_the_employ(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        employ_position = item["employ_position"]
        employ_city = item["employ_city"]
        employ_area = item["employ_area"]
        employ_company = item["employ_company"]
        wage = item["wage"]
        experience = item["experience"]
        source = item["source"]
        source_url = item["source_url"]
        start_date = item["start_date"]
        end_date = item["end_date"]
        education = item["education"]
        employ_num = item["employ_num"]
        position_desc = item["position_desc"]

        if flag[26] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["companyEmploymentList"]:
                try:
                    employ_position.append(dic["title"] or u'')
                except:
                    employ_position.append(u'')

                try:
                    employ_city.append(dic["city"] or u'')
                except:
                    employ_city.append(u'')

                try:
                    employ_area.append(dic["district"] or u'')
                except:
                    employ_area.append(u'')

                try:
                    employ_company.append(dic["companyName"] or u'')
                except:
                    employ_company.append(u'')

                try:
                    wage.append(dic["oriSalary"] or u'')
                except:
                    wage.append(u'')

                try:
                    experience.append(dic["experience"] or u'')
                except:
                    experience.append(u'')

                try:
                    source.append(dic["source"] or u'')
                except:
                    source.append(u'')

                try:
                    source_url.append(dic["urlPath"] or u'')
                except:
                    source_url.append(u'')
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["startdate"])[:10])))
                    start_date.append(date)
                except:
                    start_date.append(u'')
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["enddate"])[:10])))
                    end_date.append(date)
                except:
                    end_date.append(u'')
                try:
                    education.append(dic["education"] or u'')
                except:
                    education.append(u'')

                try:
                    employ_num.append(dic["employerNumber"] or u'')
                except:
                    employ_num.append(u'')

                try:
                    position_desc.append(dic["description"] or u'')
                except:
                    position_desc.append(u'')

        item["employ_position"] = employ_position
        item["employ_city"] = employ_city
        item["employ_area"] = employ_area
        item["employ_company"] = employ_company
        item["wage"] = wage
        item["experience"] = experience
        item["source"] = source
        item["source_url"] = source_url
        item["start_date"] = start_date
        item["end_date"] = end_date
        item["education"] = education
        item["employ_num"] = employ_num
        item["position_desc"] = position_desc

        if len(response.body) > 6000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/extend/getEmploymentList.json?companyName=' + str(item["company_name"]) + '&ps=10&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_the_employ)
            yield request
        else:
            item["rating_year"] = []
            item["rating_level"] = []
            item["rating_type"] = []
            item["rating_num"] = []
            item["rating_office"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/taxcredit.json?id=' + str(item["company_id"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_rating_tax)
            yield request

    def parse_rating_tax(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        rating_year = item["rating_year"]
        rating_level = item["rating_level"]
        rating_type = item["rating_type"]
        rating_num = item["rating_num"]
        rating_office = item["rating_office"]

        if flag[27] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["items"]:
                try:
                    rating_year.append(dic["year"] or u'')
                except:
                    rating_year.append(u'')

                try:
                    rating_level.append(dic["grade"] or u'')
                except:
                    rating_level.append(u'')

                try:
                    rating_type.append(dic["type"] or u'')
                except:
                    rating_type.append(u'')

                try:
                    rating_num.append(dic["idNumber"] or u'')
                except:
                    rating_num.append(u'')

                try:
                    rating_office.append(dic["evalDepartment"] or u'')
                except:
                    rating_office.append(u'')

        if len(response.body) > 500:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/taxcredit.json?id=' + str(item["company_id"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_rating_tax)
            yield request
        else:
            item["check_date"] = []
            item["check_type"] = []
            item["check_result"] = []
            item["check_office"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/companyCheckInfo.json?name=' + str(item["company_name"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_random_check)
            yield request

    def parse_random_check(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        check_date = item["check_date"]
        check_type = item["check_type"]
        check_result = item["check_result"]
        check_office = item["check_office"]

        if flag[28] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["items"]:
                try:
                    check_date.append(dic["checkDate"] or '')
                except:
                    check_date.append('')
                try:
                    check_type.append(dic["checkType"] or '')
                except:
                    check_type.append('')
                try:
                    check_result.append(dic["checkResult"] or '')
                except:
                    check_result.append('')
                try:
                    check_office.append(dic["checkOrg"] or '')
                except:
                    check_office.append('')

        item["check_date"] = check_date
        item["check_type"] = check_type
        item["check_result"] = check_result
        item["check_office"] = check_office

        if len(response.body) > 300:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/companyCheckInfo.json?name=' + str(item["company_name"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_random_check)
            yield request
        else:
            item["product_icon"] = []
            item["product_title"] = []
            item["product_short"] = []
            item["product_type"] = []
            item["product_field"] = []
            item["product_desc"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/appbkinfo.json?id=' + str(item["company_id"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_product_info)
            yield request

    def parse_product_info(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        product_icon = item["product_icon"]
        product_title = item["product_title"]
        product_short = item["product_short"]
        product_type = item["product_type"]
        product_field = item["product_field"]
        product_desc = item["product_desc"]

        if flag[29] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["items"]:
                try:
                    product_icon.append(dic["icon"] or u'')
                except:
                    product_icon.append(u'')

                try:
                    product_title.append(dic["name"] or u'')
                except:
                    product_title.append(u'')

                try:
                    product_short.append(dic["filterName"] or u'')
                except:
                    product_short.append(u'')

                try:
                    product_type.append(dic["type"] or u'')
                except:
                    product_type.append(u'')

                try:
                    product_field.append(dic["classes"] or u'')
                except:
                    product_field.append(u'')

                try:
                    product_desc.append(dic["brief"] or u'')
                except:
                    product_desc.append(u'')

        item["product_icon"] = product_icon
        item["product_title"] = product_title
        item["product_short"] = product_short
        item["product_type"] = product_type
        item["product_field"] = product_field
        item["product_desc"] = product_desc

        if len(response.body) > 3000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/appbkinfo.json?id=' + str(item["company_id"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_product_info)
            yield request
        else:
            item["device_name"] = []
            item["cert_type"] = []
            item["cert_start"] = []
            item["cert_end"] = []
            item["device_num"] = []
            item["permit_num"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/qualification.json?id=' + str(item["company_id"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_quality_cert)
            yield request

    def parse_quality_cert(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        device_name = item["device_name"]
        cert_type = item["cert_type"]
        cert_start = item["cert_start"]
        cert_end = item["cert_end"]
        device_num = item["device_num"]
        permit_num = item["permit_num"]

        if flag[30] is 1:
            data = json.loads(response.body)
            for dic in data["data"]["items"]:
                try:
                    device_num.append(dic["deviceType"] or u'')
                except:
                    device_num.append(u'')

                try:
                    permit_num.append(dic["licenceNum"] or u'')
                except:
                    permit_num.append(u'')

                try:
                    device_name.append(dic["deviceName"] or u'')
                except:
                    device_name.append(u'')

                try:
                    cert_type.append(dic["licenceType"] or u'')
                except:
                    cert_type.append(u'')
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["issueDate"])[:10])))
                    cert_start.append(date)
                except:
                    cert_start.append(u'')
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["toDate"])[:10])))
                    cert_end.append(date)
                except:
                    cert_end.append(u'')

        item["device_name"] = device_name
        item["cert_type"] = cert_type
        item["cert_start"] = cert_start
        item["cert_end"] = cert_end
        item["device_num"] = device_num
        item["permit_num"] = permit_num

        if len(response.body) > 1000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/qualification.json?id=' + str(item["company_id"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_quality_cert)
            yield request
        else:
            item["brand_date"] = []
            item["brand_icon"] = []
            item["brand_name"] = []
            item["brand_num"] = []
            item["brand_type"] = []
            item["brand_cond"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/tm/getTmList.json?id=' + str(item["company_id"]) + '&ps=5&&pageNum=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_brand_info)
            yield request

    def parse_brand_info(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        brand_date = item["brand_date"]
        brand_icon = item["brand_icon"]
        brand_name = item["brand_name"]
        brand_num = item["brand_num"]
        brand_type = item["brand_type"]
        brand_cond = item["brand_cond"]

        data = json.loads(response.body)
        try:
            test = data["data"]["items"]
        except:
            flag[31] = 0

        if flag[31] is 1:
            for dic in data["data"]["items"]:
                try:
                    date = time.strftime("%Y-%m-%d", time.localtime(int(str(dic["appDate"])[:10])))
                    brand_date.append(date)
                except:
                    brand_date.append(u'')
                try:
                    brand_icon.append(dic["tmPic"] or u'')
                except:
                    brand_icon.append(u'')
                try:
                    brand_name.append(dic["tmName"] or u'')
                except:
                    brand_name.append(u'')
                try:
                    brand_num.append(dic["regNo"] or u'')
                except:
                    brand_num.append(u'')
                try:
                    brand_type.append(dic["intCls"] or u'')
                except:
                    brand_type.append(u'')
                try:
                    brand_cond.append(dic["category"] or u'')
                except:
                    brand_cond.append(u'')

        item["brand_date"] = brand_date
        item["brand_icon"] = brand_icon
        item["brand_name"] = brand_name
        item["brand_num"] = brand_num
        item["brand_type"] = brand_type
        item["brand_cond"] = brand_cond

        if len(response.body) > 800:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/tm/getTmList.json?id=' + str(item["company_id"]) + '&ps=5&&pageNum=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_brand_info)
            yield request
        else:
            item["patent_id"] = []
            item["patent_pic"] = []
            item["app_num"] = []
            item["patent_num"] = []
            item["category_num"] = []
            item["patent_name"] = []
            item["patent_address"] = []
            item["inventor"] = []
            item["applicant"] = []
            item["apply_date"] = []
            item["publish_date"] = []
            item["agency"] = []
            item["agent"] = []
            item["abstracts"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/patent.json?id=' + str(item["company_id"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_patent_info)
            yield request

    def parse_patent_info(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        patent_id = item["patent_id"]
        patent_pic = item["patent_pic"]
        app_num = item["app_num"]
        patent_num = item["patent_num"]
        category_num = item["category_num"]
        patent_name = item["patent_name"]
        patent_address = item["patent_address"]
        inventor = item["inventor"]
        applicant = item["applicant"]
        apply_date = item["apply_date"]
        publish_date = item["publish_date"]
        agency = item["agency"]
        agent = item["agent"]
        abstracts = item["abstracts"]

        data = json.loads(response.body)
        try:
            test = data["data"]["items"]
        except:
            flag[32] = 0

        if flag[32] is 1:
            for dic in data["data"]["items"]:
                try:
                    patent_pic.append(dic["imgUrl"] or u'')
                except:
                    patent_pic.append("u''")
                try:
                    app_num.append(dic["applicationPublishNum"] or u'')
                except:
                    app_num.append(u'')

                try:
                    patent_num.append(dic["patentNum"] or u'')
                except:
                    patent_num.append(u'')

                try:
                    category_num.append(dic["allCatNum"] or u'')
                except:
                    category_num.append(u'')

                try:
                    patent_name.append(dic["patentName"] or u'')
                except:
                    patent_name.append(u'')

                try:
                    patent_address.append(dic["address"] or u'')
                except:
                    patent_address.append(u'')

                try:
                    inventor.append(dic["inventor"] or u'')
                except:
                    inventor.append(u'')

                try:
                    applicant.append(dic["applicantName"] or u'')
                except:
                    applicant.append(u'')

                try:
                    apply_date.append(dic["applicationTime"] or u'')
                except:
                    apply_date.append(u'')

                try:
                    publish_date.append(dic["applicationPublishTime"] or u'')
                except:
                    publish_date.append(u'')

                try:
                    patent_id.append(dic["pid"] or u'')
                except:
                    patent_id.append(u'')
                try:
                    agency.append(dic["agency"] or u'')
                except:
                    agency.append(u'')
                try:
                    agent.append(dic["agent"] or u'')
                except:
                    agent.append(u'')
                try:
                    abstracts.append(dic["abstracts"] or u'')
                except:
                    abstracts.append(u'')

        item["patent_id"] = patent_id
        item["patent_pic"] = patent_pic
        item["app_num"] = app_num
        item["patent_num"] = patent_num
        item["category_num"] = category_num
        item["patent_name"] = patent_name
        item["patent_address"] = patent_address
        item["inventor"] = inventor
        item["applicant"] = applicant
        item["apply_date"] = apply_date
        item["publish_date"] = publish_date
        item["agency"] = agency
        item["agent"] = agent
        item["abstracts"] = abstracts

        if len(response.body) > 5000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/patent.json?id=' + str(item["company_id"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_patent_info)
            yield request
        else:
            item["full_name"] = []
            item["simple_name"] = []
            item["reg_num"] = []
            item["cat_num"] = []
            item["version"] = []
            item["author_nationality"] = []
            item["first_publish"] = []
            item["reg_time"] = []
            item["page"] = 1

            next_url = 'http://www.tianyancha.com/expanse/copyReg.json?id=' + str(item["company_id"]) + '&ps=5&pn=1'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_copyright_info)
            yield request

    def parse_copyright_info(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        full_name = item["full_name"]
        simple_name = item["simple_name"]
        reg_num = item["reg_num"]
        cat_num = item["cat_num"]
        version = item["version"]
        author_nationality = item["author_nationality"]
        first_publish = item["first_publish"]
        reg_time = item["reg_time"]

        data = json.loads(response.body)
        try:
            test = data["data"]["items"]
        except:
            flag[33] = 0

        if flag[33] is 1:
            for dic in data["data"]["items"]:
                try:
                    simple_name.append(dic["simplename"] or u'')
                except:
                    simple_name.append(u'')
                try:
                    reg_num.append(dic["regnum"] or u'')
                except:
                    reg_num.append(u'')

                try:
                    cat_num.append(dic["catnum"] or u'')
                except:
                    cat_num.append(u'')

                try:
                    version.append(dic["version"] or u'')
                except:
                    version.append(u'')

                try:
                    author_nationality.append(dic["authorNationality"] or u'')
                except:
                    author_nationality.append(u'')

                try:
                    first_publish.append(dic["publishtime"] or u'')
                except:
                    first_publish.append(u'')

                try:
                    reg_time.append(dic["regtime"] or u'')
                except:
                    reg_time.append(u'')

                try:
                    full_name.append(dic["fullname"] or u'')
                except:
                    full_name.append(u'')

        item["full_name"] = full_name
        item["simple_name"] = simple_name
        item["reg_num"] = reg_num
        item["cat_num"] = cat_num
        item["version"] = version
        item["author_nationality"] = author_nationality
        item["first_publish"] = first_publish
        item["reg_time"] = reg_time

        if len(response.body) > 1000:
            item["page"] += 1
            next_url = 'http://www.tianyancha.com/expanse/copyReg.json?id=' + str(item["company_id"]) + '&ps=5&pn=' + str(item["page"])
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_copyright_info)
            yield request
        else:
            next_url = 'http://www.tianyancha.com/v2/IcpList/' + str(item["company_id"]) + '.json'
            request = scrapy.Request(url=next_url, meta={"item": item, "flag": flag}, callback=self.parse_website_filing)
            yield request

    def parse_website_filing(self, response):
        flag = response.meta["flag"]
        item = response.meta["item"]

        record_date = []
        web_name = []
        web_url = []
        record_num = []
        web_status = []
        unit_nature = []
        domain_name = []

        data = json.loads(response.body)
        try:
            test = data["data"]
        except:
            flag[34] = 0

        if flag[34] is 1:
            for dic in data["data"]:
                try:
                    domain_name.append(dic["ym"] or u'')
                except:
                    domain_name.append(u'')
                try:
                    record_date.append(dic["examineDate"] or u'')
                except:
                    record_date.append(u'')

                try:
                    web_name.append(dic["webName"] or u'')
                except:
                    web_name.append(u'')

                try:
                    record_num.append(dic["liscense"] or u'')
                except:
                    record_num.append(u'')

                web_status.append(u'正常')

                try:
                    unit_nature.append(dic["companyType"] or u'')
                except:
                    unit_nature.append(u'')
                try:
                    web = '，'.join(dic["webSite"])
                    web_url.append(web)
                except:
                    web_url.append(u'')

        item["record_date"] = record_date
        item["web_name"] = web_name
        item["web_url"] = web_url
        item["record_num"] = record_num
        item["web_status"] = web_status
        item["unit_nature"] = unit_nature
        item["domain_name"] = domain_name

        return item
