pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Compilando/Preparando el código fuente...'
                bat 'python --version'
            }
        }
        stage('Test') {
            steps {
                echo 'Ejecutando pruebas unitarias...'
                bat 'python test_hello.py'
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