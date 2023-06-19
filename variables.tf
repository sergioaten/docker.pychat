variable "project_id" {
  default     = "testing-project-390317"
  description = "Project where terraform resources will be created"
}

variable "region" {
  default     = "us-central1"
  description = "Region where terraform resources will be created"
}

variable "credentials" {
  default     = "/home/sergio/terraform.json"
  description = "Credentials PATH"
}

variable "repo" {
  default     = "repo"
  description = "Artifact Registry Repository name"
}
