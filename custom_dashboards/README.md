# Custom Dashboards Module - Odoo 18

## Resumen del Proyecto

Se ha creado un módulo de dashboards personalizados para Odoo 18 con Tailwind CSS y la nueva versión de OWL.

## Estructura del Módulo

```
custom_dashboards/
├── __manifest__.py          # Manifest del módulo
├── __init__.py              # Importa controllers
├── controllers/
│   └── __init__.py          # Controladores Python con endpoints RPC
├── static/
│   ├── src/
│   │   ├── css/
│   │   │   └── custom_dashboards.css  # Estilos Tailwind CSS
│   │   ├── js/
│   │   │   ├── Dashboard.js            # Componente OWL
│   │   │   └── custom_dashboards.js    # JS legacy (opcional)
│   │   └── xml/
│   │       └── index.html              # Template HTML
├── views/
│   └── templates.xml                   # Templates Odoo con datos dinámicos
└── security/
    └── ir.model.access.csv             # Permisos de acceso

```

## Funcionalidades

### KPIs (Tarjetas de Métricas)
- 💵 Invoiced This Month - Monto facturado este mes
- 📄 Sales Invoices - Cantidad de facturas de ventas
- 🏭 Manufacturing Orders Done - Órdenes de manufactura completadas
- 📦 Total Qty Produced - Cantidad total producida
- ⏳ Sales to Deliver - Ventas pendientes de entrega
- 📋 Pending Sales Amount - Monto pendiente por ventas
- ⚠️ Overdue Invoices - Facturas vencidas
- 📈 Total Revenue - Ingresos totales

### Tablas de Datos
- Top Products by Sales - Productos más vendidos
- Recent Manufacturing Orders - Últimas órdenes de manufactura
- Overdue Invoices - Facturas vencidas con detalles

## Instalación

1. **Repositorio OCA/web clonado:**
   ```bash
   cd /home/krasorx/proyectos-personales/moneda/odoo/addons
   git clone git@github.com:OCA/web.git -b 18.0
   ```

2. **Módulo copiado a addons:**
   ```bash
   cp -r /home/krasorx/proyectos-personales/odoo-tailwind-css/custom_dashboards/* \
         /home/krasorx/proyectos-personales/moneda/odoo/addons/
   ```

3. **Configuración docker-compose:**
   El archivo `docker-compose.yaml` ya está configurado para montar el módulo:
   ```yaml
   volumes:
     - /home/krasorx/proyectos-personales/odoo-tailwind-css/custom_dashboards:/mnt/extra-addons/custom_dashboards
   ```

4. **Configuración odoo.conf:**
   El archivo `/home/krasorx/proyectos-personales/moneda/odoo/config/odoo.conf` incluye:
   ```
   addons_path = /mnt/extra-addons,~/proyectos-personales/odoo-tailwind-css/custom_dashboards,/opt/odoo/addons
   ```

## URL de Acceso

Una vez instalado el módulo en Odoo Studio o desde Admin > Apps:

- Dashboard principal: `http://localhost:8069/custom-dashboards/dashboard`
- API endpoints para datos:
  - `/my/invoices/monthly` - Facturación mensual
  - `/my/mps/completed` - Órdenes de manufactura completadas
  - `/my/sales/pending` - Ventas pendientes
  - `/my/overdue/invoices` - Facturas vencidas
  - `/my/top/products` - Productos top por ventas

## Tecnologías Usadas

- **Odoo 18** - Framework principal
- **OWL v2** - New Web Library (sin `odoo.define`)
- **Tailwind CSS** - Estilos modernos y responsivos
- **Chart.js** - Gráficos de tendencias mensuales

## Notas Importantes

1. El módulo requiere los módulos: `website`, `account`, `sale`
2. Necesitas permisos de usuario para ver el dashboard
3. Los datos se cargan automáticamente al acceder al dashboard
4. El botón "Refresh Data" actualiza los datos sin recargar la página
