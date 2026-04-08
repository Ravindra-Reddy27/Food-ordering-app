pipeline {
    agent any

    // Define your environment variables here
    environment {
        EC2_IP = '35.172.183.168' // Replace with your EC2 Public IPv4 address
        SONAR_TOKEN = 'squ_2867fd2e20f2b2bfe0a31a1a4550fc19c2d82849' // Your token
        SONAR_IP = 'http://192.168.56.1:9000' // Your Windows IP address
    }

    stages {
        stage('Spin Up Test Environment') {
            steps {
                echo 'Starting Docker containers for testing...'
                // 1. Clean up Jenkins' own workspace
                powershell 'docker-compose down' 
                
                // 2. THE FIX: Forcefully kill any stray ghost containers from manual testing
                // The '; exit 0' ensures the pipeline keeps going even if the containers don't exist
                powershell 'docker rm -f food_app_db food_app_backend food_app_frontend; exit 0'
                
                // 3. Now it is safe to spin them up
                powershell 'docker-compose up -d db backend'
                
                // Give the database a few seconds to fully boot up
                sleep time: 15, unit: 'SECONDS' 
            }
        }

        stage('Run Tests & Coverage') {
            steps {
                echo 'Running pytest and generating coverage.xml...'
                powershell 'docker exec food_app_backend pytest --cov=. --cov-report=xml'
                
                echo 'Extracting coverage file to Windows host...'
                powershell 'docker cp food_app_backend:/app/coverage.xml ./backend/coverage.xml'
                
                echo 'Fixing file paths for SonarScanner...'
                powershell "(Get-Content .\\backend\\coverage.xml) -replace '<source>/app</source>', '<source>/usr/src/backend</source>' -replace 'filename=\"', 'filename=\"backend/' | Set-Content .\\backend\\coverage.xml"
            }
        }

        stage('SonarQube Analysis') {
            steps {
                echo 'Scanning code with SonarQube...'
                powershell """
                docker run --rm -v "${env.WORKSPACE}:/usr/src" sonarsource/sonar-scanner-cli `
                "-Dsonar.token=${env.SONAR_TOKEN}" `
                "-Dsonar.host.url=${env.SONAR_IP}"
                """
            }
        }

        stage('Clean Up Local Environment') {
            steps {
                echo 'Tearing down local test containers...'
                powershell 'docker-compose down'
            }
        }

        stage('Deploy to EC2') {
            steps {
                echo 'Deploying application to AWS EC2...'
                
                withCredentials([sshUserPrivateKey(credentialsId: 'ec2-ssh-key', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
                    powershell """
                    \$target = "\$env:SSH_USER@${env.EC2_IP}"
                    
                    echo "Creating directory on EC2..."
                    ssh -o StrictHostKeyChecking=no -i "\$env:SSH_KEY" \$target "mkdir -p ~/food-booking-app"
                    
                    echo "Securely copying files to EC2..."
                    scp -r -o StrictHostKeyChecking=no -i "\$env:SSH_KEY" ./* "\$target`:~/food-booking-app/"
                    
                    echo "Spinning up production containers on EC2..."
                    ssh -o StrictHostKeyChecking=no -i "\$env:SSH_KEY" \$target "cd ~/food-booking-app && sudo docker-compose down && sudo docker-compose up -d --build"
                    """
                }
            }
        }
    }
}