-- Reset de stock y remitos huerfanos
--
-- Vacia todo el stock de los depositos y BORRA DEFINITIVAMENTE todos los
-- remitos del sistema (necesario para liberar los numeros y poder
-- reiniciar la secuencia). No toca:
--   * catalogo de Materiales (codigos, nombres, unidades)
--   * Depositos / Subdepositos (siguen vivos pero vacios)
--   * Clientes, Proyectos, Usuarios, Equipos
--
-- Pensado para correr UNA vez antes de empezar a operar limpio.
-- IMPORTANTE: hacer backup antes.
--
-- IMPORTANTE: hace hard-delete (no soft-delete). Si se hacia soft-delete
-- y luego se reiniciaba la secuencia a 1, los numeros viejos (REM-0001..)
-- chocaban con el unique constraint al crear remitos nuevos.

BEGIN;

-- 1) Hard-delete de remitos (cascade borra items y descuentos por FK)
DELETE FROM remitos;

-- 2) Hard-delete del stock por deposito
DELETE FROM deposito_materiales;

-- 3) Reiniciar la secuencia de numero de remito a 1
--    (asi el proximo remito que se cree sera REM-0001)
ALTER SEQUENCE remito_numero_seq RESTART WITH 1;

COMMIT;
