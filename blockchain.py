"""
Proyecto Integrador — Blockchain Simulator
==========================================
Módulo 1 : Wallets y Claves      (ECDSA secp256k1 + SHA-256)
Módulo 2 : Transacciones y UTXO
Módulo 3 : Bloques y Blockchain
Módulo 4 : Génesis y Minería     (Proof of Work)
"""

import hashlib
import json
import time
from datetime import datetime

from ecdsa import SigningKey, VerifyingKey, SECP256k1

# ─────────────────────────────────────────────────────────────
# Parámetros globales
# ─────────────────────────────────────────────────────────────
DIFFICULTY    = 4       # Ceros iniciales requeridos en el hash (PoW)
MINING_REWARD = 3.0     # Monedas base por bloque minado
GENESIS_COINS = 1000.0  # Monedas iniciales del bloque génesis


# ═════════════════════════════════════════════════════════════
# MÓDULO 1 — WALLETS Y CLAVES
# ═════════════════════════════════════════════════════════════

class Wallet:
    """
    Billetera de usuario con par de llaves ECDSA sobre secp256k1.

    - private_key : clave privada aleatoria (SigningKey)
    - public_key  : clave pública derivada   (VerifyingKey)
    - address     : SHA-256 de la clave pública (hex, 64 chars)
    """

    def __init__(self, name: str = ""):
        self.name = name
        # Generación de claves con ECDSA / secp256k1
        self._sk: SigningKey  = SigningKey.generate(curve=SECP256k1)
        self._vk: VerifyingKey = self._sk.get_verifying_key()
        # Dirección = SHA-256(clave pública)
        self.address: str = hashlib.sha256(self._vk.to_string()).hexdigest()

    # ── accesores de solo lectura ─────────────────────────────

    @property
    def private_key_hex(self) -> str:
        """Clave privada en formato hexadecimal."""
        return self._sk.to_string().hex()

    @property
    def public_key_hex(self) -> str:
        """Clave pública (punto de la curva) en hexadecimal."""
        return self._vk.to_string().hex()

    # ── firma y verificación ─────────────────────────────────

    def sign(self, data: str) -> str:
        """Firma 'data' con la clave privada; devuelve firma en hex."""
        return self._sk.sign(data.encode()).hex()

    @staticmethod
    def verify(pub_hex: str, sig_hex: str, data: str) -> bool:
        """
        Verifica que 'sig_hex' sea una firma válida de 'data'
        producida con la clave privada correspondiente a 'pub_hex'.
        """
        try:
            vk = VerifyingKey.from_string(bytes.fromhex(pub_hex), curve=SECP256k1)
            return vk.verify(bytes.fromhex(sig_hex), data.encode())
        except Exception:
            return False


# ═════════════════════════════════════════════════════════════
# MÓDULO 2 — TRANSACCIONES Y UTXO
# ═════════════════════════════════════════════════════════════

class Transaction:
    """
    Transacción de la blockchain.

    inputs  : [{"txid": str, "index": int, "signature": str, "public_key": str}]
              Cada entrada referencia un UTXO existente y lleva firma digital.
    outputs : [{"address": str, "amount": float}]
              Cantidad enviada y dirección del receptor.
    fee     : comisión opcional para el minero (mining fee).
    txid    : SHA-256(meta de inputs + outputs + fee)
    """

    def __init__(self, inputs: list, outputs: list, fee: float = 0.0):
        self.inputs  = inputs
        self.outputs = outputs
        self.fee     = fee
        self.txid    = self._compute_txid()

    def _compute_txid(self) -> str:
        # Solo meta-datos de inputs (sin firma) para calcular txid
        meta = [{"txid": i["txid"], "index": i["index"]} for i in self.inputs]
        raw  = json.dumps({"inputs": meta, "outputs": self.outputs, "fee": self.fee},
                          sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    @classmethod
    def coinbase(cls, recipient: str, amount: float) -> "Transaction":
        """
        Transacción especial sin entradas:
        crea monedas de la nada (génesis o recompensa de minero).
        """
        return cls(inputs=[], outputs=[{"address": recipient, "amount": amount}])

    def to_dict(self) -> dict:
        return {
            "txid":    self.txid,
            "inputs":  self.inputs,
            "outputs": self.outputs,
            "fee":     self.fee,
        }


class UTXOSet:
    """
    Conjunto de salidas no gastadas (Unspent Transaction Outputs).

    Representación interna (diccionario):
        clave : "txid:index"
        valor : {"address": str, "amount": float}
    """

    def __init__(self):
        self.utxos: dict = {}

    # ── lectura ───────────────────────────────────────────────

    def for_address(self, address: str) -> dict:
        """Todos los UTXOs de una dirección."""
        return {k: v for k, v in self.utxos.items()
                if v["address"] == address}

    def available_for(self, address: str, pending: list) -> dict:
        """
        UTXOs de la dirección que NO están comprometidos
        por transacciones en el pool de pendientes.
        """
        locked = {
            f"{inp['txid']}:{inp['index']}"
            for tx in pending for inp in tx.inputs
        }
        return {k: v for k, v in self.for_address(address).items()
                if k not in locked}

    def balance(self, address: str) -> float:
        return sum(v["amount"] for v in self.for_address(address).values())

    def available_balance(self, address: str, pending: list) -> float:
        return sum(v["amount"] for v in self.available_for(address, pending).values())

    # ── escritura ─────────────────────────────────────────────

    def _add(self, txid: str, idx: int, address: str, amount: float):
        self.utxos[f"{txid}:{idx}"] = {"address": address, "amount": amount}

    def _remove(self, txid: str, idx: int):
        self.utxos.pop(f"{txid}:{idx}", None)

    # ── validación y aplicación ───────────────────────────────

    def apply(self, tx: Transaction) -> tuple:
        """
        Valida la transacción y la aplica al UTXO set.
        Devuelve (True, "") o (False, mensaje_de_error).

        Flujo:
          1. Coinbase → siempre válida; agrega UTXOs sin verificar entradas.
          2. Normal   → verifica existencia, firma digital y propiedad de UTXOs;
                        elimina UTXOs gastados y agrega los nuevos.
        """
        # ── Coinbase: sin entradas ────────────────────────────
        if not tx.inputs:
            for i, out in enumerate(tx.outputs):
                self._add(tx.txid, i, out["address"], out["amount"])
            return True, ""

        # ── Verificar cada entrada ────────────────────────────
        total_in  = 0.0
        to_remove = []

        for inp in tx.inputs:
            key = f"{inp['txid']}:{inp['index']}"

            # 1. El UTXO debe existir
            if key not in self.utxos:
                return False, f"UTXO '{key}' no existe en el conjunto actual"

            utxo = self.utxos[key]

            # 2. Verificar firma digital
            sig_msg = f"{inp['txid']}:{inp['index']}"
            if not Wallet.verify(inp["public_key"], inp["signature"], sig_msg):
                return False, "Firma digital inválida"

            # 3. Verificar propiedad: address = SHA-256(clave pública)
            derived = hashlib.sha256(bytes.fromhex(inp["public_key"])).hexdigest()
            if derived != utxo["address"]:
                return False, "La clave pública no corresponde al propietario del UTXO"

            total_in += utxo["amount"]
            to_remove.append((inp["txid"], int(inp["index"])))

        # 4. Verificar que las entradas cubran salidas + fee
        total_out = sum(o["amount"] for o in tx.outputs) + tx.fee
        if total_in < total_out - 1e-9:
            return False, (f"Fondos insuficientes: "
                           f"entrada={total_in:.6f}, salida+fee={total_out:.6f}")

        # ── Confirmar cambios ─────────────────────────────────
        for txid, idx in to_remove:
            self._remove(txid, idx)
        for i, out in enumerate(tx.outputs):
            self._add(tx.txid, i, out["address"], out["amount"])

        return True, ""


# ═════════════════════════════════════════════════════════════
# MÓDULOS 3 & 4 — BLOQUES, BLOCKCHAIN, GÉNESIS Y MINERÍA
# ═════════════════════════════════════════════════════════════

class Block:
    """
    Bloque de la cadena.

    Campos de cabecera : index, timestamp, prev_hash, nonce
    Cuerpo             : transactions (lista de dicts)
    hash               : SHA-256(cabecera + cuerpo), calculado con PoW

    La cadena es inmutable: cambiar cualquier campo invalida el hash
    y, en cascada, todos los bloques siguientes.
    """

    def __init__(self, index: int, transactions: list, prev_hash: str,
                 difficulty: int = DIFFICULTY):
        self.index        = index
        self.timestamp    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.transactions = transactions        # lista de dicts serializables
        self.prev_hash    = prev_hash
        self.difficulty   = difficulty
        self.nonce        = 0
        self.hash         = self._mine()        # PoW al construir

    def _to_hashable(self) -> str:
        """Serializa el bloque (con nonce actual) para calcular su hash."""
        return json.dumps({
            "index":        self.index,
            "timestamp":    self.timestamp,
            "prev_hash":    self.prev_hash,
            "nonce":        self.nonce,
            "transactions": self.transactions,
        }, sort_keys=True)

    def compute_hash(self) -> str:
        return hashlib.sha256(self._to_hashable().encode()).hexdigest()

    def _mine(self) -> str:
        """
        Prueba de Trabajo (PoW):
        Incrementa el nonce hasta que el hash comience con
        'difficulty' ceros consecutivos.
        """
        prefix = "0" * self.difficulty
        while True:
            h = self.compute_hash()
            if h.startswith(prefix):
                return h
            self.nonce += 1

    def to_dict(self) -> dict:
        return {
            "index":        self.index,
            "timestamp":    self.timestamp,
            "prev_hash":    self.prev_hash,
            "nonce":        self.nonce,
            "hash":         self.hash,
            "transactions": self.transactions,
        }


class Blockchain:
    """
    Cadena de bloques completa.

    Integra:
      · Registro de wallets
      · UTXO set
      · Pool de transacciones pendientes
      · Minería con PoW
      · Validación de integridad de la cadena
    """

    def __init__(self):
        self.chain:        list    = []        # Lista de Block
        self.pending:      list    = []        # Lista de Transaction (pendientes)
        self.utxo_set:     UTXOSet = UTXOSet()
        self.wallets:      dict    = {}        # address → Wallet
        self.mining_times: list    = []        # Tiempos de minado (segundos)

    # ── wallets ───────────────────────────────────────────────

    def create_wallet(self, name: str = "") -> Wallet:
        """Crea una nueva wallet y la registra en el sistema."""
        w = Wallet(name=name)
        self.wallets[w.address] = w
        return w

    # ── génesis ───────────────────────────────────────────────

    def initialize(self, genesis_wallet: Wallet):
        """
        Crea el bloque génesis con una transacción coinbase especial
        que entrega GENESIS_COINS a genesis_wallet.
        Solo se llama una vez al inicio.
        """
        cb      = Transaction.coinbase(genesis_wallet.address, GENESIS_COINS)
        genesis = Block(index=0, transactions=[cb.to_dict()], prev_hash="0")
        ok, err = self.utxo_set.apply(cb)
        if not ok:
            raise RuntimeError(f"Error en bloque génesis: {err}")
        self.chain.append(genesis)

    # ── consultas de saldo ────────────────────────────────────

    def balance(self, address: str) -> float:
        """Saldo total (incluye UTXOs comprometidos en pending)."""
        return self.utxo_set.balance(address)

    def available_balance(self, address: str) -> float:
        """Saldo disponible (excluye UTXOs ya comprometidos)."""
        return self.utxo_set.available_balance(address, self.pending)

    def all_balances(self) -> dict:
        return {addr: self.balance(addr) for addr in self.wallets}

    # ── validación de la cadena ───────────────────────────────

    def is_valid(self) -> bool:
        """
        Verifica la integridad de toda la cadena:
          1. prev_hash de cada bloque coincide con el hash del anterior.
          2. El hash de cada bloque cumple la condición de PoW.
        """
        prefix = "0" * DIFFICULTY
        for i in range(1, len(self.chain)):
            blk  = self.chain[i]
            prev = self.chain[i - 1]
            if blk.prev_hash != prev.hash:
                return False
            if not blk.hash.startswith(prefix):
                return False
        return True

    # ── construcción de transacciones ─────────────────────────

    def build_transaction(self, sender: Wallet, recipient: str,
                          amount: float, fee: float = 0.0) -> Transaction:
        """
        Construye y firma una transacción usando UTXOs disponibles.
        Incluye cambio de vuelta al remitente si sobra saldo.
        No aplica cambios al UTXO set; la tx debe minarse primero.
        """
        avail      = self.utxo_set.available_for(sender.address, self.pending)
        total_avail = sum(v["amount"] for v in avail.values())

        if total_avail < amount + fee - 1e-9:
            raise ValueError(
                f"Fondos insuficientes. "
                f"Disponible: {total_avail:.4f}, "
                f"Requerido:  {amount + fee:.4f}"
            )

        # Seleccionar UTXOs hasta cubrir monto + fee
        inputs, total_in = [], 0.0
        for key, utxo in avail.items():
            txid, idx = key.rsplit(":", 1)
            sig_msg = f"{txid}:{idx}"
            inputs.append({
                "txid":       txid,
                "index":      int(idx),
                "signature":  sender.sign(sig_msg),
                "public_key": sender.public_key_hex,
            })
            total_in += utxo["amount"]
            if total_in >= amount + fee:
                break

        outputs = [{"address": recipient, "amount": amount}]
        change  = round(total_in - amount - fee, 8)
        if change > 1e-9:
            outputs.append({"address": sender.address, "amount": change})

        return Transaction(inputs=inputs, outputs=outputs, fee=fee)

    def submit(self, tx: Transaction):
        """Agrega una transacción al pool de pendientes."""
        self.pending.append(tx)

    # ── minería ───────────────────────────────────────────────

    def mine_pending(self, miner: Wallet) -> tuple:
        """
        Mina un nuevo bloque con las transacciones pendientes:
          1. Calcula la recompensa: MINING_REWARD + suma de fees.
          2. Crea la transacción coinbase con la recompensa.
          3. Ejecuta la Prueba de Trabajo (PoW) para encontrar el nonce.
          4. Aplica todas las transacciones al UTXO set.
          5. Agrega el bloque a la cadena y vacía el pool.
        Devuelve (Block, tiempo_de_minado_en_segundos).
        """
        if not self.chain:
            raise RuntimeError("Blockchain no inicializada. Llama a initialize() primero.")

        fees     = sum(tx.fee for tx in self.pending)
        reward   = round(MINING_REWARD + fees, 8)
        coinbase = Transaction.coinbase(miner.address, reward)

        all_txs  = [coinbase] + self.pending[:]

        # Medir tiempo de minado (incluye PoW)
        t0    = time.time()
        block = Block(
            index        = len(self.chain),
            transactions = [tx.to_dict() for tx in all_txs],
            prev_hash    = self.chain[-1].hash,
        )
        elapsed = time.time() - t0
        self.mining_times.append(elapsed)

        # Aplicar transacciones al UTXO set
        for tx in all_txs:
            ok, err = self.utxo_set.apply(tx)
            if not ok:
                raise RuntimeError(f"TX {tx.txid[:12]}… rechazada: {err}")

        self.chain.append(block)
        self.pending.clear()
        return block, elapsed
