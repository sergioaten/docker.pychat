provider "google" {
  project     = var.project_id
  credentials = var.credentials
}

locals {
  artifact_registry = "${var.region}-docker.pkg.dev"
  image_name        = "${local.artifact_registry}/${var.project_id}/${var.repo}/test-app:v1"
}

module "project-factory_project_services" {
  source     = "terraform-google-modules/project-factory/google//modules/project_services"
  version    = "14.2.0"
  project_id = var.project_id
  activate_apis = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com"
  ]
  disable_dependent_services  = true
  disable_services_on_destroy = false
}

resource "null_resource" "build_image" {
  triggers = {
    value = local.image_name
  }

  provisioner "local-exec" {
    command = <<-EOF
      #!/bin/bash
      #GOOGLE_APPLICATION_CREDENTIALS=${var.credentials}
      service_account=$(jq -r ".client_email" ${var.credentials})
      gcloud auth activate-service-account --key-file=${var.credentials}
      gcloud config set account $service_account
      docker build -t ${local.image_name} .

      # Extraer el puerto de la imagen Docker y almacenarlo en una variable de entorno
      DOCKER_IMAGE="nombre_imagen_docker"
      container_id=$(docker run -d "${local.image_name}")
      port_number=$(docker inspect --format='{{range $p, $conf := .Config.ExposedPorts}} {{$p}} {{end}}' ${local.image_name} | grep -oE '[0-9]+')
      echo -n $port_number > port

      gcloud auth configure-docker ${local.artifact_registry} --quiet
      docker push ${local.image_name}
    EOF
  }
  depends_on = [module.project-factory_project_services, google_artifact_registry_repository.repo]
}

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.repo
  format        = "DOCKER"

}

resource "google_cloud_run_service" "app" {
  name     = "test-app"
  location = var.region

  metadata {
    annotations = {
      "run.googleapis.com/client-name" = "terraform"
    }
  }

  template {
    spec {
      containers {
        image = local.image_name
        ports {
          container_port = file("${path.module}/port")
        }
        env {
          name  = "GOOGLE_APPLICATION_CREDENTIALS"
          value = "credentials.json"
        }
      }
    }
  }

  depends_on = [null_resource.build_image]
}

data "google_iam_policy" "noauth" {
  binding {
    role    = "roles/run.invoker"
    members = ["allUsers"]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location = google_cloud_run_service.app.location
  project  = google_cloud_run_service.app.project
  service  = google_cloud_run_service.app.name

  policy_data = data.google_iam_policy.noauth.policy_data
}

output "service_url" {
  value = google_cloud_run_service.app.status[0].url
}
