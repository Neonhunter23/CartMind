# CartMind — AI E-commerce Assistant Plugin

Plugin de inteligencia artificial para tiendas online que combina búsqueda por lenguaje natural (NLP) y recomendaciones de cross-selling basadas en Machine Learning (Apriori), con el objetivo de reducir el abandono de carrito y aumentar el ticket medio.

Desarrollado como proyecto de la asignatura **Datos y Negocio** del MUDS (La Salle – Universitat Ramon Llull).  
**Autores:** Daniel Ruiz · Marc Dulcet

---

## El problema

> La falta de relevancia en la búsqueda de productos causa un abandono del carrito del **68%**.

Los usuarios no encuentran lo que buscan → se frustran → se van. CartMind actúa como un experto en ventas disponible 24/7 directamente en la tienda.

---

## Resultados — Caso de éxito A/B Test (Lámparas Barcelona, 2 meses)

| Métrica | Sin CartMind (12k sesiones) | Con CartMind (11k sesiones) | Uplift |
|---|---|---|---|
| Tasa de Conversión (CR) | 2.1% | 2.6% | **+23.8%** |
| Valor Medio del Pedido (AOV) | 85.00 € | 104.50 € | **+22.9%** |
| CTR en Recomendaciones | 0% | 11.8% | **∞** |
| Ingreso por Sesión (RPS) | 1.78 € | 2.71 € | **+52.2%** |

---

## Arquitectura

```
Historial de Transacciones  ──┐
                               ├──► Motor ETL & Data Augmentation
Catálogo de Productos       ──┘         │
                                        ├──► Cerebro IA (Gemini 2.5 Flash)  ──┐
                                        │    NLP + Extracción de intención     │
                                        │                                       ├──► API REST ──► Widget JS
                                        └──► Motor Recomendación (Apriori ML) ──┘    FastAPI      PrestaShop
                                             Cross-selling automático                              WooCommerce
```

**Dos motores de IA:**
- **Cerebro IA** — Extrae intención estructurada `{categoría, keywords, precio_max, ordenación}` de cualquier consulta en lenguaje natural usando `gemini-2.5-flash`. Genera pitches de venta personalizados con `gemini-3.5-flash`.
- **Motor Recomendación** — Algoritmo Apriori sobre el historial de pedidos. Objetivo de producción: Lift > 1 y Confianza > 70%. Expuesto como "Frecuentemente comprados juntos".

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Demo UI | Streamlit |
| API REST | FastAPI + Uvicorn |
| IA / LLM | Google Gemini 2.5 Flash · 3.5 Flash |
| ML | mlxtend (Apriori) · scikit-learn |
| Base de datos | PostgreSQL 15 (SQLAlchemy) |
| ETL | Pandas · NumPy · OpenPyXL |
| Infraestructura | Docker · Docker Compose |
| Widget | Vanilla JS (sin dependencias) |

---

## Estructura del proyecto

```
CartMind/
├── src/
│   ├── app.py              # Demo Streamlit (chatbot IKEA-branded)
│   ├── api.py              # API REST FastAPI — endpoints /search /recommend /health
│   ├── ai_engine.py        # Cerebro IA: intent extraction + pitch generation (Gemini)
│   ├── db.py               # Modelos SQLAlchemy + conexión PostgreSQL
│   ├── logic.py            # Motor de búsqueda: filtro categoría + keywords + precio
│   ├── recommender.py      # Apriori: build_association_rules() + get_recommendations()
│   ├── processor.py        # ETL: fusión de catálogo + ventas + data augmentation
│   └── ui_config.py        # CSS y configuración visual de la demo
├── static/
│   └── widget.js           # Widget embebible (recomendaciones + chat flotante)
├── docker/
│   ├── Dockerfile          # Imagen Streamlit
│   └── Dockerfile.api      # Imagen FastAPI
├── Data/
│   ├── IKEA SALES DATA.xlsx
│   ├── IKEA_SA_Furniture_Web_Scrapings_sss.csv
│   └── DecoMate_Master_Augmented.csv   # generado por processor.py
├── docker-compose.yml      # Streamlit + FastAPI + PostgreSQL
├── requirements.txt
├── INSTRUCCIONES.txt       # Setup detallado paso a paso
└── CLAUDE.md               # Documentación técnica del proyecto
```

---

## Quickstart

### Prerequisito — `.env` en la raíz:

```env
GEMINI_API_KEY=tu_clave_de_google_ai_studio

POSTGRES_USER=cartmind
POSTGRES_PASSWORD=tu_password
POSTGRES_DB=cartmind
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

Obtener clave gratuita: https://aistudio.google.com/app/apikey

### Con Docker:

```bash
# 1. Levantar todos los servicios
docker compose up --build

# 2. Generar el dataset (solo la primera vez)
docker exec decomate_app python src/processor.py
```

| Servicio | URL |
|---|---|
| Demo Streamlit | http://localhost:8501 |
| API REST | http://localhost:8000 |
| Documentación API | http://localhost:8000/docs |

### Sin Docker:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cd src && python processor.py && cd ..

# Terminal 1 — Demo
cd src && streamlit run app.py

# Terminal 2 — API
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

---

## API

```bash
# Búsqueda por lenguaje natural
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "quiero una lámpara industrial para el salón"}'

# Recomendaciones cross-sell
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"product_name": "KIVIK", "top_n": 3}'

# Estado del sistema
curl http://localhost:8000/health
```

---

## Integración en cualquier tienda web

Pegar antes del `</body>` de la web:

```html
<script
  src="https://tu-servidor.com:8000/static/widget.js"
  data-decomate-api="https://tu-servidor.com:8000"
  defer>
</script>
```

El widget detecta automáticamente si es una página de producto (PrestaShop / WooCommerce) y añade el bloque "Frecuentemente comprados juntos". En todas las páginas activa un chat flotante de asistencia.

---

## Modelo de negocio (SaaS)

| Plan | Tarifa | Características |
|---|---|---|
| **BUSINESS** | 299 €/mes + 1% success fee | Hasta 1.000 productos · Plug & Play · Mate-Basic |
| **ENTERPRISE** | A valorar + 0.3% success fee | Sin límites · ERP integrations · Mate-Pro · API dedicada |

**Break-even estimado:** 3.3 años · **Expansión global:** 4 años

---

## Roadmap

- [x] **Fase 1 — MVP** · Demo funcional + integración Gemini real + API REST + widget JS
- [ ] **Fase 2 — Plan Business** · Mate-Basic · integraciones de pago · módulo de ingesta personalizada
- [ ] **Fase 3 — Plan Enterprise** · Mate-Pro · fine-tuning de marca · servidores dedicados
- [ ] **Fase 4 — Expansión** · predicción de inventario · dashboard avanzado · internacionalización
