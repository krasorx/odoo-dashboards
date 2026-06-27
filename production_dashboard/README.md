# Production Dashboard

Dashboard OWL de estimación de producción para **Odoo 19 EE**, con caché inteligente
e invalidación event-driven. Mejora el módulo `bom_dashboard` con un popup de detalle
de BOM que navega a la estimación precargando producto/BOM.

## Instalación

1. Instalar `production_dashboard` (arrastra `mrp`, `sale`, `purchase`, `stock`, `product`, `web`).
2. Actualizar `bom_dashboard` (ahora depende de `production_dashboard`):
   ```
   -u production_dashboard,bom_dashboard
   ```
3. Menús creados bajo **Fabricación**:
   - *Dashboard BOM* (popup mejorado)
   - *Estimación de Producción* (dashboard nuevo, menú propio)

## Uso

- **Por Cantidad:** elegí producto + cantidad objetivo → KPIs (coste unitario/total,
  tiempo total, % en stock), tabla de componentes ordenable, desglose de costes y alertas
  de faltantes.
- **Por Coste:** elegí producto + presupuesto objetivo → cantidad máxima fabricable +
  presupuesto restante + desglose.
- **Historial** global de ejecuciones; clic en una fila recarga sus filtros y recalcula.
- Desde **Dashboard BOM**, clic en una tarjeta de producto → popup con estructura + KPIs
  → botón **"Estimar Producción"** abre el dashboard de estimación con todo precargado.
- Badge **⚡ desde caché** cuando el resultado vino de caché (experiencia instantánea).

## Arquitectura: caché e invalidación

### Caché (`production.estimation.cache`)
- **Clave** = `sha256(modo + product_id + bom_id + monto + filtros)`. Resultados en JSON.
- **TTL** configurable vía `ir.config_parameter` `production_dashboard.cache_ttl`
  (def. `3600` seg). Caché **global** compartido entre usuarios: si alguien ya calculó la
  misma consulta, cualquier usuario la recibe al instante.
- Cada entrada guarda `involved_product_ids` (todos los productos de la explosión de la
  BOM), de modo que las **BOMs anidadas** quedan cubiertas en la invalidación: basta con
  que cambie cualquier producto involucrado para invalidar la entrada.
- Cron diario `_gc_expired` purga entradas vencidas.

### Invalidación event-driven (overrides síncronos)
Se sobrescribe `create`/`write`/`unlink` en los modelos relevantes; cada uno junta los
`product_id` afectados y llama a `cache.invalidate_for_products(...)`:

| Modelo | Evento | Productos afectados |
|---|---|---|
| `mrp.production` | `write` a `state = done` | producto + componentes (`move_raw_ids`) |
| `sale.order.line` | create/write/unlink | productos de las líneas |
| `purchase.order.line` | create/write/unlink | productos de las líneas |
| `mrp.bom` / `mrp.bom.line` | create/write/unlink | producto + líneas + **reverse-BOM** (padres anidados) |
| `product.template` / `product.product` | write de `standard_price`/`list_price` | el producto |
| `stock.move` | write a `state = done` | `product_id` |
| `stock.lot` | create/write/unlink | `product_id` |

**Reverse-BOM** (`_reverse_bom_products`): ante cambios *estructurales* de una BOM, sube por
`mrp.bom.line` hasta los productos terminados padre (iterando hasta punto fijo) e invalida
también sus cachés, porque un cambio de estructura altera qué productos quedan "involucrados".

### Motor (`production.estimation.engine`, AbstractModel)
- `_unit_cost` recursivo (memoizado por request) sobre la explosión de BOM.
- `estimate_by_quantity` / `estimate_by_cost` / `bom_detail`.
- Lead time: para fabricados, `mrp.bom.produce_delay`; para comprados, `supplierinfo.delay`.
- **Sin cuentas analíticas** (a diferencia del wizard de referencia v14).

## Mejoras futuras

- Vendorizar Chart.js/Tailwind (offline, sin CDN).
- Precálculo asíncrono (cron/cola) de estimaciones frecuentes para "precalentar" el caché.
- Estimación por orden de venta completa / multi-producto.
- Que los filtros de lotes y proveedores preferidos alteren el cálculo (hoy entran a la
  clave de caché pero no modifican costos).
- Exportación PDF/XLSX y creación directa de MO/PO desde la estimación (plan de
  optimización, como el wizard v14).
- Lead time con calendario laboral y delays reales de proveedor encadenados.
- Invalidación con granularidad por almacén/ubicación.
