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

                echo 'Ejecutando escaneo con límites de CPU...'
                        sh '''
                        docker run --rm -u root --network host \
                        --cpus="0.5" \
                        -v $(pwd):/zap/wrk/:rw \
                        -t zaproxy/zap-stable \
                        zap-baseline.py -t http://app_test:5000 -r zap_report.html || true
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
                echo 'Sincronizando con el repositorio...'
                withCredentials([usernamePassword(credentialsId: 'GIT-TOKEN', passwordVariable: 'GIT_PASSWORD', usernameVariable: 'GIT_USER')]) {
                    sh '''
                    # 1. Asegurar limpieza
                    rm -fr .git/rebase-merge || true
                    git config user.name "Jenkins Automator"
                    git config user.email "jenkins@local"
                    
                    # 2. Sincronizar ANTES de generar archivos
                    git fetch origin main
                    git reset --hard origin/main
                    
                    # 3. AHORA generamos los archivos nuevos
                    date > build_timestamp.txt
                    
                    # 4. Añadimos y commiteamos
                    git add .
                    # Comprobamos si hay cambios reales antes de commitear
                    if ! git diff-index --quiet HEAD --; then
                        git commit -m "docs/sec: Actualización automática [skip ci]"
                        git push https://${GIT_USER}:${GIT_PASSWORD}@github.com/diegoparra-git/prueba-jenkins.git HEAD:main
                    else
                        echo "No hay cambios nuevos, saltando commit."
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