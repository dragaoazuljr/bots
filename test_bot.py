import unittest
import os
import json
import tempfile
from datetime import datetime
from unittest.mock import patch, mock_open
import sys

# Adiciona o diretório atual ao path para importar o bot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importa funções do bot (assumindo que serão extraídas para um módulo separado)
# Por enquanto, vamos simular as funções aqui

# Configurações globais para teste
taxa_transacao = 0.002
last_price = 654139.18

def mock_get_bitcoin_price():
    """Versão mockada para testes."""
    global last_price
    variation = 0.01  # Variação fixa para teste
    new_price = last_price * (1 + variation / 100)
    last_price = new_price
    return new_price

def mock_buy_bitcoin(montante, preco_compra, timestamp, dobrar_aposta, stop_loss_atual, meta_lucro_atual, max_duration_atual):
    """Versão mockada para testes."""
    try:
        if montante <= 0:
            raise ValueError("Montante deve ser positivo")
        if preco_compra <= 0:
            raise ValueError("Preço de compra deve ser positivo")

        taxa = montante * taxa_transacao
        btc_comprado = (montante - taxa) / preco_compra
        return btc_comprado, taxa
    except Exception as e:
        print(f"Erro na compra de Bitcoin: {e}")
        return 0, 0

def mock_sell_bitcoin(btc_total, preco_venda, timestamp, motivo):
    """Versão mockada para testes."""
    try:
        if btc_total <= 0:
            raise ValueError("Quantidade de BTC deve ser positiva")
        if preco_venda <= 0:
            raise ValueError("Preço de venda deve ser positivo")

        valor_venda = btc_total * preco_venda
        taxa = valor_venda * taxa_transacao
        return valor_venda, taxa
    except Exception as e:
        print(f"Erro na venda de Bitcoin: {e}")
        return 0, 0

def load_bot_state():
    """Versão mockada para testes."""
    try:
        if os.path.exists('test_bot_state.json'):
            with open('test_bot_state.json', 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Erro ao carregar estado: {e}")
        return None

def save_bot_state(state):
    """Versão mockada para testes."""
    try:
        with open('test_bot_state.json', 'w') as f:
            json.dump(state, f, indent=2, default=str)
    except Exception as e:
        print(f"Erro ao salvar estado: {e}")

class TestBotFunctions(unittest.TestCase):

    def setUp(self):
        """Configuração inicial para cada teste."""
        global last_price
        last_price = 654139.18
        # Remove arquivo de estado de teste se existir
        if os.path.exists('test_bot_state.json'):
            os.remove('test_bot_state.json')

    def tearDown(self):
        """Limpeza após cada teste."""
        if os.path.exists('test_bot_state.json'):
            os.remove('test_bot_state.json')

    def test_mock_get_bitcoin_price_valid(self):
        """Testa geração de preço válido."""
        price = mock_get_bitcoin_price()
        self.assertGreater(price, 0)
        self.assertIsInstance(price, float)

    def test_mock_buy_bitcoin_valid(self):
        """Testa compra válida de Bitcoin."""
        montante = 10000
        preco = 650000
        timestamp = datetime.now()

        btc_comprado, taxa = mock_buy_bitcoin(montante, preco, timestamp, False, -0.05, 0.1, 86400)

        self.assertGreater(btc_comprado, 0)
        self.assertGreater(taxa, 0)
        expected_btc = (montante - taxa) / preco
        self.assertAlmostEqual(btc_comprado, expected_btc, places=5)

    def test_mock_buy_bitcoin_invalid_montante(self):
        """Testa compra com montante inválido."""
        btc_comprado, taxa = mock_buy_bitcoin(-1000, 650000, datetime.now(), False, -0.05, 0.1, 86400)
        self.assertEqual(btc_comprado, 0)
        self.assertEqual(taxa, 0)

    def test_mock_buy_bitcoin_invalid_price(self):
        """Testa compra com preço inválido."""
        btc_comprado, taxa = mock_buy_bitcoin(10000, -650000, datetime.now(), False, -0.05, 0.1, 86400)
        self.assertEqual(btc_comprado, 0)
        self.assertEqual(taxa, 0)

    def test_mock_sell_bitcoin_valid(self):
        """Testa venda válida de Bitcoin."""
        btc_total = 0.015
        preco = 650000
        timestamp = datetime.now()

        valor_venda, taxa = mock_sell_bitcoin(btc_total, preco, timestamp, "Teste")

        self.assertGreater(valor_venda, 0)
        self.assertGreater(taxa, 0)
        expected_valor = btc_total * preco
        self.assertAlmostEqual(valor_venda, expected_valor, places=2)

    def test_mock_sell_bitcoin_invalid_btc(self):
        """Testa venda com quantidade inválida de BTC."""
        valor_venda, taxa = mock_sell_bitcoin(-0.015, 650000, datetime.now(), "Teste")
        self.assertEqual(valor_venda, 0)
        self.assertEqual(taxa, 0)

    def test_mock_sell_bitcoin_invalid_price(self):
        """Testa venda com preço inválido."""
        valor_venda, taxa = mock_sell_bitcoin(0.015, -650000, datetime.now(), "Teste")
        self.assertEqual(valor_venda, 0)
        self.assertEqual(taxa, 0)

    def test_load_bot_state_no_file(self):
        """Testa carregamento de estado quando arquivo não existe."""
        state = load_bot_state()
        self.assertIsNone(state)

    def test_save_and_load_bot_state(self):
        """Testa salvar e carregar estado."""
        test_state = {
            'montante': 15000,
            'btc_total': 0.02,
            'total_lucro': 5000
        }

        # Salva estado
        save_bot_state(test_state)

        # Carrega estado
        loaded_state = load_bot_state()

        self.assertIsNotNone(loaded_state)
        self.assertEqual(loaded_state['montante'], 15000)
        self.assertEqual(loaded_state['btc_total'], 0.02)
        self.assertEqual(loaded_state['total_lucro'], 5000)

    def test_calcular_imposto(self):
        """Testa cálculo de imposto."""
        # Testa venda > 35k com lucro > 0
        valor_venda = 40000
        custo = 35000
        lucro = valor_venda - custo
        imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0

        self.assertGreater(imposto, 0)
        self.assertAlmostEqual(imposto, 750, places=2)  # 5000 * 0.15

        # Testa venda < 35k (sem imposto)
        valor_venda = 30000
        custo = 25000
        lucro = valor_venda - custo
        imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0

        self.assertEqual(imposto, 0)

        # Testa venda > 35k com prejuízo (sem imposto)
        valor_venda = 40000
        custo = 45000
        lucro = valor_venda - custo
        imposto = lucro * 0.15 if valor_venda > 35000 and lucro > 0 else 0.0

        self.assertEqual(imposto, 0)

if __name__ == '__main__':
    unittest.main()