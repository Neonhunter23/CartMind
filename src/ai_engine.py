import json
import time
import random

# Esto asegura que la demo funcione al 100% sin problemas de cuota o internet.

def extract_search_intent(user_query):
    """
    SIMULACIÓN DE IA (Rule-Based):
    Analiza la frase del usuario y decide qué categoría y filtros aplicar
    basándose en palabras clave predefinidas para la demo.
    """
    # Simulamos un pequeño "tiempo de pensar" para dar realismo (0.5 segundos)
    time.sleep(1)

    q = user_query.lower()

    # --- CASO 1: OFICINA / TELETRABAJO ---
    if any(x in q for x in ["teletrabajo", "estudiar", "escritorio", "oficina", "silla pc"]):
        return {
            "category": "Chairs",  # Priorizamos sillas, pero el buscador también mirará keywords
            "keywords": "escritorio",
            "max_price": None,
            "sort_by": "relevance"
        }

    # --- CASO 2: JARDÍN / TERRAZA (Datos Inyectados) ---
    if any(x in q for x in ["jardín", "terraza", "exterior", "balcón"]):
        return {
            "category": "Outdoor",
            "keywords": "jardín",
            "max_price": None,
            "sort_by": "relevance"
        }

    # --- CASO 3: SALÓN / KIVIK (Para enseñar Cross-Selling) ---
    if any(x in q for x in ["kivik", "sofá", "salón", "descansar"]):
        return {
            "category": "Sofas & armchairs",
            "keywords": "KIVIK" if "kivik" in q else "Sofa",
            "max_price": None,
            "sort_by": "relevance"
        }

    # --- CASO 4: ILUMINACIÓN (Para enseñar filtros de precio) ---
    if any(x in q for x in ["luz", "lámpara", "bombilla", "industrial", "alumbrar", "iluminación"]):
        return {
            "category": "Lighting",
            "keywords": "industrial" if "industrial" in q else "Lamp",
            # Si pide barato o menos de X, activamos filtro simulado
            "max_price": 70 if ("70" in q or "barato" in q) else None,
            "sort_by": "price_asc" if ("barata" in q or "económica" in q) else "relevance"
        }

    # --- CASO 5: DORMITORIO ---
    if any(x in q for x in ["cama", "dormitorio", "colchón", "sábana"]):
        return {
            "category": "Beds",
            "keywords": "Bed",
            "max_price": None,
            "sort_by": "relevance"
        }

    # --- CASO POR DEFECTO (Búsqueda genérica) ---
    # Si no cae en los casos preparados, buscamos tal cual lo que escribió
    return {
        "category": None,
        "keywords": user_query,
        "max_price": None,
        "sort_by": "relevance"
    }


def generate_sales_response(product_row, user_query):
    """
    Genera un pitch de venta convincente sin llamar a la IA.
    Detecta el producto y devuelve un texto "enlatado" de alta calidad.
    """
    name = str(product_row['name']).upper()
    price = product_row['price']

    # Respuestas específicas para los productos estrella de la demo
    if "KIVIK" in name:
        return f"¡Excelente elección! El sofá KIVIK es nuestro top ventas. Es modular, súper cómodo y su funda es lavable. Ideal para tu salón."

    if "MARKUS" in name:
        return f"La silla MARKUS es un clásico de oficinas. Tiene soporte lumbar, respaldo de malla transpirable y 10 años de garantía."

    if "FLINTAN" in name:
        return f"La FLINTAN es la mejor opción calidad-precio. Ergonómica y compacta, perfecta si tienes poco espacio para teletrabajar."

    if "ÄPPLARÖ" in name:
        return f"¡Prepárate para el buen tiempo! La serie ÄPPLARÖ está hecha de acacia sostenible y aguanta sol y lluvia perfectamente."

    if "TÄRNÖ" in name:
        return f"La TÄRNÖ es ideal para balcones pequeños. Se pliega fácilmente y ocupa poquísimo espacio."

    if "HEKTAR" in name:
        return f"El estilo industrial de la HEKTAR nunca pasa de moda. Da una luz focalizada genial para leer o crear ambiente."

    # Respuesta genérica aleatoria para el resto de productos
    generic_responses = [
        f"Aquí tienes el modelo {product_row['name']}. Es una opción fantástica por {price} € que encaja con lo que buscas.",
        f"He encontrado este {product_row['name']} por {price} €. Los clientes destacan su durabilidad y diseño nórdico.",
        f"Mira qué maravilla: {product_row['name']}. Funcionalidad y diseño sueco al mejor precio ({price} €)."
    ]

    return random.choice(generic_responses)