pipeline {
    agent { dockerfile true }
    stages {
      stage('prepare files') {
        steps {
          sh "> .swannybot.db"
          withCredentials([string(credentialsId: 'swannybotdb', variable: 'SECRET')]) {
            sh "echo ${SECRET} > .swannybot.db"
          }
          sh "> .swannybottokens.py"
          withCredentials([string(credentialsId: 'swannybottokens', variable: 'SECRET')]) {
            sh "echo ${SECRET} > .swannybottokens.py"
          }
          sh "> special_cog.py"
          withCredentials([string(credentialsId: 'specialcog', variable: 'SECRET')]) {
            sh "echo ${SECRET} > .special_cog.db"
          }
          sh "> ./wavelink/application.yml"
          withCredentials([string(credentialsId: 'swannybotdb', variable: 'SECRET')]) {
            sh "echo ${SECRET} > ./wavelink/application.yml"
          }
        }
      }
        stage('Test') {
            steps {
                sh 'node --version'
                sh 'svn --version'
            }
        }
    }
}