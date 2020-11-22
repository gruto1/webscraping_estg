import scrapy
from selenium import webdriver
from time import sleep


class TjalSpdrSpider(scrapy.Spider):

    name = 'tjal_2'
    allowed_domains = ['www2.tjal.jus.br/']


    def start_requests(self):

        input_num = "0731425-82.2014.8.02.0001"

        self.drive = webdriver.Chrome(executable_path=r'./chromedriver.exe')
        self.drive.get('https://www2.tjal.jus.br/cpopg/open.do')

        search_input_1 = self.drive.find_element_by_xpath('//*[@id="numeroDigitoAnoUnificado"]')
        search_input_1.send_keys(f'{input_num[:15]}')

        search_input_3 = self.drive.find_element_by_xpath('//*[@id="foroNumeroUnificado"]')
        search_input_3.send_keys(f'{input_num[-4:]}')

        self.drive.find_element_by_xpath('//*[@id="pbEnviar"]').click()

        url = self.drive.current_url

        yield scrapy.Request(url=url,
                             callback=self.parse,
                             dont_filter=True
                             )

    def parse(self, response):

        partes = []
        mov = []

        table_partes = response.xpath('//table[@id="tableTodasPartes"]/tr[@class="fundoClaro"]')

        for dados in table_partes:
            tipo = dados.xpath('./td/span/text()').get().strip()[:-1]
            tipo_adv = dados.xpath('./td[2]/span[@class="mensagemExibindo"]/text()').get()

            nome = dados.xpath('./td[2]/text()').get().strip()
            advg = [{'nome': f'{adv}'.strip(),'tipo': f'{tipo_adv}'.strip()[:-1]}
                    for adv in dados.xpath('./td[2]/text()[preceding-sibling::span]').getall() if adv.strip() != '']
            if nome != '':
                if tipo != 'Testemunha':
                    partes.append({
                        'nome': nome,
                        'tipo': tipo,
                        'Advogado(s)': advg
                        })
                else:
                    partes.append({
                        'nome': nome,
                        'tipo': tipo,
                    })

        table_mov = response.xpath('//tbody[@id="tabelaTodasMovimentacoes"]/tr')

        classe = response.xpath('//*[@class="secaoFormBody"]/tr[3]//span/text()').getall()[1]

        indice = len(table_mov)
        area = ''.join(response.xpath('//table[@class="secaoFormBody"]/tr[4]/td[2]/table/tr/td/text()').getall())
        juiz = response.xpath('//table[@class="secaoFormBody"]/tr[10]/td/span/text()').get()

        for dados in table_mov:

            data = dados.xpath('./td/text()').get().strip()
            indice_absoluto = indice
            e_movimento = True
            nome = dados.xpath('./td[3]/text()').get().strip().upper()
            if nome == '':
                nome = dados.xpath('./td[3]/a/text()').get().strip().upper()

            descri = dados.xpath('./td[3]/span[1]/text()').get().strip()
            indice -= 1

            if descri != '':
                mov.append({
                    'data': data,
                    'indice': indice_absoluto,
                    'descricao': descri,
                    'eMovimento': e_movimento,
                    'nomeOriginal': [nome]
                })
            else:
                mov.append({
                    'data': data,
                    'indice': indice_absoluto,
                    'eMovimento': e_movimento,
                    'nomeOriginal': [nome]
                })

        url = response.url
        grau = response.xpath('//*[@class="esajTituloPagina"]/text()').get().split()[-2]
        status_processo = response.xpath('//*[@class="secaoFormBody"]/tr[1]//span/text()').getall()[-1]
        numero_processo = response.xpath('//*[@class="secaoFormBody"]/tr[1]//span/text()').get().strip()
        data_hr = response.xpath('//*[@class="secaoFormBody"]/tr[7]//span/text()').getall()[-1].split('-')[0]
        orgao = response.xpath('//*[@class="secaoFormBody"]/tr[8]//span/text()').getall()[-1].split('-')[0]
        unidade = response.xpath('//*[@class="secaoFormBody"]/tr[8]//span/text()').getall()[-1].split('-')[1]

        yield {
                'uf': 'AL',
                'area': area.strip(),
                'juiz': juiz,
                'partes': partes,
                'sistema': 'ESAJ-TJAL',
                'segmento': 'JUSTICA ESTADUAL',
                'tribunal': 'TJ-AL',
                'movimentos': [mov],
                'url': url,
                'grauProcesso': grau,
                'orgaoJulgador': orgao,
                'unidadeOrigem': unidade,
                'classeProcessural': {classe},
                'dataDistribuicao': data_hr,
                'eProcessoDigital': True,
                'statusObservacao': status_processo,
                'numeroProcessoUnico': numero_processo,
             }
        sleep(1.5)
        self.drive.quit()

