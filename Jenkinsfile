pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Compilando/Preparando el código fuente...'
                bat 'echo Código preparado con éxito'
            }
        }
        stage('Test') {
            steps {
                echo 'Ejecutando pruebas unitarias...'
                bat 'echo Pruebas unitarias pasadas correctamente (Simulado)'
            }
        }
        stage('Deploy') {
            steps {
                echo 'Desplegando la aplicación en el entorno de prueba...'
                bat 'echo Despliegue exitoso!'
            }
        }
    }
}