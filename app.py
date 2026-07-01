from flask import Flask, request, render_template_string
from prometheus_client import make_wsgi_app, Counter
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from markupsafe import escape

app = Flask(__name__)

# Métrica para Prometheus y Grafana
REQUESTS = Counter('http_requests_total', 'Total de peticiones HTTP')

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
        <h2>Buscador de Registros</h2>
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
@app.route('/')
def home():
    REQUESTS.inc()
    return render_template_string(HTML_TEMPLATE, result="")

## @brief Ruta de búsqueda (VULNERABLE A XSS).
#  @details Recibe un parámetro 'q' por URL y lo refleja directamente en el HTML sin sanitizar, permitiendo inyección de scripts.
@app.route('/buscar')
def buscar():
    REQUESTS.inc()
    # Capturamos lo que el usuario escribió
    query = request.args.get('q', '')
    
    # VULNERABILIDAD: Reflejamos el input directamente concatenado
    mensaje = f"Resultados para la búsqueda: <b>{query}</b>" 
    
    return render_template_string(HTML_TEMPLATE, result=mensaje)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)