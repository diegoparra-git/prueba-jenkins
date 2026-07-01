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
            steps {
                echo 'Levantando la aplicación temporal...'
                sh 'docker run -d --name app_test -p 5001:5000 appsegura'

                echo 'Esperando 10 segundos a que Flask inicie...'
                sh 'sleep 10' // Pausa obligatoria

                echo 'Ejecutando escaneo con OWASP ZAP...'
                sh '''
                docker run --rm -u root --network host \
                -v $WORKSPACE:/zap/wrk/:rw \
                -t zaproxy/zap-stable \
                zap-baseline.py -t http://localhost:5001 -r zap_report.html || true
                '''
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
                        
                        git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/diegoparra-git/prueba-jenkins.git HEAD:main
                    '''
                }
            }
        }
        
        stage('Deploy') {
            steps {
                echo 'Desplegando la aplicación...'
                // -f fuerza el borrado y || true evita que el pipeline se detenga si no existe
                sh 'docker rm -f appsegura || true' 
                sh 'docker run -d --name appsegura -p 5000:5000 appsegura'
            }
        }
    }
}