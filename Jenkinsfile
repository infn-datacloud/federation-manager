#!groovy
@Library('jenkins-libraries') _

pipeline {
    agent {
        node {
            label 'jenkins-node-label-1'
        }
    }

    environment {
        PROJECT_NAME = 'fed-mgr'
        DOCKERFILE = './docker/Dockerfile'
        SRC_DIR = 'fed_mgr'
        TESTS_DIR = 'tests'
        POETRY_VERSION = '2.1'
        TARGET_PYTHON = '3.13'
    }

    triggers {
        cron("${myCron.periodicTrigger(env.BRANCH_NAME)}")
    }

    stages {
        stage('Linting and format') {
            agent {
                docker {
                    label 'jenkins-node-label-1'
                    image "python:${env.TARGET_PYTHON}"
                    args '-u root:root'
                    reuseNode true
                }
            }
            when {
                expression { return env.CHANGE_ID != null || env.BRANCH_NAME == 'main' } // It is a PR or main branch
            }
            steps {
                script {
                    ruffChecks(env.SRC_DIR)
                }
            }
        }
        stage('Tests execution') {
            matrix {
                axes {
                    axis {
                        name 'PYTHON_VERSION'
                        values '3.12', '3.13'
                    }
                }
                stages {
                    stage('Test'){
                        agent {
                            docker {
                                label 'jenkins-node-label-1'
                                image "python:${env.PYTHON_VERSION}"
                                args '-u root:root'
                                reuseNode true
                            }
                        }
                        stages{
                            stage('Install dependencies') {
                                steps {
                                    script  {
                                        installDependencies(env.PYTHON_VERSION, env.POETRY_VERSION)
                                    }
                                }
                            }
                            stage('Run Tests') {
                                steps {
                                    script {
                                        runTests(env.SRC_DIR, env.PYTHON_VERSION)
                                    }
                                }
                                post {
                                    always {
                                        script {
                                            archiveArtifacts artifacts: 'coverage-reports/**/*', fingerprint: true
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        stage('Combine coverages') {
            agent {
                docker {
                    label 'jenkins-node-label-1'
                    image "python:${env.TARGET_PYTHON}"
                    args '-u root:root'
                    reuseNode true
                }
            }
            steps {
                script {
                    combineCovReports()
                }
            }
            post {
                success {
                    script {
                        archiveArtifacts artifacts: 'coverage.xml', fingerprint: true
                    }
                }
            }
        }
        stage('Notify SonarCloud') {
            agent {
                docker {
                    label 'jenkins-node-label-1'
                    image 'sonarsource/sonar-scanner-cli'
                    args "-u root:root -v ${env.WORKSPACE}:/usr/src"
                    reuseNode true
                }
            }
            steps {
                script {
                    notifySonar(env.PROJECT_NAME, env.SRC_DIR, env.TESTS_DIR, env.TARGET_PYTHON)
                }
            }
        }
        stage('Build images') {
            when {
                allOf {
                    expression { return currentBuild.currentResult != 'UNSTABLE' }
                    expression { return currentBuild.result != 'UNSTABLE' }
                    expression { return env.CHANGE_ID != null || env.TAG_NAME != null || env.BRANCH_NAME == 'main' } // It is a PR or tag or main branch
                }
            }
            matrix {
                axes {
                    axis {
                        name 'PYTHON_VERSION'
                        values '3.12', '3.13'
                    }
                }
                stages {
                    stage('Build') {
                        steps {
                            script {
                                buildDockerImage(env.PROJECT_NAME, env.PYTHON_VERSION, env.POETRY_VERSION)
                            }
                        }
                    }
                }
            }
        }
        stage('Push images') {
            when {
                allOf {
                    expression { return currentBuild.currentResult != 'UNSTABLE' }
                    expression { return currentBuild.result != 'UNSTABLE' }
                    expression { return env.CHANGE_ID != null || env.TAG_NAME != null || env.BRANCH_NAME == 'main' } // It is a PR or tag or main branch
                }
            }
            matrix {
                axes {
                    axis {
                        name 'PYTHON_VERSION'
                        values '3.12', '3.13'
                    }
                    axis {
                        name 'DOCKER_REGISTRY'
                        values 'harbor2', 'dockerhub'
                    }
                }
                stages {
                    stage('Push') {
                        steps {
                            script {
                                pushDockerImage(
                                    env.PROJECT_NAME,
                                    env.DOCKER_REGISTRY,
                                    env.PYTHON_VERSION,
                                    env.PYTHON_VERSION == env.TARGET_PYTHON
                                )
                            }
                        }
                    }
                }
            }
        }
        stage('Update docker description') {
            when {
                allOf {
                    expression { return currentBuild.currentResult != 'UNSTABLE' }
                    expression { return currentBuild.result != 'UNSTABLE' }
                    expression { return env.CHANGE_ID != null || env.TAG_NAME != null || env.BRANCH_NAME == 'main' } // It is a PR or tag or main branch
                }
            }
            matrix {
                axes {
                    axis {
                        name 'DOCKER_REGISTRY'
                        values 'harbor2', 'dockerhub'
                    }
                }
                stages {
                    stage('Update description') {
                        steps {
                            script {
                                updateDockerRegistryDoc(env.PROJECT_NAME, env.DOCKER_REGISTRY)
                            }
                        }
                    }
                }
            }
        }
    }
    post {
        always {
            echo 'Cleaning up Docker images...'
            sh 'docker system prune -af || true'
        }
    }
}
