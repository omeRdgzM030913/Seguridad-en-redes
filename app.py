"""
Interfaz web para interactuar con el simulador de blockchain.

"""

import streamlit as st
import pandas as pd

from blockchain import (
    Blockchain,
    DIFFICULTY,
    MINING_REWARD,
    GENESIS_COINS,
)


st.set_page_config(
    page_title="Simulador de Blockchain",
    page_icon="⛓️🤑🪙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CSS personalizado 
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>

    .stApp {
        background-color: #0a0a0a;
        color: #00ff00;
        font-family: 'Courier New', Courier, monospace;
    }
    

    [data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 2px solid #003300;
    }


    h1, h2, h3 {
        color: #00ff00 !important;
        text-shadow: 0 0 8px rgba(0, 255, 0, 0.5);
    }

 
    div[data-testid="metric-container"] {
        background-color: #050505;
        border: 1px solid #00ff00;
        border-radius: 0px;
        padding: 15px;
        box-shadow: 0 0 10px rgba(0, 255, 0, 0.2);
    }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: #00ff00 !important;
    }

   
    .stButton > button {
        background-color: #000000;
        color: #00ff00;
        border: 1px solid #00ff00;
        border-radius: 0px;
        font-family: 'Courier New', Courier, monospace;
        text-transform: uppercase;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #00ff00;
        color: #000000;
        box-shadow: 0 0 15px #00ff00;
        border-color: #00ff00;
    }

  
    code {
        color: #00ff00 !important;
        background-color: #001a00 !important;
        border: 1px solid #004400;
    }
    
    
    .stAlert {
        background-color: #001100;
        border-left-color: #00ff00;
        color: #00ff00;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Inicialización del estado de sesión
# ─────────────────────────────────────────────────────────────
def _init_blockchain():
    """
    Crea la blockchain con bloque génesis la primera vez.
    Se usa st.session_state para persistir entre reruns de Streamlit.
    """
    if "bc" not in st.session_state:
        bc = Blockchain()
        gw = bc.create_wallet(name="Génesis (Admin)")
        bc.initialize(gw)
        st.session_state.bc = bc
        st.session_state.genesis_address = gw.address

_init_blockchain()
bc: Blockchain = st.session_state.bc

# ─────────────────────────────────────────────────────────────
# Sidebar — Navegación
# ─────────────────────────────────────────────────────────────
st.sidebar.title("⛓️🤑🪙 Simulador de Blockchain")
st.sidebar.caption("Proyecto Integrador")
st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**Configuración PoW**  \n"
    f"Dificultad: `{DIFFICULTY}` ceros  \n"
    f"Recompensa base: `{MINING_REWARD}` monedas  \n"
    f"Génesis: `{GENESIS_COINS}` monedas"
)
st.sidebar.markdown("---")

section = st.sidebar.radio(
    "Navegación",
    [
        "🏠 Inicio",
        "👤 Usuarios",
        "💸 Transacciones",
        "⛏️ Minería",
        "🔗 Blockchain",
        "💰 Balances",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info(
    " **Flujo básico:**  \n"
    "1. Crea usuarios (wallets)  \n"
    "2. Crea transacciones  \n"
    "3. Mina un bloque  \n"
    "4. Visualiza la cadena"
)

# ═════════════════════════════════════════════════════════════
# 🏠  INICIO — Resumen general
# ═════════════════════════════════════════════════════════════
if section == "🏠 Inicio":
    st.title("🏠 Resumen del Sistema")
    st.markdown(
        "Simulador completo de blockchain con **wallets ECDSA**, "
        "**modelo UTXO**, **firmas digitales** y **Prueba de Trabajo (PoW)**."
    )

    # ── Métricas principales ──────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⛓️ Bloques en la cadena", len(bc.chain))
    c2.metric("👤 Wallets registradas",  len(bc.wallets))
    c3.metric("🕒 Txs pendientes",       len(bc.pending))
    fees_pending = sum(t.fee for t in bc.pending)
    c4.metric("💸 Fees acumuladas",      f"{fees_pending:.4f}")

    st.markdown("---")

    # ── Estadísticas de minería ───────────────────────────────
    if bc.mining_times:
        avg  = sum(bc.mining_times) / len(bc.mining_times)
        best = min(bc.mining_times)
        worst = max(bc.mining_times)
        st.markdown("### ⏱️ Estadísticas de Minería")
        m1, m2, m3 = st.columns(3)
        m1.metric("Tiempo promedio", f"{avg:.2f}s")
        m2.metric("Más rápido",      f"{best:.2f}s")
        m3.metric("Más lento",       f"{worst:.2f}s")

    # ── Últimos bloques ───────────────────────────────────────
    st.markdown("### 🧱 Últimos bloques")
    rows = [
        {
            "Índice":    b.index,
            "Timestamp": b.timestamp,
            "Txs":       len(b.transactions),
            "Nonce":     b.nonce,
            "Hash (inicio)": b.hash[:28] + "...",
            "Hash previo (inicio)": b.prev_hash[:20] + "..." if b.prev_hash != "0" else "0 (génesis)",
        }
        for b in reversed(bc.chain)
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── Estado de la cadena ───────────────────────────────────
    st.markdown("---")
    valid = bc.is_valid()
    if valid:
        st.success("✅ La cadena de bloques es **válida e íntegra**. "
                   "Todos los hashes están correctamente encadenados.")
    else:
        st.error("❌ ¡La cadena de bloques está **comprometida**! "
                 "Algún bloque fue modificado después de ser minado.")


# ═════════════════════════════════════════════════════════════
# 👤  USUARIOS — Crear wallets
# ═════════════════════════════════════════════════════════════
elif section == "👤 Usuarios":
    st.title("👤 Gestión de Wallets")
    st.markdown(
        "Cada usuario tiene un par de llaves **ECDSA sobre secp256k1**.  \n"
        "Su **dirección** es el hash SHA-256 de su clave pública."
    )

    # ── Formulario de creación ────────────────────────────────
    st.markdown("### ➕ Crear nueva wallet")
    with st.form("form_create_wallet", clear_on_submit=True):
        name      = st.text_input("Nombre del usuario", placeholder="Ej. Luis, pedro, Omar…")
        submitted = st.form_submit_button("🆕 Generar Wallet")

    if submitted:
        if not name.strip():
            st.warning("⚠️ Por favor ingresa un nombre válido.")
        else:
            w = bc.create_wallet(name=name.strip())
            st.success(f"✅ Wallet creada exitosamente para **{w.name}**")

            col1, col2 = st.columns(2)
            col1.markdown("**Información de la Wallet:**")
            col1.code(
                f"Nombre       : {w.name}\n"
                f"Dirección    : {w.address}\n"
                f"Clave Pública: {w.public_key_hex}\n"
                f"Clave Privada: {w.private_key_hex}",
                language="text",
            )
            col2.markdown("**¿Cómo se calculó la dirección?**")
            col2.code(
                f"SHA-256( clave_publica_bytes ) = dirección\n\n"
                f"SHA-256({w.public_key_hex[:20]}...)\n"
                f"  = {w.address}",
                language="text",
            )

    # ── Tabla de wallets ──────────────────────────────────────
    st.markdown("### 📋 Wallets registradas")
    if bc.wallets:
        rows = [
            {
                "Nombre":           w.name or "—",
                "Dirección":        addr,
                "Clave Pública":    w.public_key_hex[:36] + "...",
                "Saldo (monedas)":  f"{bc.balance(addr):.4f}",
            }
            for addr, w in bc.wallets.items()
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay wallets. ¡Crea una arriba!")

    # ── Detalle de wallet ─────────────────────────────────────
    if bc.wallets:
        st.markdown("### 🔍 Detalle de una wallet")
        wallet_opts = {
            f"{w.name} — {addr[:16]}...": addr
            for addr, w in bc.wallets.items()
        }
        sel_label = st.selectbox("Selecciona una wallet", list(wallet_opts.keys()),
                                 key="wallet_detail")
        sel_addr  = wallet_opts[sel_label]
        sel_w     = bc.wallets[sel_addr]

        d1, d2 = st.columns(2)
        d1.markdown(f"**Nombre:** {sel_w.name}")
        d1.markdown(f"**Saldo:** {bc.balance(sel_addr):.4f} monedas")
        d1.markdown(f"**UTXOs:** {len(bc.utxo_set.for_address(sel_addr))}")
        d2.markdown("**Clave Privada (hex):**")
        d2.code(sel_w.private_key_hex, language="text")
        d2.markdown("**Dirección (SHA-256 de clave pública):**")
        d2.code(sel_addr, language="text")


# ═════════════════════════════════════════════════════════════
# 💸  TRANSACCIONES — Enviar entre usuarios
# ═════════════════════════════════════════════════════════════
elif section == "💸 Transacciones":
    st.title("💸 Transacciones")
    st.markdown(
        "Las transacciones usan el modelo **UTXO**: solo se pueden gastar "
        "salidas no utilizadas. Cada entrada lleva una **firma digital ECDSA**."
    )

    if len(bc.wallets) < 2:
        st.warning("⚠️ Necesitas al menos **2 wallets** para crear transacciones. "
                   "Ve a la sección **Usuarios** y crea más.")
        st.stop()

    # ── Selector dinámico de remitente ────────────────────────
    st.markdown("### 📤 Crear transacción")

    senders = {
        f"{w.name} — disponible: {bc.available_balance(addr):.4f} — {addr[:12]}...": addr
        for addr, w in bc.wallets.items()
        if bc.available_balance(addr) > 0
    }

    if not senders:
        st.warning("⚠️ Ninguna wallet tiene saldo disponible. "
                   "¿Tienes transacciones pendientes sin minar?  \n"
                   "Ve a **Minería** para minar el bloque actual.")
    else:
        sender_label = st.selectbox("Remitente", list(senders.keys()), key="tx_sender")
        sender_addr  = senders[sender_label]
        sender_w     = bc.wallets[sender_addr]
        avail        = bc.available_balance(sender_addr)

        st.info(f"💰 Saldo disponible de **{sender_w.name}**: **{avail:.4f}** monedas")

        recipients = {
            f"{w.name} — {addr[:12]}...": addr
            for addr, w in bc.wallets.items()
            if addr != sender_addr
        }
        recip_label = st.selectbox("Destinatario", list(recipients.keys()), key="tx_recip")
        recip_addr  = recipients[recip_label]

        col1, col2 = st.columns(2)
        amount = col1.number_input(
            "Monto a enviar",
            min_value=0.0001,
            max_value=float(avail),
            value=min(1.0, float(avail) * 0.9),
            step=0.01,
            format="%.4f",
            key="tx_amount",
        )
        max_fee = max(0.0, round(avail - amount, 8))
        fee = col2.number_input(
            "Comisión (fee) para el minero",
            min_value=0.0,
            max_value=float(max_fee),
            value=min(0.1, float(max_fee)),
            step=0.01,
            format="%.4f",
            key="tx_fee",
        )

        st.markdown(
            f"**Resumen:** "
            f"envías `{amount:.4f}` + fee `{fee:.4f}` = **`{amount+fee:.4f}`** de `{avail:.4f}` disponibles  \n"
            f"Cambio de vuelta: `{round(avail - amount - fee, 4):.4f}` monedas"
        )

        if st.button("📤 Enviar Transacción", type="primary"):
            try:
                tx = bc.build_transaction(sender_w, recip_addr, amount, fee)
                bc.submit(tx)
                st.toast(f"Transacción {tx.txid[:8]}... agregada al pool", icon="💸")
                
                st.success(f"✅ Transacción creada y agregada al pool.  \n"
                           f"**TXID:** `{tx.txid}`")
                with st.expander("📄 Ver detalle de la transacción"):
                    st.json(tx.to_dict())
            except ValueError as e:
                st.error(f"❌ Error: {e}")

    # ── Pool de pendientes ─────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🕒 Pool de transacciones pendientes")
    st.caption("Estas transacciones se incluirán en el próximo bloque minado.")

    if bc.pending:
        rows = [
            {
                "TXID":          t.txid[:24] + "...",
                "Entradas":      len(t.inputs),
                "Salidas":       len(t.outputs),
                "Fee":           f"{t.fee:.4f}",
                "Total outputs": f"{sum(o['amount'] for o in t.outputs):.4f}",
            }
            for t in bc.pending
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        total_fees = sum(t.fee for t in bc.pending)
        st.info(f"📊 {len(bc.pending)} tx(s) pendiente(s) · "
                f"Fees totales: **{total_fees:.4f}** monedas")

        with st.expander("🔎 Ver transacciones completas (JSON)"):
            for tx in bc.pending:
                st.json(tx.to_dict())
    else:
        st.info("No hay transacciones pendientes. Créalas arriba y luego mina un bloque.")


# ═════════════════════════════════════════════════════════════
# ⛏️  MINERÍA — Ejecutar PoW
# ═════════════════════════════════════════════════════════════
elif section == "⛏️ Minería":
    st.title("⛏️ Minería de Bloques")
    st.markdown(
        "**Prueba de Trabajo (PoW):** el sistema busca un `nonce` tal que el "
        f"hash SHA-256 del bloque empiece con **{DIFFICULTY} ceros** consecutivos.  \n"
        f"Al minar, el minero recibe **{MINING_REWARD} monedas** fijas + "
        "la suma de todas las comisiones de las transacciones incluidas."
    )

    if not bc.wallets:
        st.warning("⚠️ Crea al menos una wallet antes de minar.")
        st.stop()

    # ── Selector de minero ────────────────────────────────────
    st.markdown("### ⚙️ Configurar minería")
    miners = {
        f"{w.name} — {addr[:14]}...": addr
        for addr, w in bc.wallets.items()
    }
    miner_label = st.selectbox("Wallet del minero (recibirá la recompensa)",
                               list(miners.keys()))
    miner_addr  = miners[miner_label]
    miner_w     = bc.wallets[miner_addr]

    fees         = sum(t.fee for t in bc.pending)
    total_reward = round(MINING_REWARD + fees, 8)

    # ── Resumen antes de minar ────────────────────────────────
    info1, info2, info3 = st.columns(3)
    info1.metric("Txs a incluir",       len(bc.pending))
    info2.metric("Fees acumuladas",     f"{fees:.4f}")
    info3.metric("Recompensa esperada", f"{total_reward:.4f}")

    st.markdown("---")

    if st.button("⛏️ Minar Bloque Ahora", type="primary"):
      
        st.toast("Iniciando algoritmo de Prueba de Trabajo (PoW)...", icon="⏳")
      
        with st.spinner(
            f"Ejecutando Prueba de Trabajo (buscando hash con {DIFFICULTY} ceros)… "
            "Esto puede tardar unos segundos."
        ):
            try:
                blk, elapsed = bc.mine_pending(miner_w)

                st.balloons()
                st.toast("¡Bloque minado con éxito!", icon="🤑✔️")
              
                st.success(
                    f"✅ **¡Bloque #{blk.index} minado!**  \n"
                    f"⏱️ Tiempo: **{elapsed:.2f}s**  \n"
                    f"🔢 Nonce encontrado: **{blk.nonce:,}**  \n"
                    f"💰 Recompensa para **{miner_w.name}**: **{total_reward:.4f}** monedas"
                )

                col1, col2 = st.columns(2)
                col1.markdown("**Hash del bloque:**")
                col1.code(blk.hash, language="text")
                col2.markdown("**Hash del bloque anterior:**")
                col2.code(blk.prev_hash, language="text")

                with st.expander("📦 Ver bloque completo (JSON)"):
                    st.json(blk.to_dict())

            except RuntimeError as e:
                st.error(f"❌ Error durante la minería: {e}")

    # ── Historial de tiempos ──────────────────────────────────
    if bc.mining_times:
        st.markdown("---")
        st.markdown("### 📊 Historial de tiempos de minado")
        df_times = pd.DataFrame({
            "Bloque":     list(range(1, len(bc.mining_times) + 1)),
            "Tiempo (s)": bc.mining_times,
        }).set_index("Bloque")
        st.bar_chart(df_times, y="Tiempo (s)")
        st.caption(
            f"Promedio: {sum(bc.mining_times)/len(bc.mining_times):.2f}s  |  "
            f"Total bloques minados: {len(bc.mining_times)}"
        )


# ═════════════════════════════════════════════════════════════
# 🔗  BLOCKCHAIN — Visualizar la cadena
# ═════════════════════════════════════════════════════════════
elif section == "🔗 Blockchain":
    st.title("🔗 Visualización de la Blockchain")

    # ── Estado de integridad ──────────────────────────────────
    valid = bc.is_valid()
    if valid:
        st.success("✅ Cadena válida — todos los hashes encadenados correctamente")
    else:
        st.error("❌ Cadena inválida — se detectó una modificación en algún bloque")

    st.markdown(
        f"**Total de bloques:** {len(bc.chain)}  |  "
        f"**Dificultad:** {DIFFICULTY} ceros  |  "
        f"**Bloques válidos:** {'Todos' if valid else 'Detectado error'}"
    )
    st.markdown("---")

    # ── Vista resumen tipo tabla ──────────────────────────────
    st.markdown("### 📋 Resumen de la cadena")
    summary = [
        {
            "Bloque":  b.index,
            "Timestamp": b.timestamp,
            "Txs":     len(b.transactions),
            "Nonce":   b.nonce,
            "Hash":    b.hash[:32] + "...",
        }
        for b in bc.chain
    ]
    st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

    # ── Detalle bloque a bloque ───────────────────────────────
    st.markdown("---")
    st.markdown("### 🔎 Detalle por bloque")
    for blk in reversed(bc.chain):
        label = (
            f"Bloque #{blk.index}  "
            f"{'🟢' if blk.hash.startswith('0'*DIFFICULTY) else '🔴'}  "
            f"| {blk.timestamp}  "
            f"| {len(blk.transactions)} tx(s)  "
            f"| Hash: {blk.hash[:20]}..."
        )
        with st.expander(label, expanded=(blk.index == len(bc.chain) - 1)):
            r1, r2 = st.columns(2)
            r1.markdown(f"**Índice:** `{blk.index}`")
            r1.markdown(f"**Timestamp:** `{blk.timestamp}`")
            r1.markdown(f"**Nonce:** `{blk.nonce:,}`")
            r1.markdown(f"**Transacciones:** `{len(blk.transactions)}`")
            r2.markdown("**Hash del bloque:**")
            r2.code(blk.hash, language="text")
            r2.markdown("**Hash del bloque anterior:**")
            r2.code(blk.prev_hash, language="text")

            st.markdown("**Transacciones en este bloque:**")
            for idx, tx in enumerate(blk.transactions):
                is_coinbase = len(tx.get("inputs", [])) == 0
                tipo = "💎 Coinbase (recompensa)" if is_coinbase else f"💸 Tx #{idx}"
                with st.expander(f"{tipo} — TXID: {tx['txid'][:20]}...", expanded=False):
                    st.json(tx)


# ═════════════════════════════════════════════════════════════
# 💰  BALANCES — Saldos y UTXOs
# ═════════════════════════════════════════════════════════════
elif section == "💰 Balances":
    st.title("💰 Balances y UTXOs")
    st.markdown(
        "Los saldos se calculan sumando todos los **UTXOs** "
        "(salidas no gastadas) de cada dirección."
    )

    if not bc.wallets:
        st.info("No hay wallets registradas. Ve a **Usuarios** para crear una.")
        st.stop()

    # ── Tabla de saldos ───────────────────────────────────────
    st.markdown("### 💵 Saldos actuales")
    rows = []
    for addr, w in bc.wallets.items():
        total_bal  = bc.balance(addr)
        avail_bal  = bc.available_balance(addr)
        locked_bal = round(total_bal - avail_bal, 8)
        rows.append({
            "Nombre":            w.name or "—",
            "Dirección":         addr[:20] + "...",
            "Saldo total":       round(total_bal, 8),
            "Saldo disponible":  round(avail_bal, 8),
            "En transacciones":  round(locked_bal, 8),
            "UTXOs":             len(bc.utxo_set.for_address(addr)),
        })

    df = pd.DataFrame(rows).sort_values("Saldo total", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Gráfico de distribución ────────────────────────────────
    non_zero = df[df["Saldo total"] > 0]
    if not non_zero.empty:
        st.markdown("### 📊 Distribución de saldos")
        chart_df = non_zero.set_index("Nombre")[["Saldo total", "Saldo disponible"]]
        st.bar_chart(chart_df)

    # ── UTXOs del sistema ─────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🗂️ Conjunto UTXO completo")
    st.caption("Cada UTXO es una salida de transacción que aún no ha sido gastada.")

    if bc.utxo_set.utxos:
        utxo_rows = []
        for key, u in bc.utxo_set.utxos.items():
            txid, idx = key.rsplit(":", 1)
            owner = bc.wallets.get(u["address"])
            # Determinar si está bloqueado en un pending
            locked = key in {
                f"{inp['txid']}:{inp['index']}"
                for tx in bc.pending for inp in tx.inputs
            }
            utxo_rows.append({
                "TXID":         txid[:20] + "...",
                "Índice":       int(idx),
                "Propietario":  owner.name if owner else u["address"][:14] + "...",
                "Cantidad":     round(u["amount"], 8),
                "Estado":       "🔒 En uso" if locked else "✅ Disponible",
            })

        st.dataframe(
            pd.DataFrame(utxo_rows).sort_values("Cantidad", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            f"Total UTXOs: {len(utxo_rows)}  |  "
            f"Suma total: {sum(u['Cantidad'] for u in utxo_rows):.4f} monedas"
        )
    else:
        st.info("No hay UTXOs en el sistema.")
