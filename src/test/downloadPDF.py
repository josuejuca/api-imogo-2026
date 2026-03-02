import requests
import os
from urllib.parse import urlparse

def baixar_pdf(url, nome_arquivo=None):
    """
    Baixa um arquivo PDF de uma URL e salva localmente.
    
    Args:
        url (str): URL do PDF a ser baixado
        nome_arquivo (str): Nome do arquivo para salvar (opcional)
    
    Returns:
        bool: True se o download foi bem-sucedido, False caso contrário
    """
    try:
        # Headers para simular um navegador (evita bloqueios)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Fazer a requisição GET com streaming para arquivos grandes
        resposta = requests.get(url, headers=headers, stream=True, timeout=30)
        resposta.raise_for_status()  # Verifica se houve erro na requisição
        
        # Verificar se o conteúdo é realmente um PDF
        content_type = resposta.headers.get('content-type', '').lower()
        if 'application/pdf' not in content_type and 'octet-stream' not in content_type:
            print(f"Aviso: O tipo de conteúdo retornado é '{content_type}', não PDF confirmado.")
            # Mesmo assim, tenta salvar, pois pode ser um PDF com content-type errado
        
        # Determinar nome do arquivo
        if not nome_arquivo:
            # Tenta extrair nome da URL ou usa padrão
            nome_arquivo = os.path.basename(urlparse(url).path) or 'simulacao_financiamento.pdf'
            if not nome_arquivo.endswith('.pdf'):
                nome_arquivo += '.pdf'
        
        # Salvar o arquivo em partes (para arquivos grandes)
        with open(nome_arquivo, 'wb') as arquivo:
            for chunk in resposta.iter_content(chunk_size=8192):
                if chunk:
                    arquivo.write(chunk)
        
        print(f"✅ PDF baixado com sucesso: {nome_arquivo}")
        print(f"Tamanho do arquivo: {os.path.getsize(nome_arquivo)} bytes")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao baixar o PDF: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

# URL fornecida
url_pdf = "https://simulador.quadracred.com.br/cadastros/pdf/eyJpdiI6ImZHS2oxMWN5Zjc3amx1c2NKZU9qdGc9PSIsInZhbHVlIjoiWGpmdm16bXc3UkE1ekVpS2dYK2tOQT09IiwibWFjIjoiOTc0NjljNmZjNTJiYmRhZjZiM2M0OTBmM2MyMWQ4NmUxYmUyNWZjMzdiOTdmOTc1ZTBlNTgzM2E5MTliNjE1NiIsInRhZyI6IiJ9"

# Nome opcional para o arquivo (se não fornecer, será extraído da URL)
nome_do_arquivo = "simulacao_josue.pdf"

# Executar o download
baixar_pdf(url_pdf, nome_do_arquivo)