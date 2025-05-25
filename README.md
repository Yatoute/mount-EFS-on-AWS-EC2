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
    - Create a `.env` file with:
      ```
      GIT_REPO=<your-repo-url>
      BUCKET=<your-s3-bucket-name>
      ```

3. **Synthesize and deploy infrastructure**:
    ```sh
    poetry run python 
    cdktf synth
    cdktf deploy
    ```

4. **Build and update AMI**:
    - Use the GitHub Actions workflow or run Packer manually:
      ```sh
      packer build packer_ami.json
      ```

5. **Run the web service locally (for testing)**:
    ```sh
    cd webservice
    poetry run uvicorn app:app --reload --port 8080
    ```

## API Endpoints

- `POST /upload`: Upload a file to EFS.
- `POST /process`: Process a file (convert to uppercase).
- `POST /save-file-on-s3`: Save processed file to S3.

## License

MIT License. See [LICENSE](LICENSE) for details.