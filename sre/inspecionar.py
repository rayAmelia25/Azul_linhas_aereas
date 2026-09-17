import pandas as pd
from pathlib import Path

caminho = Path("data/original/Azul Fundamentos e Planilha 2T26.xlsx")

if not caminho.exists():
    print("Planilha não encontrada")
    exit()

excel = pd.ExcelFile(caminho)

print("Abas encontradas na planilha:")

for aba in excel.sheet_names:  # mostra as abas existentes no excel
    print(f" - {aba}")

print("\n" + "=" * 50)


df = pd.read_excel(
    caminho,
    sheet_name="DRE | Income Statement",
    header=None
)

print(f"Quantidade de linhas: {df.shape[0]}")
print(f"Quantidade de colunas: {df.shape[1]}")

# Mostra apenas a posição das células preenchidas,
# sem imprimir valores financeiros
preenchidas = df.notna().sum()

print("\nQuantidade de células preenchidas por coluna:")
print(preenchidas.to_string())

print("\n✅ Inspeção concluída.")

