#!groovy
@Library('jenkins-libraries') _

void runTests(String pythonVersion) {
    // Run in backgound a dockerized neo4j DB instance.
    // Install dependencies for the specified python version.
    // Run tests.
    script {
        pythonProject.testCode(
            pythonVersion: "${pythonVersion}",
            coveragercId: '.coveragerc',
            coverageDir: "${COVERAGE_DIR}",
        )
    }
}

pipeline {
    agent { label 'jenkins-node-label-1' }

    environment {
        COVERAGE_DIR = 'coverage-reports'
        SONAR_HOST = 'https://sonarcloud.io'
        SONAR_ORGANIZATION = 'infn-datacloud'
        SONAR_PROJECT = 'fed-mgr'
        SONAR_TOKEN = credentials('sonar-token')
    }

    stages {
        stage('Run tests on multiple python versions') {
            parallel {
                stage('Run tests on python3.12') {
                    steps {
                        runTests('3.12')
                    }
                }
            }
        }
    }
    post {
        always {
            script {
                sonar.analysis(
                    sonarToken: '${SONAR_TOKEN}',
                    sonarProject: "${SONAR_PROJECT}",
                    sonarOrganization: "${SONAR_ORGANIZATION}",
                    sonarHost: "${SONAR_HOST}",
                    coverageDir: "${COVERAGE_DIR}",
                    srcDir: 'fed-mgr',
                    testsDir: 'tests',
                    pythonVersions: '3.12'
                )
            }
        }
    }
}
