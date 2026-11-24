"""
RentSmart - Sistema de Orçamento de Locação da R.M Imóveis.

Recebe as características da locação, aplica as regras comerciais da
imobiliária, exibe um orçamento detalhado e gera um arquivo CSV com a
projeção dos 12 primeiros meses de contrato.

Estrutura de classes:
    Imovel (abstrata)
     ├── ImovelResidencial (abstrata: quartos + garagem)
     │    ├── Apartamento   (desconto de 5% para quem não tem crianças)
     │    └── Casa
     └── Estudio            (regra própria de estacionamento)
    TaxaContratual          (taxa de R$ 2.000,00 em até 5 parcelas)
    Orcamento               (junta imóvel + taxa e gera a projeção)

Execução:  python rentsmart.py
"""

import csv
from abc import ABC, abstractmethod

ARQUIVO_CSV = "projecao_12_meses.csv"
MESES_PROJECAO = 12


# ---------------------------------------------------------------------------
# Utilitários de formatação
# ---------------------------------------------------------------------------
def formatar_moeda(valor):
    """Formata um número como moeda brasileira. Ex.: 1140 -> 'R$ 1.140,00'."""
    texto = f"{abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    sinal = "-" if valor < 0 else ""
    return f"{sinal}R$ {texto}"


def formatar_decimal_csv(valor):
    """Formata número com vírgula decimal, para abrir corretamente no Excel BR."""
    return f"{valor:.2f}".replace(".", ",")


# ---------------------------------------------------------------------------
# Modelo de domínio: imóveis
# ---------------------------------------------------------------------------
class Imovel(ABC):
    """Classe base de todo imóvel.

    Define o "esqueleto" do cálculo do aluguel (padrão Template Method):
    aluguel-base -> adicionais -> descontos. Cada subclasse preenche apenas
    as partes que são diferentes, sem repetir o restante.
    """

    NOME = "Imóvel"
    VALOR_BASE = 0.0

    @abstractmethod
    def _adicionais(self):
        """Retorna a lista de (descrição, valor) dos acréscimos do imóvel."""

    @abstractmethod
    def descricao(self):
        """Texto curto que resume as escolhas feitas pelo cliente."""

    def _descontos(self, subtotal):
        """Descontos aplicáveis. Por padrão, nenhum."""
        return []

    def detalhar(self):
        """Lista (descrição, valor) com cada componente do aluguel mensal."""
        itens = [(f"Aluguel-base ({self.NOME})", self.VALOR_BASE)]
        itens += self._adicionais()
        subtotal = sum(valor for _, valor in itens)
        itens += self._descontos(subtotal)
        return itens

    def calcular_aluguel(self):
        """Valor mensal final do aluguel."""
        return round(sum(valor for _, valor in self.detalhar()), 2)


class ImovelResidencial(Imovel):
    """Imóvel com opção de 1 ou 2 quartos e vaga de garagem (casa/apartamento)."""

    ADICIONAL_2_QUARTOS = 0.0
    VAGA_GARAGEM = 300.00

    def __init__(self, quartos, garagem):
        self.quartos = quartos
        self.garagem = garagem

    def _adicionais(self):
        itens = []
        if self.quartos == 2:
            itens.append(("Adicional de 2 quartos", self.ADICIONAL_2_QUARTOS))
        if self.garagem:
            itens.append(("Vaga de garagem", self.VAGA_GARAGEM))
        return itens

    def descricao(self):
        quartos = "2 quartos" if self.quartos == 2 else "1 quarto"
        garagem = "com garagem" if self.garagem else "sem garagem"
        return f"{self.NOME} de {quartos}, {garagem}"


class Apartamento(ImovelResidencial):
    """Apartamento: 5% de desconto para clientes sem crianças."""

    NOME = "Apartamento"
    VALOR_BASE = 700.00
    ADICIONAL_2_QUARTOS = 200.00
    DESCONTO_SEM_CRIANCAS = 0.05

    def __init__(self, quartos, garagem, tem_criancas):
        super().__init__(quartos, garagem)
        self.tem_criancas = tem_criancas

    def _descontos(self, subtotal):
        # O desconto incide sobre o aluguel já com os adicionais (e só sobre ele).
        if not self.tem_criancas:
            desconto = round(subtotal * self.DESCONTO_SEM_CRIANCAS, 2)
            return [("Desconto de 5% (sem crianças)", -desconto)]
        return []

    def descricao(self):
        criancas = "com crianças" if self.tem_criancas else "sem crianças"
        return f"{super().descricao()}, {criancas}"


class Casa(ImovelResidencial):
    """Casa: adicional de R$ 250,00 para 2 quartos."""

    NOME = "Casa"
    VALOR_BASE = 900.00
    ADICIONAL_2_QUARTOS = 250.00


class Estudio(Imovel):
    """Estúdio: estacionamento em pacote de 2 vagas + vagas adicionais."""

    NOME = "Estúdio"
    VALOR_BASE = 1200.00
    PACOTE_VAGAS = 2
    VALOR_PACOTE = 250.00
    VALOR_VAGA_ADICIONAL = 60.00

    def __init__(self, vagas=0):
        # vagas = 0 significa que o cliente não quer estacionamento.
        self.vagas = vagas

    def _adicionais(self):
        itens = []
        if self.vagas >= self.PACOTE_VAGAS:
            itens.append((f"Pacote de {self.PACOTE_VAGAS} vagas de estacionamento",
                          self.VALOR_PACOTE))
            extras = self.vagas - self.PACOTE_VAGAS
            if extras > 0:
                itens.append((
                    f"{extras} vaga(s) adicional(is) x {formatar_moeda(self.VALOR_VAGA_ADICIONAL)}",
                    extras * self.VALOR_VAGA_ADICIONAL))
        return itens

    def descricao(self):
        if self.vagas:
            return f"{self.NOME} com {self.vagas} vagas de estacionamento"
        return f"{self.NOME} sem estacionamento"


# ---------------------------------------------------------------------------
# Modelo de domínio: taxa contratual e orçamento
# ---------------------------------------------------------------------------
class TaxaContratual:
    """Taxa de contrato de R$ 2.000,00, parcelável em até 5 vezes."""

    VALOR = 2000.00
    MAX_PARCELAS = 5

    def __init__(self, parcelas):
        if not 1 <= parcelas <= self.MAX_PARCELAS:
            raise ValueError(f"A taxa pode ser parcelada de 1 a {self.MAX_PARCELAS} vezes.")
        self.parcelas = parcelas

    def valores_parcelas(self):
        """Lista com o valor de cada parcela.

        Quando a divisão não é exata (ex.: 3 parcelas), a última parcela
        absorve a diferença de centavos para que a soma seja exatamente R$ 2.000,00.
        """
        valor = round(self.VALOR / self.parcelas, 2)
        lista = [valor] * self.parcelas
        lista[-1] = round(self.VALOR - valor * (self.parcelas - 1), 2)
        return lista

    def descricao_parcelamento(self):
        valores = self.valores_parcelas()
        if self.parcelas == 1:
            return f"À vista: {formatar_moeda(valores[0])} no mês 1"
        texto = f"{self.parcelas}x de {formatar_moeda(valores[0])}"
        if valores[-1] != valores[0]:
            texto += f" (última parcela de {formatar_moeda(valores[-1])})"
        return f"{texto}, nos meses 1 a {self.parcelas}"


class Orcamento:
    """Reúne imóvel e taxa contratual; gera resumo e projeção de 12 meses."""

    def __init__(self, imovel, taxa):
        self.imovel = imovel
        self.taxa = taxa

    def projecao(self):
        """Lista de dicionários, um por mês, com aluguel, taxa e total."""
        aluguel = self.imovel.calcular_aluguel()
        parcelas = self.taxa.valores_parcelas()
        linhas, acumulado = [], 0.0
        for mes in range(1, MESES_PROJECAO + 1):
            parcela = parcelas[mes - 1] if mes <= len(parcelas) else 0.0
            total = round(aluguel + parcela, 2)
            acumulado = round(acumulado + total, 2)
            linhas.append({
                "mes": mes,
                "aluguel": aluguel,
                "parcela_taxa": parcela,
                "total_mes": total,
                "total_acumulado": acumulado,
            })
        return linhas

    def total_primeiro_ano(self):
        return self.projecao()[-1]["total_acumulado"]

    def exibir_resumo(self):
        largura = 58
        aluguel = self.imovel.calcular_aluguel()
        print("\n" + "=" * largura)
        print("RENTSMART - ORÇAMENTO DE LOCAÇÃO".center(largura))
        print("R.M Imóveis".center(largura))
        print("=" * largura)
        print(f"Imóvel: {self.imovel.descricao()}")

        print("\nCOMPOSIÇÃO DO ALUGUEL MENSAL")
        print("-" * largura)
        for descricao, valor in self.imovel.detalhar():
            print(f"  {descricao:<38}{formatar_moeda(valor):>18}")
        print("-" * largura)
        print(f"  {'ALUGUEL MENSAL':<38}{formatar_moeda(aluguel):>18}")

        print("\nTAXA CONTRATUAL (cobrada à parte do aluguel)")
        print("-" * largura)
        print(f"  Valor total: {formatar_moeda(self.taxa.VALOR)}")
        print(f"  Parcelamento: {self.taxa.descricao_parcelamento()}")

        total_aluguel = round(aluguel * MESES_PROJECAO, 2)
        print("\nRESUMO DO PRIMEIRO ANO (12 meses)")
        print("-" * largura)
        print(f"  {'Aluguel (12 meses)':<38}{formatar_moeda(total_aluguel):>18}")
        print(f"  {'Taxa contratual':<38}{formatar_moeda(self.taxa.VALOR):>18}")
        print(f"  {'TOTAL DO PRIMEIRO ANO':<38}{formatar_moeda(self.total_primeiro_ano()):>18}")
        print("=" * largura)


# ---------------------------------------------------------------------------
# Geração do CSV
# ---------------------------------------------------------------------------
def gerar_csv(projecao, caminho=ARQUIVO_CSV):
    """Grava a projeção em CSV (separador ';' e vírgula decimal, para o Excel BR)."""
    cabecalho = ["Mês", "Aluguel", "Parcela da taxa contratual",
                 "Total do mês", "Total acumulado"]
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(cabecalho)
        for linha in projecao:
            escritor.writerow([
                linha["mes"],
                formatar_decimal_csv(linha["aluguel"]),
                formatar_decimal_csv(linha["parcela_taxa"]),
                formatar_decimal_csv(linha["total_mes"]),
                formatar_decimal_csv(linha["total_acumulado"]),
            ])
    return caminho


# ---------------------------------------------------------------------------
# Entrada de dados com validação
# ---------------------------------------------------------------------------
def ler_opcao(mensagem, opcoes):
    """Repete a pergunta até o usuário digitar uma das opções válidas.

    `opcoes` é um dicionário {texto_digitado: valor_retornado}.
    """
    while True:
        resposta = input(mensagem).strip().lower()
        if resposta in opcoes:
            return opcoes[resposta]
        print(f"  Opção inválida. Digite uma destas: {', '.join(opcoes)}.")


def ler_sim_nao(mensagem):
    return ler_opcao(f"{mensagem} (s/n): ", {"s": True, "n": False})


def ler_inteiro(mensagem, minimo, maximo=None):
    """Lê um número inteiro dentro do intervalo permitido."""
    while True:
        try:
            valor = int(input(mensagem).strip())
        except ValueError:
            print("  Entrada inválida. Digite um número inteiro.")
            continue
        if valor < minimo or (maximo is not None and valor > maximo):
            limite = f"entre {minimo} e {maximo}" if maximo is not None else f"maior ou igual a {minimo}"
            print(f"  Valor fora do permitido. Digite um número {limite}.")
            continue
        return valor


def coletar_imovel():
    """Pergunta ao usuário as características e devolve o objeto de imóvel correto."""
    print("Tipos de imóvel:")
    print("  1 - Apartamento (a partir de R$ 700,00)")
    print("  2 - Casa        (a partir de R$ 900,00)")
    print("  3 - Estúdio     (R$ 1.200,00)")
    tipo = ler_opcao("Escolha o tipo de imóvel (1/2/3): ", {"1": "apartamento", "2": "casa", "3": "estudio"})

    if tipo == "estudio":
        if ler_sim_nao("Deseja estacionamento?"):
            print("  O pacote inicial inclui 2 vagas; vagas adicionais custam R$ 60,00 cada.")
            vagas = ler_inteiro("  Quantas vagas no total? (mínimo 2): ", minimo=2)
        else:
            vagas = 0
        return Estudio(vagas)

    quartos = ler_opcao("Quantidade de quartos (1/2): ", {"1": 1, "2": 2})
    garagem = ler_sim_nao("Deseja vaga de garagem?")
    if tipo == "casa":
        return Casa(quartos, garagem)
    tem_criancas = ler_sim_nao("Há crianças que irão morar no imóvel?")
    return Apartamento(quartos, garagem, tem_criancas)


def coletar_taxa():
    print(f"\nTaxa contratual: {formatar_moeda(TaxaContratual.VALOR)}, "
          f"em até {TaxaContratual.MAX_PARCELAS} parcelas.")
    parcelas = ler_inteiro(f"Em quantas parcelas deseja pagar? (1 a {TaxaContratual.MAX_PARCELAS}): ",
                           minimo=1, maximo=TaxaContratual.MAX_PARCELAS)
    return TaxaContratual(parcelas)


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main():
    print("=" * 58)
    print("RENTSMART - R.M Imóveis".center(58))
    print("=" * 58)
    imovel = coletar_imovel()
    taxa = coletar_taxa()

    orcamento = Orcamento(imovel, taxa)
    orcamento.exibir_resumo()

    caminho = gerar_csv(orcamento.projecao())
    print(f"\nProjeção dos 12 meses gravada em: {caminho}")


if __name__ == "__main__":
    main()
