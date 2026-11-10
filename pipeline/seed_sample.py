"""Gera dados de amostra representativos para teste rápido local caso raw/ esteja vazio."""

from pathlib import Path
import random
from datetime import datetime, timedelta
import pandas as pd

RAW_DIR = Path("raw")


def gerar_amostra(num_pedidos: int = 500) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    ufs = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "PE", "CE", "DF", "GO", "PB"]
    ufs_pesos = [0.4, 0.15, 0.12, 0.06, 0.05, 0.04, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
    
    # 1. Clientes
    clientes = []
    for i in range(1, num_pedidos + 1):
        uf = random.choices(ufs, weights=ufs_pesos)[0]
        clientes.append({
            "cliente_id": f"c_{i:04d}",
            "cliente_unico_id": f"u_{i % 400:04d}",
            "cep": f"{random.randint(10000, 99999):05d}",
            "cidade": f"Cidade {uf}",
            "uf": uf,
        })
    pd.DataFrame(clientes).to_csv(RAW_DIR / "clientes.csv", index=False)
    
    # 2. Vendedores
    vendedores = []
    for i in range(1, 40):
        uf = random.choice(["SP", "RJ", "MG", "PR", "SC", "RS"])
        vendedores.append({
            "vendedor_id": f"v_{i:03d}",
            "cep": f"{random.randint(10000, 99999):05d}",
            "cidade": f"Polo {uf}",
            "uf": uf,
        })
    pd.DataFrame(vendedores).to_csv(RAW_DIR / "vendedores.csv", index=False)

    # 3. Pedidos, Itens, Avaliações e Pagamentos
    pedidos = []
    itens = []
    avaliacoes = []
    pagamentos = []

    base_date = datetime(2017, 1, 1)

    for i in range(1, num_pedidos + 1):
        p_id = f"ped_{i:04d}"
        c_id = f"c_{i:04d}"
        
        # Data aleatória entre jan/2017 e ago/2018
        dias_offset = random.randint(0, 580)
        dt_compra = base_date + timedelta(days=dias_offset, hours=random.randint(8, 20))
        dt_aprov = dt_compra + timedelta(hours=random.randint(1, 24))
        
        status = random.choices(["delivered", "shipped", "canceled"], weights=[0.94, 0.04, 0.02])[0]
        
        dias_previsto = random.randint(10, 25)
        dt_prevista = (dt_compra + timedelta(days=dias_previsto)).date()
        
        if status == "delivered":
            # 88% no prazo, 12% atrasado
            if random.random() < 0.88:
                dias_real = random.randint(3, dias_previsto)
            else:
                dias_real = dias_previsto + random.randint(1, 10)
                
            dt_despacho = dt_aprov + timedelta(days=random.randint(1, 4))
            dt_entrega = dt_compra + timedelta(days=dias_real)
        else:
            dt_despacho = None
            dt_entrega = None

        pedidos.append({
            "pedido_id": p_id,
            "cliente_id": c_id,
            "status": status,
            "data_compra": dt_compra.strftime("%Y-%m-%d %H:%M:%S"),
            "data_aprovacao": dt_aprov.strftime("%Y-%m-%d %H:%M:%S"),
            "data_envio_transportadora": dt_despacho.strftime("%Y-%m-%d %H:%M:%S") if dt_despacho else "",
            "data_entrega": dt_entrega.strftime("%Y-%m-%d %H:%M:%S") if dt_entrega else "",
            "data_entrega_prevista": dt_prevista.strftime("%Y-%m-%d"),
        })

        # Itens
        qtd_itens = random.choices([1, 2, 3], weights=[0.85, 0.12, 0.03])[0]
        preco_total = 0.0
        frete_total = 0.0
        for item_idx in range(1, qtd_itens + 1):
            v_id = f"v_{random.randint(1, 35):03d}"
            preco = round(random.uniform(25.0, 350.0), 2)
            frete = round(random.uniform(12.0, 45.0), 2)
            preco_total += preco
            frete_total += frete
            itens.append({
                "pedido_id": p_id,
                "item_id": item_idx,
                "produto_id": f"prod_{random.randint(1, 80):03d}",
                "vendedor_id": v_id,
                "data_envio_limite": (dt_compra + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),
                "preco": f"{preco:.2f}",
                "frete": f"{frete:.2f}",
            })

        # Pagamentos
        pagamentos.append({
            "pedido_id": p_id,
            "sequencia": 1,
            "tipo": random.choices(["credit_card", "boleto", "voucher"], weights=[0.75, 0.2, 0.05])[0],
            "parcelas": random.choice([1, 2, 3, 6, 10]),
            "valor": f"{preco_total + frete_total:.2f}",
        })

        # Avaliação
        if status == "delivered":
            if dt_entrega.date() <= dt_prevista:
                nota = random.choices([5, 4, 3, 2, 1], weights=[0.65, 0.22, 0.08, 0.03, 0.02])[0]
            else:
                nota = random.choices([1, 2, 3, 4, 5], weights=[0.55, 0.25, 0.12, 0.05, 0.03])[0]
            avaliacoes.append({
                "avaliacao_id": f"rev_{i:04d}",
                "pedido_id": p_id,
                "nota": nota,
                "mensagem": "Entrega pontual e produto excelente!" if nota >= 4 else "Demorou muito para chegar.",
                "data_criacao": (dt_entrega + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "data_resposta": (dt_entrega + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            })

    pd.DataFrame(pedidos).to_csv(RAW_DIR / "pedidos.csv", index=False)
    pd.DataFrame(itens).to_csv(RAW_DIR / "itens_pedido.csv", index=False)
    pd.DataFrame(avaliacoes).to_csv(RAW_DIR / "avaliacoes.csv", index=False)
    pd.DataFrame(pagamentos).to_csv(RAW_DIR / "pagamentos.csv", index=False)
    print(f"✓ Amostra de {num_pedidos} pedidos gerada com sucesso em {RAW_DIR}")


if __name__ == "__main__":
    gerar_amostra()
