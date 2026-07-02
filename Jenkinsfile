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
                script {
                    sh 'docker rm -f app_test || true'
                    sh 'docker build -t appsegura .'
                    sh 'docker run -d --name app_test -p 5001:5000 appsegura'
                    sh 'sleep 10'
                    
                    echo 'Ejecutando escaneo con OWASP ZAP...'
                    sh '''
                    # 1. Permisos totales a la carpeta para que ZAP pueda escribir el reporte
                    chmod 777 .
                    
                    # 2. Corremos ZAP CON EL VOLUMEN OBLIGATORIO (-v)
                    docker run --rm -u root --network host \
                    -v $(pwd):/zap/wrk/:rw \
                    -t zaproxy/zap-stable \
                    zap-baseline.py -t http://localhost:5001 -r zap_report.html -I || true
                    
                    # 3. Restauramos los permisos normales
                    chmod 755 .
                    
                    # 4. Verificamos que se haya creado sin detener el pipeline si falla
                    ls -lh zap_report.html || true
                    '''
                    
                    sh 'docker rm -f app_test || true'
                }
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
                withCredentials([usernamePassword(credentialsId: 'GIT-TOKEN', passwordVariable: 'GIT_PASSWORD', usernameVariable: 'GIT_USER')]) {
                    sh '''
                    git config user.name "Jenkins Automator"
                    git config user.email "jenkins@local"
                    
                    git fetch origin main
                    git reset --hard origin/main
                    
                    date > build_timestamp.txt
                    
                    # Usamos la ruta completa del workspace para añadir el archivo
                    if [ -f "${WORKSPACE}/zap_report.html" ]; then
                        git add "${WORKSPACE}/zap_report.html" "${WORKSPACE}/build_timestamp.txt"
                        git commit -m "docs/sec: Reporte de seguridad actualizado [skip ci]" || true
                        git push https://${GIT_USER}:${GIT_PASSWORD}@github.com/diegoparra-git/prueba-jenkins.git HEAD:main
                    else
                        echo "¡ERROR! El reporte no existe en ${WORKSPACE}/zap_report.html"
                        exit 1
                    fi
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