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
                echo 'Limpiando contenedores previos...'
                // -f fuerza el borrado, || true evita error si no existe
                sh 'docker rm -f app_test || true' 

                echo 'Levantando la aplicación temporal...'
                sh 'docker build -t appsegura .'
                sh 'docker run -d --name app_test -p 5001:5000 appsegura'

                echo 'Esperando 10 segundos a que Flask inicie...'
                sh 'sleep 10'

                echo 'Ejecutando escaneo con OWASP ZAP...'
                sh '''
                docker run --rm -u root --network host \
                -v $WORKSPACE:/zap/wrk/:rw \
                -t zaproxy/zap-stable \
                zap-baseline.py -t http://localhost:5001 -r zap_report.html || true
                '''

                echo 'Apagando entorno temporal de pruebas...'
                sh 'docker rm -f app_test || true'
            }
        }
        
        stage('Generate Documentation') { 
            // ETAPA: Generación de documentación
            steps {
                echo 'Generando documentación técnica automatizada...'
                sh 'doxygen Doxyfile' 
            }
        }
        
        stage('Version Control') {
            steps {
                echo 'Generando archivo de marca de tiempo...'
                sh 'date > build_timestamp.txt'

                withCredentials([usernamePassword(credentialsId: 'GIT-TOKEN', passwordVariable: 'GIT_PASSWORD', usernameVariable: 'GIT_USER')]) {
                    sh '''
                    git config user.name "Jenkins Automator"
                    git config user.email "jenkins@local"
                    git add .
                    git commit -m "docs/sec: Actualización automática del pipeline" || echo "No hay cambios para commitear"
                    git push https://${GIT_USER}:${GIT_PASSWORD}@github.com/diegoparra-git/prueba-jenkins.git HEAD:main
                    '''
                }
            }
        }
        
        stage('Deploy') {
            steps {
                echo 'Desplegando la aplicación...'
                // -f fuerza el borrado y || true evita que el pipeline se detenga si no existe
                sh 'docker rm -f appsegura || true' 
                sh 'docker run -d --name appsegura -p 5002:5000 appsegura'
            }
        }
    }
}