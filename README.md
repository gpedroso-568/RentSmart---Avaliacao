# RentSmart — Sistema de Orçamento de Locação (R.M Imóveis)

Aplicação em Python, orientada a objetos, que automatiza o orçamento de locação da R.M Imóveis: coleta as características do imóvel, valida as entradas, aplica as regras comerciais, exibe um orçamento detalhado e gera um arquivo CSV com a projeção dos 12 primeiros meses de contrato.

Projeto da disciplina **Algorithmic Thinking & Introduction to Object-Oriented Programming**.

## Requisitos

- Python 3.8 ou superior
- Nenhuma biblioteca externa (usa apenas a biblioteca padrão: `csv` e `abc`)

## Como executar

```bash
# 1. Clone o repositório (ou baixe os arquivos)
git clone <URL-DO-SEU-REPOSITORIO>
cd rentsmart

# 2. Execute o programa
python rentsmart.py          # no Windows, também pode ser: py rentsmart.py
```

O programa faz as perguntas no terminal, mostra o orçamento e grava o arquivo **`projecao_12_meses.csv`** na pasta onde foi executado. O CSV usa `;` como separador e vírgula decimal, então abre direto no Excel em português.

### Executar os testes automatizados

```bash
python -m unittest -v
```

## Regras de negócio implementadas

| Item | Regra |
|---|---|
| Aluguel-base | Apartamento (1 quarto) R$ 700,00 · Casa (1 quarto) R$ 900,00 · Estúdio R$ 1.200,00 |
| 2 quartos | Apartamento + R$ 200,00 · Casa + R$ 250,00 |
| Garagem (casa/apto) | + R$ 300,00 (1 vaga) |
| Estacionamento (estúdio) | Pacote de 2 vagas R$ 250,00 + R$ 60,00 por vaga adicional |
| Desconto | 5% **somente em apartamento sem crianças**, aplicado após os adicionais |
| Taxa contratual | R$ 2.000,00 em 1 a 5 parcelas, exibida separadamente do aluguel |
| Projeção | 12 meses: aluguel + parcela da taxa (quando houver) |

### Premissas adotadas (pontos que o enunciado deixa em aberto)

1. **Estúdio — estacionamento é opcional.** O cliente escolhe se quer vagas; se quiser, informa o total (mínimo 2): paga R$ 250,00 pelo pacote de 2 vagas e R$ 60,00 por cada vaga acima disso.
2. **Estúdio não tem opção de 1 ou 2 quartos**, pois o enunciado só define adicional de quartos para casas e apartamentos.
3. **O desconto de 5% incide apenas sobre o aluguel mensal** (já com adicionais e garagem), nunca sobre a taxa contratual.
4. **As parcelas da taxa começam no mês 1** e seguem em meses consecutivos.
5. **Divisão não exata:** quando 2.000 não divide por igual (ex.: 3 parcelas), a última parcela absorve a diferença de centavos, para que a soma seja exatamente R$ 2.000,00.

## Exemplo de uso

Apartamento de 2 quartos, com garagem, sem crianças, taxa em 5 parcelas:

```
COMPOSIÇÃO DO ALUGUEL MENSAL
----------------------------------------------------------
  Aluguel-base (Apartamento)                     R$ 700,00
  Adicional de 2 quartos                         R$ 200,00
  Vaga de garagem                                R$ 300,00
  Desconto de 5% (sem crianças)                  -R$ 60,00
----------------------------------------------------------
  ALUGUEL MENSAL                               R$ 1.140,00

TAXA CONTRATUAL (cobrada à parte do aluguel)
  Valor total: R$ 2.000,00
  Parcelamento: 5x de R$ 400,00, nos meses 1 a 5
```

Um exemplo completo do CSV gerado está em [`exemplo_projecao_12_meses.csv`](exemplo_projecao_12_meses.csv).

## Estrutura do projeto

```
rentsmart/
├── rentsmart.py                    # código-fonte da aplicação
├── testes_rentsmart.py             # testes automatizados das regras
├── exemplo_projecao_12_meses.csv   # exemplo de arquivo gerado
├── README.md
└── docs/
    ├── fluxograma.png
    └── diagrama_classes.png
```

## Estrutura de classes

```
Imovel (abstrata)
 ├── ImovelResidencial (abstrata: quartos + garagem)
 │    ├── Apartamento   → desconto de 5% sem crianças
 │    └── Casa
 └── Estudio            → regra própria de estacionamento
TaxaContratual          → R$ 2.000,00 em até 5 parcelas
Orcamento               → junta imóvel + taxa; gera resumo e projeção
```

- **Herança e polimorfismo:** `Orcamento` só chama `imovel.calcular_aluguel()`; cada tipo de imóvel aplica sua própria regra.
- **Template Method:** `Imovel.detalhar()` define a ordem *base → adicionais → descontos*; as subclasses implementam apenas o que muda.
- **Sem repetição:** casa e apartamento compartilham quartos e garagem em `ImovelResidencial`; os valores ficam em constantes de classe.
- **Separação de responsabilidades:** as classes de domínio não leem dados do usuário; leitura e validação ficam nas funções `ler_*` e `coletar_*`, e a gravação do CSV em `gerar_csv`.
