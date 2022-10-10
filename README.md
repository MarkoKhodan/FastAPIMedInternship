# FastAPI MedInternship Project

## Installation 

```shell
git clone git@github.com:MarkoKhodan/FastAPIMedInternship.git
cd FastAPIMedInternship
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Windows:
```shell
git clone git@github.com:MarkoKhodan/FastAPIMedInternship.git
cd FastAPIMedInternship
python3 -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
uvicorn main:app --reload
  ```

Docker:
```shell
git clone git@github.com:MarkoKhodan/FastAPIMedInternship.git
cd FastAPIMedInternship
docker build -t myimage . 
docker run -p 8000:8000 -t -i myimage   
```