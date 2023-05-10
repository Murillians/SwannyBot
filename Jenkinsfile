pipeline {
    agent { dockerfile true }
    stages {
      stage('prepare files') {
        steps {
          sh "> .swannybot.db"
          withCredentials([file(credentialsId: 'swannybotdb', variable: 'SECRET')]) {
            sh "echo ${SECRET} > ./swannybot.db"
          }
          sh "> .swannybottokens.py"
          withCredentials([file(credentialsId: 'swannybottokens', variable: 'SECRET')]) {
            sh "echo ${SECRET} > ./swannybottokens.py"
          }
          sh "> special_cog.py"
          withCredentials([file(credentialsId: 'special_cog', variable: 'SECRET')]) {
            sh "echo ${SECRET} > ./special_cog.py"
          }
          sh "> ./wavelink/application.yml"
          withCredentials([file(credentialsId: 'swannybotdb', variable: 'SECRET')]) {
            sh "echo ${SECRET} > ./wavelink/application.yml"
          }
        }
      }
  }
}