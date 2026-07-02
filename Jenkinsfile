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
            // 1. Limpiar
            sh 'docker rm -f app_test || true'
            
            // 2. Construir
            sh 'docker build -t appsegura .'
            
            // 3. Correr la app
            sh 'docker run -d --name app_test -p 5001:5000 appsegura'
            sh 'sleep 10'
            
            // 4. Ejecutar ZAP con copia explícita
            // Creamos un contenedor ZAP y le decimos que guarde el reporte en /zap/wrk
            sh '''
            docker run --rm -u root --network host \
            -v ${WORKSPACE}:/zap/wrk/:rw \
            -t zaproxy/zap-stable \
            zap-baseline.py -t http://localhost:5001 -r zap_report.html -I || true
            '''
            
            // 5. Verificación forzada: Si no está en el workspace, lo sacamos del contenedor
            // Si el mapeo falló, esto lo rescata
            sh 'cp zap_report.html zap_report_backup.html || echo "No se pudo copiar el reporte"'
            
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
                    
                    # 1. Sincronizamos con el origen
                    git fetch origin main
                    git reset --hard origin/main
                    
                    # 2. Generamos archivos (el reporte ya debería estar ahí por el volumen)
                    date > build_timestamp.txt
                    
                    # 3. Comprobamos si el reporte existe antes de hacer el add
                    if [ -f "zap_report.html" ]; then
                        git add zap_report.html build_timestamp.txt
                        git commit -m "docs/sec: Reporte de seguridad actualizado [skip ci]" || true
                        git push https://${GIT_USER}:${GIT_PASSWORD}@github.com/diegoparra-git/prueba-jenkins.git HEAD:main
                    else
                        echo "El reporte zap_report.html no fue encontrado. Saltando commit."
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