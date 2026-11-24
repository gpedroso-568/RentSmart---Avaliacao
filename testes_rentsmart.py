"""Testes das regras de negócio do RentSmart. Execução: python -m unittest -v"""

import csv
import os
import tempfile
import unittest

from rentsmart import (Apartamento, Casa, Estudio, Orcamento, TaxaContratual,
                       gerar_csv)


class TestAluguel(unittest.TestCase):
    def test_apartamento_1_quarto_com_criancas(self):
        self.assertEqual(Apartamento(1, False, True).calcular_aluguel(), 700.00)

    def test_apartamento_1_quarto_sem_criancas_tem_desconto(self):
        self.assertEqual(Apartamento(1, False, False).calcular_aluguel(), 665.00)

    def test_apartamento_2_quartos_garagem_sem_criancas(self):
        # (700 + 200 + 300) * 0,95 = 1.140
        self.assertEqual(Apartamento(2, True, False).calcular_aluguel(), 1140.00)

    def test_apartamento_2_quartos_garagem_com_criancas(self):
        self.assertEqual(Apartamento(2, True, True).calcular_aluguel(), 1200.00)

    def test_casa_1_quarto(self):
        self.assertEqual(Casa(1, False).calcular_aluguel(), 900.00)

    def test_casa_2_quartos_com_garagem_nao_tem_desconto(self):
        self.assertEqual(Casa(2, True).calcular_aluguel(), 1450.00)

    def test_estudio_sem_estacionamento(self):
        self.assertEqual(Estudio(0).calcular_aluguel(), 1200.00)

    def test_estudio_pacote_de_2_vagas(self):
        self.assertEqual(Estudio(2).calcular_aluguel(), 1450.00)

    def test_estudio_com_vagas_adicionais(self):
        # 1200 + 250 + 2 * 60
        self.assertEqual(Estudio(4).calcular_aluguel(), 1570.00)


class TestTaxa(unittest.TestCase):
    def test_parcelas_exatas(self):
        self.assertEqual(TaxaContratual(5).valores_parcelas(), [400.0] * 5)

    def test_soma_das_parcelas_sempre_2000(self):
        for n in range(1, 6):
            self.assertAlmostEqual(sum(TaxaContratual(n).valores_parcelas()), 2000.00, places=2)

    def test_parcelas_invalidas(self):
        for n in (0, 6, -1):
            with self.assertRaises(ValueError):
                TaxaContratual(n)


class TestProjecao(unittest.TestCase):
    def setUp(self):
        self.orcamento = Orcamento(Apartamento(2, True, False), TaxaContratual(5))

    def test_projecao_tem_12_meses(self):
        self.assertEqual(len(self.orcamento.projecao()), 12)

    def test_taxa_apenas_nos_meses_parcelados(self):
        proj = self.orcamento.projecao()
        self.assertEqual(proj[0]["total_mes"], 1540.00)
        self.assertEqual(proj[4]["total_mes"], 1540.00)
        self.assertEqual(proj[5]["total_mes"], 1140.00)

    def test_total_primeiro_ano(self):
        # 1140 * 12 + 2000
        self.assertEqual(self.orcamento.total_primeiro_ano(), 15680.00)

    def test_csv_gerado(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = gerar_csv(self.orcamento.projecao(), os.path.join(pasta, "t.csv"))
            with open(caminho, encoding="utf-8-sig", newline="") as f:
                linhas = list(csv.reader(f, delimiter=";"))
        self.assertEqual(len(linhas), 13)  # cabeçalho + 12 meses
        self.assertEqual(linhas[1][3], "1540,00")


if __name__ == "__main__":
    unittest.main()
