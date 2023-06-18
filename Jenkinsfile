pipeline {
    agent {
        label "agent"; 
    }
    environment {
        BRANCH_NAME = "${GIT_BRANCH.split("/")[1]}"
        dev_credentials = credentials('gcp-cloudrun-json') //Load dev credentials
        prod_credentials = credentials('gcp-cloudrun-json') //Load prod credentials
        application_credentials = credentials('gcp-pychat-json') 
        region = 'us-central1' //Google Cloud Region
        artifact_registry = "${region}-docker.pkg.dev" //Artifact Registry URL
        service_name = 'pychat' //Service name
        repo = 'jenkins-repo' //Artifact Registry repo
        test_path_url = '/' //Url with "/"
    }
    stages {
        stage('Preparing environment') {
            steps {
                script {
                    if (BRANCH_NAME == "dev") {
                        echo "Loading dev environment credentials."
                        env.GOOGLE_APPLICATION_CREDENTIALS = dev_credentials
                    } else if (BRANCH_NAME == "main") {
                        echo "Loading production environment credentials."
                        env.GOOGLE_APPLICATION_CREDENTIALS = prod_credentials     
                    } else {
                        error "Invalid branch name. Only 'main' or 'dev' are allowed."
                    }
                    env.project_id = sh(script: 'jq -r ".project_id" $GOOGLE_APPLICATION_CREDENTIALS', returnStdout: true).trim()
                    env.dockerimg_name = "${artifact_registry}/${project_id}/${repo}/${service_name}:${GIT_COMMIT}"
                    service_account_email = sh(script: 'jq -r ".client_email" $GOOGLE_APPLICATION_CREDENTIALS', returnStdout: true).trim()
                    sh(script: 'gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS', returnStdout: true).trim()
                    sh(script: "gcloud config set account ${service_account_email}", returnStdout: true).trim()
                    sh(script: 'sudo cp $application_credentials credentials.json', returnStdout: true).trim()
                    sh(script: 'sudo chown jenkins:jenkins credentials.json', returnStdout: true).trim()
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
                sh 'docker build . -t ${dockerimg_name}'
                script {
                    echo "Getting the port used by the image for deployment"
                    env.port = sh(script: "docker inspect --format='{{range \$p, \$conf := .Config.ExposedPorts}} {{\$p}} {{end}}' ${dockerimg_name} | grep -oE '[0-9]+'", returnStdout: true).trim()
                }
            }
        }
        stage('Upload artifact to repo') {
            steps {
                sh 'echo Uploading Docker image to Google Cloud "Artifact Registry"'
                sh 'gcloud auth configure-docker ${artifact_registry} --quiet'
                sh 'docker push ${dockerimg_name}'
            }
        }
        stage('Deploying application') {
            steps {
                sh 'echo Checking if the application is already running to update the image version, otherwise, deploying to Cloud Run.'
                script {
                    def containerRunning = sh(script: "gcloud run services describe ${service_name} --format='value(status.url)' --region='us-central1' --project='${project_id}'", returnStatus: true) == 0
                    if (containerRunning) {
                        echo "The container is running. Updating the image."
                        sh("gcloud run services update ${service_name} --image='${dockerimg_name}' --region='${region}' --port='${port}' --project='${project_id}' --update-env-vars GOOGLE_APPLICATION_CREDENTIALS='credentials.json'")
                    } else {
                        echo "The container is not running. Deploying the service."
                        sh("gcloud run deploy ${service_name} --image='${dockerimg_name}' --region='${region}' --port=${port} --project='${project_id}' --update-env-vars GOOGLE_APPLICATION_CREDENTIALS='credentials.json'")
                    }
                    sh 'echo Publishing the Cloud Run service for all users'
                    sh 'gcloud run services add-iam-policy-binding ${service_name} --member="allUsers" --role="roles/run.invoker" --region="${region}" --project="${project_id}"'
                    sh 'echo Performing test on the deployed application'
                    def url = sh(script: "gcloud run services describe ${service_name} --format='value(status.url)' --region='${region}' --project='${project_id}'", returnStdout: true).trim()
                    def responseCode = sh(script: "curl -s -o /dev/null -w '%{http_code}' ${url}${test_path_url}", returnStdout: true).trim()
                    if (responseCode == '200') {
                        echo 'The test passed. The response is 200 OK.'
                    } else {
                        error 'The test failed. The response is not 200.'
                    }
                } 
            }
        }
    }
}