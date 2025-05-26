# EFS-on-EC2: AWS EFS & S3 Data Processing Pipeline

This project provisions an AWS infrastructure using CDK for Terraform (CDKTF) to deploy a scalable EC2-based web service with shared storage via EFS and lifecycle-managed S3 storage. It includes a FastAPI web application for file upload, processing, and S3 archiving.

## Features

- **Infrastructure as Code**: Uses CDKTF (Python) to provision AWS resources:
  - EC2 instances (with Auto Scaling and Load Balancer)
  - EFS for shared file storage
  - S3 bucket with lifecycle rules and encryption
- **Web Service**: FastAPI app for:
  - Uploading files to EFS
  - Processing files (e.g., converting text to uppercase)
  - Saving processed files to S3
- **Automation**: Packer builds a custom AMI for the web service, with a GitHub Actions workflow for CI/CD.

## Project Structure

- [`main.py`](main.py): CDKTF stack for EC2, EFS, and networking.
- [`main_serverless.py`](main_serverless.py): CDKTF stack for S3 bucket and lifecycle configuration.
- [`webservice/app.py`](webservice/app.py): FastAPI application code.
- [`packer_ami.json`](packer_ami.json): Packer template for building the EC2 AMI.
- [`.github/workflows/build-ami.yml`](.github/workflows/build-ami.yml): GitHub Actions workflow for AMI build and deployment.
- [`add-secrets.sh`](add-secrets.sh): Script to add environment variables as GitHub secrets.

## Getting Started

### Prerequisites

- Python 3.10–3.11
- [Poetry](https://python-poetry.org/)
- AWS CLI & credentials
- [CDKTF](https://developer.hashicorp.com/terraform/cdktf)
- [Packer](https://www.packer.io/)
- [GitHub CLI](https://cli.github.com/)

### Setup

1. **Install dependencies**:
    ```sh
    poetry install
    ```

2. **Set environment variables**:
    - Use the provided `.env.template` file as a base to create your own `.env` file:
      ```sh
      cp .env.template .env
      # Then edit .env with your values
      ```
    - The `.env` file contains variables like:
      ```
      GIT_REPO=<your-repo-url>
      BUCKET=<your-s3-bucket-name>
      ```

3. **Synthesize and deploy infrastructure**:
    - **Step 1: Deploy S3 resources (serverless)**
      ```sh
      poetry run python main_serverless.py
      cdktf synth
      cdktf deploy
      ```
    - **Step 2: Build the custom AMI for the web service**
      ```sh
      packer build \
        -var "region=<your-region>" \
        -var "source_ami=<base-ami-id>" \
        -var "git_repo=<your-repo-url>" \
        -var "bucket=<your-s3-bucket-name>" \
        packer_ami.json
      ```
      > Retrieve the generated AMI ID for the next step.
    - **Step 3: Deploy the server infrastructure (EC2/EFS/ALB)**
      - Update the `ami_id` variable in `main.py` with the AMI ID from step 2, then deploy:
      ```sh
      poetry run python main.py
      cdktf synth
      cdktf deploy
      ```

4. **Build and update AMI automatically (CI/CD)**:
    - The GitHub Actions workflow (`.github/workflows/build-ami.yml`) automates AMI building, Launch Template update, ASG refresh, and old AMI cleanup.
    - This workflow uses GitHub secrets for sensitive variables.

## Environment Variables & Secrets

- **.env setup:**  
  Use the provided `.env.template` file as a base to create your own `.env` file.
  ```sh
  cp .env.template .env
  # Edit .env with your values
  ```
- **Secrets automation:**  
  You do **not** need to run `add-secrets.sh` manually.  
  This script is automatically executed on every push via a pre-push Git hook, ensuring your `.env` variables are always synced to GitHub Secrets.
- **Sensitive secrets** (AWS credentials, GH_TOKEN, etc.) should be set manually in your repository's GitHub Secrets.

---

## API Endpoints

- `POST /upload`: Upload a file to EFS.
- `POST /process`: Process a file (convert to uppercase).
- `POST /save-file-on-s3`: Save processed file to S3.

## License

MIT License. See [LICENSE](LICENSE) for details.