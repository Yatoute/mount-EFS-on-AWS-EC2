from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import boto3
import uvicorn
import shutil
import os
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()

EFS_UPLOAD = f"/mnt/efs/uploads"
EFS_RESULTS = "/mnt/efs/results"

bucket_s3 = os.getenv("BUCKET")

s3 = boto3.client("s3")

# ----------- ROUTE 1: Upload ------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        upload_path = os.path.join(EFS_UPLOAD, file.filename)

        # Save the uploaded file
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {"message": f"Fichier {file.filename} reçu"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------- ROUTE 2: Traitement ---------
class ArticleModel(BaseModel):
    filename: str

@app.post("/process")
def process_file(req: ArticleModel):
    try:
        filename = req.filename
        path_in = os.path.join(EFS_UPLOAD, filename)
        path_out = os.path.join(EFS_RESULTS, filename)
        with open(path_in, "r") as f_in:
            data = f_in.read().upper()

        with open(path_out, "w") as f_out:
            f_out.write(data)

        return {"message": f"Traitement terminé : {path_out}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------- ROUTE 3: Sauvegarder dans S3 ------

@app.post("/save-file-on-s3")
def save_file_on_s3(req: ArticleModel):
    try:
        filename = req.filename
        path_in = os.path.join(EFS_UPLOAD, filename)
        path_out = os.path.join(EFS_RESULTS, filename)

        s3.upload_file(path_out, bucket_s3, f"processed-articles/{filename}")
        os.remove(path_out)
        os.remove(path_in)
        
        return {"message": f"{filename} sauvegardé dans S3"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
