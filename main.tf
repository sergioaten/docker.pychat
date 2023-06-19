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
      REPO_NAME="${var.repo}"

      # Verificar si el repositorio ya existe
      if gcloud artifacts repositories describe "$REPO_NAME" --location="${var.region}" --project="${var.project_id}" >/dev/null 2>&1; then
        echo "El repositorio $REPO_NAME ya existe. No se realizará ninguna acción."
      else
        echo "Creando el repositorio $REPO_NAME..."
        gcloud artifacts repositories create "$REPO_NAME" --location="${var.region}" --repository-format=docker --project="${var.project_id}"
        echo "Repositorio creado exitosamente."
      fi
      docker push ${local.image_name}
    EOF
  }
  depends_on = [module.project-factory_project_services]
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
