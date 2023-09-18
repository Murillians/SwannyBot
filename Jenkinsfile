pipeline {
    agent any
    stages {
      stage('prepare files') {
        steps {
          /*sh "> swannybot.db"
          withCredentials([file(credentialsId: 'swannybotdb', variable: 'SECRET')]) {
            sh('cp \$SECRET ./swannybot.db')
          }*/
          sh "> swannybottokens.py"
          withCredentials([file(credentialsId: 'swannybottokens', variable: 'SECRET')]) {
            sh('cp \$SECRET ./swannybottokens.py')
          }
          sh "> special_cog.py"
          withCredentials([file(credentialsId: 'special_cog', variable: 'SECRET')]) {
            sh('cp \$SECRET ./special_cog.py')
          }
          sh "> ./wavelink/application.yml"
          withCredentials([file(credentialsId: 'applicationyml', variable: 'SECRET')]) {
            sh('cp \$SECRET ./wavelink/application.yml')
          }
      }
      }
        stage('Build docker image'){
            steps{
                sh 'docker build -t reggie:5000/swannybot:dev .'
                echo 'Build Image Completed'
                sh 'docker push reggie:5000/swannybot:dev'
                echo 'Push Image Completed'
            }
      }
  }
}