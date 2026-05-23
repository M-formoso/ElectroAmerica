-- Reset de stock y remitos huerfanos
--
-- Vacia todo el stock de los depositos y borra (soft-delete) todos los
-- remitos del sistema. No toca:
--   * catalogo de Materiales (codigos, nombres, unidades)
--   * Depositos / Subdepositos (siguen vivos pero vacios)
--   * Clientes, Proyectos, Usuarios, Equipos
--
-- Pensado para correr UNA vez antes de empezar a operar limpio.
-- IMPORTANTE: hacer backup antes.

BEGIN;

-- 1) Soft-delete de todo el stock por deposito
UPDATE deposito_materiales SET activo = false WHERE activo = true;

-- 2) Soft-delete de descuentos e items de remitos
UPDATE remito_descuentos SET activo = false WHERE activo = true;
UPDATE remito_items SET activo = false WHERE activo = true;

-- 3) Soft-delete de remitos
UPDATE remitos SET activo = false WHERE activo = true;

-- 4) Reiniciar la secuencia de numero de remito a 1
--    (asi el proximo remito que se cree sera REM-0001)
ALTER SEQUENCE remito_numero_seq RESTART WITH 1;

COMMIT;
