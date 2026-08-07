-- Reset completo de stock, remitos e historial de movimientos
--
-- Vacia toda la operatoria de stock para arrancar de cero:
--   * Borra todos los remitos (con items y descuentos en cascada)
--   * Borra el stock por deposito (deposito_materiales)
--   * Borra el historial de movimientos de stock
--   * Pone stock_actual = 0 en todos los materiales
--   * Reinicia la secuencia de numero de remito a 1
--
-- NO toca:
--   * Catalogo de materiales (codigos, nombres, unidades, precios)
--   * Depositos / Subdepositos (siguen vivos pero vacios)
--   * Proyectos, Clientes, Usuarios, Equipos, Jornadas
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

-- 3) Hard-delete del historial de movimientos de stock
DELETE FROM movimientos_stock;

-- 4) Reset del stock global de cada material
UPDATE materiales SET stock_actual = 0 WHERE stock_actual <> 0;

-- 5) Reiniciar la secuencia de numero de remito a 1
--    (asi el proximo remito que se cree sera REM-0001)
ALTER SEQUENCE remito_numero_seq RESTART WITH 1;

COMMIT;
