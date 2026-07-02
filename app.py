## @package app
#  Aplicación Flask vulnerable para fines educativos de DevSecOps.
#  Incluye métricas de Prometheus y rutas de búsqueda.
from flask import Flask, request, render_template_string
from prometheus_client import make_wsgi_app, Counter
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from markupsafe import escape
import requests
from datetime import datetime

app = Flask(__name__)

## @brief Contador global de peticiones HTTP.
#  Se utiliza para exportar métricas hacia Prometheus. Contador de peticiones HTTP para Prometheus y Grafana
REQUEST_COUNTER = Counter('flask_app_requests_total', 'Total de peticiones HTTP a la aplicación')

ELASTICSEARCH_URL = 'http://host.docker.internal:9200/flask-logs/_doc' # NOSONAR

def log_to_elastic(level, message, endpoint):
    log_data = {
        "@timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
        "endpoint": endpoint,
        "app": "flask_appsegura"
    }
    try:
        requests.post(ELASTICSEARCH_URL, json=log_data, timeout=2)
    except Exception as e:
        print(f"Error enviando log: {e}")


# Middleware para exponer métricas en /metrics
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Buscador DevSecOps</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 40px; }
        .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 500px; margin: auto; text-align: center; }
        input[type=text] { padding: 10px; width: 70%; border: 1px solid #ccc; border-radius: 4px; }
        input[type=submit] { padding: 10px 20px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Buscador de Registros Anormales</h2>
        <form action="/buscar" method="GET">
            <input type="text" name="q" placeholder="Ingresa tu búsqueda..." required>
            <input type="submit" value="Buscar">
        </form>
        <p style="color: #555; margin-top: 20px;"><i>{{ result | safe }}</i></p>
    </div>
</body>
</html>
"""



## @brief Ruta principal de la aplicación.
#  @details Incrementa la métrica de Prometheus y renderiza la interfaz principal vacía.
#  @return Una cadena HTML renderizada con un buscador.
@app.route('/')
def home():
    REQUEST_COUNTER.inc()
    return render_template_string(HTML_TEMPLATE, result="")

## @brief Ruta de búsqueda (VULNERABLE A XSS).
#  @details Recibe un parámetro 'q' por URL y lo refleja directamente en el HTML.
#  @warning Esta función es vulnerable a Cross-Site Scripting (XSS) ya que refleja 
#           la entrada del usuario directamente sin sanitizar.
#  @param q El término de búsqueda ingresado por el usuario.
#  @return Renderiza la plantilla con el resultado de la búsqueda.
@app.route('/buscar')
def buscar():
    REQUEST_COUNTER.inc()
    # Capturamos lo que el usuario escribió
    query = request.args.get('q', '')
    log_to_elastic("INFO", f"Usuario buscó el término: {query}", "/buscar")
    # VULNERABILIDAD: Reflejamos el input directamente concatenado
    mensaje = f"Resultados para la búsqueda: <b>{query}</b>" 
    
    return render_template_string(HTML_TEMPLATE, result=mensaje)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)