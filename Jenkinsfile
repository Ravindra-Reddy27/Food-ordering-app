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
                
                // This block uses the SSH Agent plugin to securely connect to AWS
                sshagent(['ec2-ssh-key']) {
                    // 1. Disable strict host key checking so Jenkins doesn't freeze asking for a yes/no prompt
                    // 2. Create an app folder on EC2
                    // 3. Securely copy (scp) all your project files to the EC2 server
                    // 4. SSH into the server and run docker-compose up
                    powershell """
                    \$sshOpts = "-o StrictHostKeyChecking=no"
                    
                    ssh \$sshOpts ubuntu@${env.EC2_IP} "mkdir -p ~/food-booking-app"
                    
                    scp -r \$sshOpts ./* ubuntu@${env.EC2_IP}:~/food-booking-app/
                    
                    ssh \$sshOpts ubuntu@${env.EC2_IP} "cd ~/food-booking-app && docker-compose down && docker-compose up -d --build"
                    """
                }
            }
        }
    }
}