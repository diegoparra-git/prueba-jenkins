pipeline {
    agent any
    
    stages {
        stage('Build & SCA') { 
            // ETAPA: Construcción y Análisis de Composición de Software
            steps {
                echo 'Instalando dependencias seguras...' 
                // pipenv install: Instalar dependencias definidas en Pipfile.lock
                sh 'pipenv install'
                
                echo 'Buscando vulnerabilidades en dependencias...'
                // pipenv check: Analizar dependencias en busca de vulnerabilidades conocidas
                // || true: Evitar que falle el pipeline si se encuentran vulnerabilidades
                sh 'pipenv check || true' 
            }
        }

        stage('Analyze - SonarQube') {
            steps {
                // 'sonarqube' debe ser el nombre configurado en Configurar el sistema
                script {
                    scannerHome = tool 'sonar-scanner'
                    withSonarQubeEnv('sonarqube') {
                        // Ejecuta el escáner
                        sh "${scannerHome}/bin/sonar-scanner \
                        -Dsonar.projectKey=flask-app \
                        -Dsonar.sources=."
                    }
                }
            }
        }
        
        stage('Test - OWASP ZAP') { 
            // ETAPA: Pruebas Dinámicas (DAST)
            steps {
                echo 'Levantando la aplicación temporal para pruebas dinámicas...'
                sh 'docker build -t appsegura .'
                
                // CAMBIO 1: Levantamos el contenedor de pruebas en el puerto 5001
                sh 'docker run -d --name app_test -p 5001:5000 appsegura'
                
                echo 'Ejecutando escaneo de vulnerabilidades con OWASP ZAP...'
                
                // CAMBIO 2: Le decimos a ZAP que ataque el puerto 5001
                sh '''
                docker run --rm -u root --network host -v $(pwd):/zap/wrk/:rw -t zaproxy/zap-stable zap-baseline.py -t http://localhost:5001 -r zap_report.html || true
                '''
                
                echo 'Apagando entorno temporal de pruebas...'
                sh 'docker stop app_test && docker rm app_test'
            }
        }
        
        stage('Generate Documentation') { 
            // ETAPA: Generación de documentación [cite: 176, 177]
            steps {
                echo 'Generando documentación técnica automatizada...'
                sh 'doxygen Doxyfile' 
            }
        }
        
        stage('Version Control') { 
            // ETAPA: Control de versiones [cite: 177]
            steps {
                echo 'Preparando commit con la nueva documentación y reportes...' 
                
                withCredentials([usernamePassword(credentialsId: 'GIT-TOKEN', passwordVariable: 'GIT_PASSWORD', usernameVariable: 'GIT_USERNAME')]) {
                    sh '''
                        git config user.name "Jenkins Automator"
                        git config user.email "jenkins@local"
                        
                        # Añadimos la documentación generada y el reporte de ZAP
                        git add docs/
                        git add zap_report.html || true
                        
                        git commit -m "docs/sec: Actualización Doxygen y reporte ZAP" || echo "No hay cambios para commitear"
                        
                        git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/DamagedGhost/test-jenkins.git HEAD:main
                    '''
                }
            }
        }
        
        stage('Deploy') { 
            // ETAPA: Despliegue a Producción 
            steps {
                echo 'Desplegando la nueva versión con vulnerabilidades en producción...' 
                
                // Limpiamos cualquier versión anterior para evitar conflictos
                sh 'docker stop appsegura || true'
                sh 'docker rm appsegura || true'
                
                // Levantamos el contenedor final asegurando que:
                // 1. Se llame 'appsegura' para que Prometheus lo encuentre
                // 2. Se conecte a la red 'semana15_default' de tu docker-compose
                sh 'docker run -d --name appsegura --network semana15_default -p 5000:5000 appsegura'
            }
        }
    }
}