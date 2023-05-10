pipeline {
  agent {
    dockerfile true
  }
  stages {
    stage('prepare files') {
      steps {
        sh '> .swannybottokens.py'
        withCredentials(bindings: [string(credentialsId: 'swannybottokens', variable: 'SECRET')]) {
          sh "echo ${SECRET} > .swannybottokens.py"
        }

        sh '> special_cog.py'
        withCredentials(bindings: [string(credentialsId: 'specialcog', variable: 'SECRET')]) {
          sh "echo ${SECRET} > .special_cog.db"
        }

        sh '> ./wavelink/application.yml'
        withCredentials(bindings: [string(credentialsId: 'swannybotdb', variable: 'SECRET')]) {
          sh "echo ${SECRET} > ./wavelink/application.yml"
        }

        sh '> .swannybot.db'
        withCredentials(bindings: [string(credentialsId: 'swannybotdb', variable: 'SECRET')]) {
          sh "echo ${SECRET} > .swannybot.db"
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