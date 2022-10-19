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
alembic revision --autogenerate -m 'first' 
alembic upgrade head
uvicorn main:app --reload
  ```

Docker:
```shell
git clone git@github.com:MarkoKhodan/FastAPIMedInternship.git
cd FastAPIMedInternship
docker-compose build
docker-compose up
```