from minio import Minio

client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

BUCKETS = ["document", "image", "video"]
FOLDERS = ["tin10", "tin11", "tin12"]

def init_minio():
    for b in BUCKETS:
        if not client.bucket_exists(b):
            client.make_bucket(b)

def upload_file(bucket, folder, file):
    client.put_object(
        bucket,
        f"{folder}/{file.filename}",
        file.file,
        length=-1,
        part_size=10*1024*1024
    )

def list_files(bucket, folder):
    objects = client.list_objects(bucket, prefix=f"{folder}/", recursive=True)
    return [obj.object_name for obj in objects if not obj.is_dir]
