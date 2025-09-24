#!groovy
@Library('jenkins-libraries') _

pipeline {
    agent {
        node { label 'jenkins-node-label-1' }
    }

    environment {
        PROJECT_NAME = 'fed-mgr'
        DOCKERFILE = './docker/Dockerfile'
    }

    triggers {
        cron("${dockerRepository.periodicTrigger(env.BRANCH_NAME)}")
    }
    
    stages {
        stage('Create and push images') {
            parallel {
                stage('Image with python 3.11 published on Harbor') {
                    steps {
                        script {
                            dockerRepository.buildAndPushImage(
                                imageName: "${PROJECT_NAME}",
                                dockerfile: "${DOCKERFILE}",
                                registryType: 'harbor2',
                                pythonVersion: '3.11'
                            )
                        }
                    }
                }
                stage('Image with python 3.12 published on Harbor') {
                    steps {
                        script {
                            dockerRepository.buildAndPushImage(
                                imageName: "${PROJECT_NAME}",
                                dockerfile: "${DOCKERFILE}",
                                registryType: 'harbor2',
                                pythonVersion: '3.12'
                            )
                        }
                    }
                }
                stage('Image with python 3.13 published on Harbor') {
                    steps {
                        script {
                            dockerRepository.buildAndPushImage(
                                imageName: "${PROJECT_NAME}",
                                dockerfile: "${DOCKERFILE}",
                                registryType: 'harbor2',
                                pythonVersion: '3.13'
                            )
                        }
                    }
                }
                stage('Image with python 3.11 published on DockerHub') {
                    steps {
                        script {
                            dockerRepository.buildAndPushImage(
                                imageName: "${PROJECT_NAME}",
                                dockerfile: "${DOCKERFILE}",
                                registryType: 'dockerhub',
                                pythonVersion: '3.11'
                            )
                        }
                    }
                }
                stage('Image with python 3.12 published on DockerHub') {
                    steps {
                        script {
                            dockerRepository.buildAndPushImage(
                                imageName: "${PROJECT_NAME}",
                                dockerfile: "${DOCKERFILE}",
                                registryType: 'dockerhub',
                                pythonVersion: '3.12'
                            )
                        }
                    }
                }
                stage('Image with python 3.13 published on DockerHub') {
                    steps {
                        script {
                            dockerRepository.buildAndPushImage(
                                imageName: "${PROJECT_NAME}",
                                dockerfile: "${DOCKERFILE}",
                                registryType: 'dockerhub',
                                pythonVersion: '3.13'
                            )
                        }
                    }
                }
            }
        }
    }
}
