pipeline {
    agent any
    stages {
      stage('prepare files') {
        steps {
          sh "> swannybot.db"
          withCredentials([file(credentialsId: 'swannybotdb', variable: 'SECRET')]) {
            sh('echo ${SECRET} > ./swannybot.db')
          }
          sh "> swannybottokens.py"
          withCredentials([file(credentialsId: 'swannybottokens', variable: 'SECRET')]) {
            sh('echo ${SECRET} > ./swannybottokens.py')
          }
          sh "> special_cog.py"
          withCredentials([file(credentialsId: 'special_cog', variable: 'SECRET')]) {
            sh('echo ${SECRET} > ./special_cog.py')
          }
          sh "> ./wavelink/application.yml"
          withCredentials([file(credentialsId: 'swannybotdb', variable: 'SECRET')]) {
            sh('echo ${SECRET} > ./wavelink/application.yml')
          }
          sh "> ./wavelink/Lavalink.jar"
          withCredentials([file(credentialsId: 'Lavalink', variable: 'SECRET')]) {
            sh('echo ${SECRET} > ./wavelink/Lavalink.jar')
        }
      }
      }
        stage('Build docker image'){
            steps{
                sh 'docker build -t reggie:5000/swannybot .'
                echo 'Build Image Completed'
                sh 'docker push reggie:5000/swannybot'
                echo 'Push Image Completed'
            }
      }
  }
}