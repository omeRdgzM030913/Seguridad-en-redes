Estimado profesor Eliseo, le comparto el enlace de mi simulador de blockchain. 
[https://seguridad-en-redes-jgfjgtwbhwhfqpjbc62knu.streamlit.app/#resumen-del-sistema]

Para comprobar el cumplimiento de los módulos solicitados, le sugiero seguir este flujo en la interfaz:

1. **Estado Inicial:** Ir a `Inicio` o `Balances` para verificar que solo existe el bloque Génesis con 1000 monedas.

2. **Creación de Identidades:** Ir a Usuarios y generar dos nuevas wallets (ej. Alice y Bob) para observar las llaves ECDSA y las direcciones SHA-256.

3. Ir a Transacciones y enviar monedas desde la cuenta Génesis Admin hacia Alice incorporando una comisión (mining fee).

4. Ir a Minería, seleccionar a Bob como minero y procesar el bloque para verificar la Prueba de Trabajo (PoW) y la distribución de recompensas.

5. Revisar Blockchain y Balances para auditar la integridad de la cadena y el modelo UTXO.»


2. **Creación de Identidades:** Ir a `Usuarios` y crear al menos dos wallets (ej. Alice y Bob).
3. **Distribución Inicial:** Ir a `Transacciones`, seleccionar a "Génesis (Admin)" como remitente y enviar fondos a Alice agregando una comisión.
4. **Prueba de Trabajo (PoW):** Ir a `Minería`, seleccionar a Bob como minero y ejecutar la minería para validar el cálculo del nonce y la asignación de recompensas.
5. **Auditoría de Integridad:** Ir a `Blockchain` para verificar el correcto encadenamiento de los hashes y a `Balances` para confirmar el modelo UTXO.
