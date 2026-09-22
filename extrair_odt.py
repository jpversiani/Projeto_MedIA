#!/usr/bin/env python3
import sys
import os
import zipfile
import xml.etree.ElementTree as ET

def extrair_odt_para_markdown(caminho_odt: str, caminho_saida_md: str = None) -> str:
    if not os.path.exists(caminho_odt):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_odt}")

    ns = {
        'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
        'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
        'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
    }

    linhas_md = []

    def get_text(node):
        return "".join(node.itertext()).strip()

    def process_container(container):
        for elem in container:
            tag = elem.tag.split('}')[-1]

            if tag in ('h', 'heading'):
                nivel = elem.attrib.get(f"{{{ns['text']}}}outline-level", "2")
                prefixo = "#" * min(int(nivel), 6)
                txt = get_text(elem)
                if txt:
                    linhas_md.append(f"\n{prefixo} {txt}\n")

            elif tag == 'p':
                txt = get_text(elem)
                if txt:
                    linhas_md.append(f"{txt}\n")

            elif tag == 'list':
                for item in elem.findall(f".//{{{ns['text']}}}list-item"):
                    txt = get_text(item)
                    if txt:
                        linhas_md.append(f"- {txt}")
                linhas_md.append("")

            elif tag == 'table':
                # Processar tabela
                for row in elem.findall(f".//{{{ns['table']}}}table-row"):
                    cells = [get_text(c) for c in row.findall(f".//{{{ns['table']}}}table-cell")]
                    if any(cells):
                        linhas_md.append("| " + " | ".join(cells) + " |")
                linhas_md.append("")

            elif tag == 'section':
                process_container(elem)

    with zipfile.ZipFile(caminho_odt, 'r') as z:
        with z.open('content.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            text_body = root.find(f".//{{{ns['office']}}}text")
            if text_body is not None:
                process_container(text_body)

    conteudo_formatado = "\n".join(linhas_md)

    if caminho_saida_md:
        with open(caminho_saida_md, "w", encoding="utf-8") as out:
            out.write(conteudo_formatado)
        print(f"Dados extraídos com sucesso para: {caminho_saida_md}")

    return conteudo_formatado

if __name__ == "__main__":
    arquivo_odt = sys.argv[1] if len(sys.argv) > 1 else "dados-sistema-E-sus.odt"
    arquivo_md = sys.argv[2] if len(sys.argv) > 2 else "dados-sistema-E-sus.md"
    extrair_odt_para_markdown(arquivo_odt, arquivo_md)
