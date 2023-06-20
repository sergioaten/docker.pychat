pipeline {
    agent {
        label "agent"; 
    }

    environment {
        BRANCH_NAME = "${GIT_BRANCH.split("/")[1]}" //Split branch name from origin/branchname
        msteams_webhook = credentials('msteams-webhook-test') //MS Teams webhook
        dev_credentials = credentials('gcp-cloudrun-json') //Load dev credentials
        prod_credentials = credentials('gcp-cloudrun-json') //Load prod credentials
        region = 'us-central1' //Google Cloud Region
        artifact_registry = "${region}-docker.pkg.dev" //Artifact Registry URL
        service_name = 'pychat' //Service name
        repo = 'jenkins-repo' //Artifact Registry repo
        test_path_url = '/' //Url with "/" - example -> /test
    }

    stages {
        stage('Preparing environment') {
            steps {
                script {
                    if (env.BRANCH_NAME == "dev") {
                        echo "Loading dev environment credentials."
                        env.GOOGLE_APPLICATION_CREDENTIALS = env.dev_credentials
                        env.app_serviceaccount = "pychat@jenkins-project-388812.iam.gserviceaccount.com"
                    } else if (env.BRANCH_NAME == "main") {
                        echo "Loading production environment credentials."
                        env.GOOGLE_APPLICATION_CREDENTIALS = env.prod_credentials 
                        env.app_serviceaccount = "pychat@jenkins-project-388812.iam.gserviceaccount.com"    
                    } else {
                        error "Invalid branch name. Only 'main' or 'dev' are allowed."
                    }
                    env.project_id = sh(
                        'jq -r ".project_id" $GOOGLE_APPLICATION_CREDENTIALS',
                        returnStdout: true
                    ).trim()
                    env.dockerimg_name = "${artifact_registry}/${project_id}/${repo}/${service_name}:${GIT_COMMIT}"
                    env.service_account_email = sh(
                        'jq -r ".client_email" $GOOGLE_APPLICATION_CREDENTIALS',
                        returnStdout: true
                    ).trim()
                    sh(
                        'gcloud auth activate-service-account \
                        --key-file=$GOOGLE_APPLICATION_CREDENTIALS'
                    )
                    sh(
                        "gcloud config set account ${service_account_email}",
                        returnStdout: true
                    )
                }
            }
        }
        
        stage('Checking requirements') {
            steps {
                sh 'echo Checking if Docker is installed on the machine'
                sh 'docker version'
                sh 'echo Installing Python dependencies'
                sh 'python3 -m pip install -r requirements.txt'
            }
        }

        stage('Building artifact') {
            steps {
                sh 'echo Building Docker image'
                sh 'docker build . -t ${env.dockerimg_name}'
                script {
                    echo "Getting the port used by the image for deployment"
                    env.port = sh(
                        script: "docker inspect \
                                --format='{{range \$p, \$conf := .Config.ExposedPorts}} {{\$p}} {{end}}' ${env.dockerimg_name} \
                                | grep -oE '[0-9]+'",
                        returnStdout: true
                    )
                }
            }
        }

        stage('Upload artifact to repo') {
            steps {
                sh 'echo Uploading Docker image to Google Cloud "Artifact Registry"'
                sh 'gcloud auth configure-docker ${env.artifact_registry} --quiet'
                sh 'docker push ${env.dockerimg_name}'
            }
        }

        stage('Deploying application') {
            steps {
                sh 'echo Checking if the application is already running to update the image version, otherwise, deploying to Cloud Run.'
                script {
                    def containerRunning = sh(
                        script: "gcloud run services describe ${env.service_name} \
                                --format='value(status.url)' \
                                --region='us-central1' \
                                --project='${env.project_id}'",
                        returnStatus: true
                        ) == 0
                    if (containerRunning) {
                        echo "The container is running. Updating the image."
                        sh("gcloud run services update ${env.service_name} \
                            --image='${env.dockerimg_name}' \
                            --region='${env.region}' \
                            --port='${env.port}' \
                            --project='${env.project_id}' \
                            --service-account='${env.app_serviceaccount}'")
                        sh("gcloud run services update-traffic ${env.service_name} \
                        --to-latest \
                        --region='${env.region}'")
                        env.application_status = "Updating"
                    } else {
                        echo "The container is not running. Deploying the service."
                        sh("gcloud run deploy ${env.service_name} \
                            --image='${env.dockerimg_name}' \
                            --region='${env.region}' \
                            --port=${env.port} \
                            --project='${env.project_id}' \
                            --service-account='${env.app_serviceaccount}'")
                        sh("gcloud run services update-traffic ${env.service_name} \
                        --to-latest \
                        --region='${env.region}'")
                        env.application_status = "Creating"
                    }
                    sh 'echo Publishing the Cloud Run service for all users'
                    sh 'gcloud run services add-iam-policy-binding ${service_name} \
                        --member="allUsers" \
                        --role="roles/run.invoker" \
                        --region="${region}" \
                        --project="${project_id}"'
                    sh 'echo Performing test on the deployed application'
                    env.url = sh(
                        script: "gcloud run services describe ${env.service_name} \
                                --format='value(status.url)' \
                                --region='${env.region}' \
                                --project='${env.project_id}'",
                        returnStdout: true
                    ).trim()
                    env.responseCode = sh(
                        script: "curl -s -o /dev/null \
                                -w '%{http_code}' ${env.url}${env.test_path_url}", 
                        returnStdout: true
                    )
                    if (env.responseCode == null) {
                        env.response_msg = 'Error: Null'
                        error('El valor de responseCode es null. Ocurrió un error en la llamada a curl.')
                    } else {
                        env.response_msg = env.responseCode
                        if (responseCode.matches('^2.*$')) {
                            echo "The test passed. The response is ${env.responseCode} OK."
                        } else {
                            try {
                                error "The test failed. The response is ${env.responseCode} FAIL."
                            } catch (Exception e) {
                                echo "Error caught: ${e.message}"
                            }

                            def last_revision = sh(
                                script: "gcloud run revisions list \
                                        --service='${env.service_name}' \
                                        --format='value(metadata.name)' \
                                        --limit=2 \
                                        --region='${env.region}' \
                                        | tail -n 1",
                                returnStdout: true
                            )
                            sh("gcloud run services update-traffic '${env.service_name}' \
                                --to-revisions='${env.last_revision}' \
                                --region='${env.region}'")
                        }
                    }
                } 
            }
        }
    }

    post {
        success {
            office365ConnectorSend webhookUrl: msteams_webhook,
            message: "Job completed!",
            factDefinitions: [
                [name: "Job Name", template: env.JOB_NAME],
                [name: "Build Number", template: env.BUILD_NUMBER],
                [name: "Build URL", template: env.BUILD_URL],
                [name: "Artifact", template: env.dockerimg_name],
                [name: "Response Code", template: env.response_msg],
                [name: "Application Status", template: env.application_status],
                [name: "Application URL", template: env.url],
                [name: "Git Repository", template: env.GIT_URL],
                [name: "Git Commit", template: env.GIT_COMMIT]
            ],
            status: "Success",
            color: "#00FF00"
        }

        failure {
            office365ConnectorSend webhookUrl: msteams_webhook,
            message: "Job error!",
            factDefinitions: [
                [name: "Job Name", template: env.JOB_NAME],
                [name: "Build Number", template: env.BUILD_NUMBER],
                [name: "Build URL", template: env.BUILD_URL],
                [name: "Artifact", template: env.dockerimg_name],
                [name: "Response Code", template: env.response_msg],
                [name: "Application Status", template: env.application_status],
                [name: "Git Repository", template: env.GIT_URL],
                [name: "Git Commit", template: env.GIT_COMMIT]
            ],
            status: "Error",
            color: "#FF0000"
        }
    }

}