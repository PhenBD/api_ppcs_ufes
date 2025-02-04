from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
import camelot
import aiohttp
import asyncio
from spellchecker import SpellChecker
import ollama
import re
import time

model = "deepseek-r1:14b"

# Configurações Iniciais
spell = SpellChecker(language='pt')  # IA Leve

app = FastAPI()

def corrigir_com_deepseek(texto: str) -> str:
    start_time = time.time()
    try:
        # Tente chamar uma função simples do Ollama
        response = ollama.generate(model=model, prompt="Gere como resposta apenas a correção do texto em uma mesma linha, mantendo a formatação original: " + texto)
        texto_limpo = re.sub(r'<think>.*?</think>', '', response["response"], flags=re.DOTALL).strip()
        print(texto_limpo)
        return texto_limpo
    except ImportError:
        print("Ollama não está instalado.")
    except ConnectionError:
        print("Falha na conexão com Ollama. Verifique se o Ollama está em execução e acessível.")
    finally:
        elapsed_time = time.time() - start_time
        print(f"Tempo decorrido em corrigir_com_deepseek: {elapsed_time:.2f} segundos")

async def get_ppcs():
    start_time = time.time()
    url = "https://prograd.ufes.br/ppc"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    ppcs = []
    
    for ppc in soup.select("span.file a"):
        href = ppc['href']
        title = ppc.text
        
        title = title.split(" | ")
        
        if len(title) == 5:
            sede = title[0]
            curso = title[1]
            tipo = title[2]
            turno = title[3]
            versao = title[4]
        else:
            sede = title[0]
            curso = title[1]
            tipo = title[2]
            turno = "N/A"
            versao = title[3]

        ppcs.append({"sede": sede, 
                     "curso": curso, 
                     "tipo": tipo, 
                     "turno": turno,
                     "versao": versao,
                     "href": href})
        
    elapsed_time = time.time() - start_time
    print(f"Tempo decorrido em ler html: {elapsed_time:.2f} segundos")
        
    await fetch_all_pdfs(ppcs)
        
    return ppcs

async def fetch_pdf(session, pdf_url):
    async with session.get(pdf_url) as response:
        content = await response.read()
        with open("temp.pdf", "wb") as f:
            f.write(content)
        
        tables = camelot.read_pdf("temp.pdf", pages="all")
        combined_table = []
        for table in tables:
            combined_table.extend(table.df.values.tolist())
        
        # Filter rows
        combined_table = filter_rows(combined_table)
        
        return combined_table

def filter_rows(table):
    start_time = time.time()
    keys = ["Período", "Departamento", "Código", "Nome da Disciplina", "Cr", "C.H.S", "Distribuição T.E.L", "Pré-Requisitos", "Tipo"]
    combined_table = []
    for row in table:
        if combined_table and row[0] == "":
            combined_table[-1]["Nome da Disciplina"] = combined_table[-1]["Nome da Disciplina"] + " " + row[3]
        else:
            if len(row) == len(keys) and not any(s in row[0] for s in ['Período', 'Disciplina', 'Estágio', 'Conclusão']):
                row[1] = corrigir_com_deepseek(row[1])
                row[3] = corrigir_com_deepseek(row[3])
                print(row)
                combined_table.append(dict(zip(keys, row)))
    elapsed_time = time.time() - start_time
    print(f"Tempo decorrido em filter_rows: {elapsed_time:.2f} segundos")
    return combined_table

async def fetch_all_pdfs(ppcs):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=1)) as session:
        tasks = []
        for ppc in ppcs[:1]:  # Limitar a 10 PDFs para processamento
            start_time = time.time()
            task = asyncio.create_task(fetch_pdf(session, ppc["href"]))
            tasks.append(task)
            elapsed_time = time.time() - start_time
            print(f"Tempo decorrido em fetch_pdf: {elapsed_time:.2f} segundos")
        discipline_list = await asyncio.gather(*tasks)
        for i, ppc, disciplines in zip(ppcs, discipline_list):
            ppc["disciplinas"] = disciplines
            print("ppc concluídos: " + i + "/" + len(ppcs))

@app.get("/ppcs")
def ppcs():
    data = get_ppcs()
    return {"ppcs": data}