# Awesome AEO en Español [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> Lista curada de recursos sobre **Answer Engine Optimization (AEO)** en español — la práctica de optimizar sitios web para ser citados por ChatGPT, Claude, Perplexity y otros modelos de lenguaje.

---

## ¿Qué es AEO?

**Answer Engine Optimization (AEO)** es el conjunto de prácticas que mejoran la probabilidad de que un modelo de lenguaje (LLM) cite tu sitio web como fuente al responder preguntas.

A diferencia del SEO tradicional, que optimiza para algoritmos de ranking, el AEO optimiza para modelos que **extraen, comprenden y sintetizan** información. Los factores que determinan si un LLM te menciona son distintos a los que determinan si Google te posiciona:

- Un sitio puede estar en el **top 3 de Google** y ser completamente ignorado por ChatGPT.
- El **70% de los cambios** necesarios para aparecer en respuestas de IA son distintos a los del SEO clásico.
- El tráfico referido desde IA generativa creció un **123% en H1 2025**.

---

## Por qué importa ahora

- El **13% de las búsquedas en escritorio** ya son respondidas directamente por IA, sin que el usuario haga clic en ningún sitio.
- Ese porcentaje crece cada trimestre.
- El tráfico que llega desde ChatGPT o Perplexity convierte **3x más** que el tráfico de búsqueda clásica.
- Si alguien le pregunta a ChatGPT *"¿qué empresa de [tu rubro] recomiendas en [tu ciudad]?"* y tu sitio no está optimizado, simplemente no apareces — aunque tengas el mejor producto del mercado.

---

## Diferencia entre SEO y AEO

| | SEO | AEO |
|---|---|---|
| **Objetivo** | Rankear en resultados de búsqueda | Ser citado en respuestas de IA |
| **Algoritmo** | Rastreadores + PageRank | Modelos de lenguaje (LLMs) |
| **Formato clave** | Keywords, backlinks | JSON-LD, contenido citable, FAQ |
| **Métrica** | Posición en SERP | Frecuencia de citación |
| **Velocidad de impacto** | Semanas a meses | 4-8 semanas |

---

## Las 4 dimensiones del AEO

Los modelos de lenguaje evalúan tu sitio en cuatro áreas principales:

### 1. Datos Estructurados
Marcado técnico que permite a los LLMs identificar qué es tu empresa y qué hace.
- `JSON-LD` de organización (`@type: Organization`)
- `Schema.org` para productos, servicios, FAQs, artículos
- `Open Graph` y metadatos

### 2. Calidad Semántica del Contenido
Qué tan "citable" es tu texto para un modelo de lenguaje.
- Párrafos que responden preguntas directas (*¿Qué es X? ¿Cómo funciona X?*)
- Cada párrafo debe poder leerse sin contexto previo
- Vocabulario técnico preciso y consistente

### 3. Estructura de Página
Cómo está organizado el contenido para facilitar su extracción.
- Jerarquía clara de headings (H1, H2, H3)
- Secciones FAQ con preguntas y respuestas explícitas
- Suficiente profundidad de contenido por tema

### 4. Confianza y Profundidad
Señales que indican a los LLMs que tu sitio es una fuente confiable.
- Información de contacto y ubicación geográfica precisa
- Fecha de publicación y actualización del contenido
- Autoría identificable
- Cobertura profunda de los temas de tu dominio

---

## Guías y recursos

### Introducción al AEO
- [¿Qué es AEO y por qué tu negocio lo necesita hoy?](https://visible-ai.cl/#faq) — VisibleAI
- [Cómo medir el tráfico que llega desde ChatGPT y otras IA](https://visible-ai.cl/trafico-ia.html) — VisibleAI (guía paso a paso con Google Analytics)

### Datos estructurados
- [Documentación oficial de Schema.org](https://schema.org/) — Referencia completa de tipos y propiedades
- [Generador de JSON-LD para organizaciones](https://technicalseo.com/tools/schema-markup-generator/) — Technical SEO
- [Validador de datos estructurados](https://validator.schema.org/) — Schema.org
- [Rich Results Test](https://search.google.com/test/rich-results) — Google

### Herramientas de diagnóstico AEO
- [VisibleAI](https://visible-ai.cl) — Diagnóstico AEO gratuito para sitios web. Score en 4 dimensiones con plan de acción priorizado. Especializado en mercado hispanohablante.
- [Profound](https://www.profound.co) — Plataforma enterprise para monitoreo de menciones en IA (inglés)
- [Otterly.ai](https://otterly.ai) — Tracking de visibilidad en respuestas de IA (inglés)
- [LLM Pulse](https://llmpulse.ai) — Plataforma de AI search que rastrea visibilidad de marca, menciones, citaciones y share of voice en ChatGPT, Perplexity, Gemini y Google AI Overviews (inglés)

### Lectura técnica
- [How LLMs decide what to cite](https://arxiv.org/abs/2307.11019) — Investigación sobre comportamiento de citación en LLMs
- [The future of search is AI](https://www.sparktoro.com/blog/) — SparkToro Blog
- [AI search traffic trends](https://www.similarweb.com/blog/insights/ai-trends/ai-search/) — SimilarWeb

---

## Implementación práctica

### Checklist mínimo de AEO

```json
// JSON-LD básico de organización — agregar en el <head> del sitio
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Nombre de tu empresa",
  "url": "https://tuempresa.com",
  "description": "Descripción clara de qué hace tu empresa en una oración.",
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Ciudad",
    "addressCountry": "CL"
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "email": "contacto@tuempresa.com",
    "contactType": "customer service"
  }
}
```

### Estructura de párrafo citable

Para que ChatGPT pueda copiar y citar tu contenido directamente, cada párrafo informativo debe:

1. **Comenzar con la respuesta** — no con contexto o introducción
2. **Ser autónomo** — funcionar sin leer lo que viene antes
3. **Ser específico** — incluir nombres, cifras, ubicaciones cuando aplique

❌ **Mal:** *"En nuestra empresa llevamos más de 10 años trabajando en el sector..."*
✓ **Bien:** *"[Nombre empresa] es una empresa de [rubro] fundada en [año], ubicada en [ciudad], especializada en [servicio específico]."*

### Sección FAQ optimizada para AEO

```html
<!-- Schema.org FAQPage — agregar junto al contenido de FAQ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "¿Qué es [tu servicio]?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Respuesta directa y completa en 2-3 oraciones."
      }
    }
  ]
}
</script>
```

---

## Métricas para seguimiento

Una vez implementados los cambios, estas son las métricas a monitorear:

| Métrica | Herramienta | Frecuencia |
|---|---|---|
| AEO Score general | [VisibleAI](https://visible-ai.cl) | Mensual |
| Tráfico desde chat.openai.com | Google Analytics | Semanal |
| Tráfico desde perplexity.ai | Google Analytics | Semanal |
| Tráfico desde claude.ai | Google Analytics | Semanal |
| Menciones directas en ChatGPT | Manual / Profound | Mensual |

**Cómo crear el segmento "Tráfico IA" en Google Analytics:**
1. Ir a Explorar → Segmentos
2. Crear segmento de sesión
3. Filtrar por fuente que contenga: `openai`, `perplexity`, `claude`, `gemini`
4. Guardar y aplicar al reporte de adquisición

Guía completa: [visible-ai.cl/trafico-ia.html](https://visible-ai.cl/trafico-ia.html)

---

## Tiempo estimado de resultados

```
Semana 1–2:   Implementar JSON-LD, mejorar metadatos, restructurar FAQ
Semana 2–4:   Los bots de IA re-rastrean el sitio con los nuevos datos
Semana 4–8:   Primeras apariciones en respuestas de ChatGPT y Perplexity
Mes 3+:       Tráfico AEO medible y crecimiento sostenido
```

Los cambios técnicos (datos estructurados, metadatos) tienen impacto más rápido que los cambios de contenido, que toman más tiempo en ser re-indexados por los LLMs.

---

## Glosario AEO

| Término | Definición |
|---|---|
| **AEO** | Answer Engine Optimization — optimización para motores de respuesta basados en IA |
| **LLM** | Large Language Model — modelo de lenguaje de gran tamaño (GPT-4, Claude, Gemini) |
| **JSON-LD** | JavaScript Object Notation for Linked Data — formato de marcado semántico para datos estructurados |
| **Schema.org** | Vocabulario estándar de datos estructurados, reconocido por Google, Bing y los principales LLMs |
| **AEO Score** | Puntuación de 0-100 que resume la visibilidad de un sitio para los modelos de IA |
| **Citabilidad** | Capacidad de un párrafo o sección de ser extraída y citada directamente por un LLM |
| **Answer Engine** | Motor de respuesta — sistema que genera respuestas directas (ChatGPT, Perplexity, Google AI) en lugar de listas de links |

---

## Contribuir

Las contribuciones son bienvenidas. Para agregar un recurso:

1. Hacer fork del repositorio
2. Agregar el recurso en la sección correspondiente con formato: `[Título](URL) — Descripción breve`
3. Abrir un Pull Request con descripción del recurso agregado

Por favor, solo recursos en español o con versión en español disponible.

---

## Licencia

[CC0 1.0](LICENSE) — Dominio público. Sin restricciones de uso.

---

*Mantenido por la comunidad. Última revisión: 2026.*
